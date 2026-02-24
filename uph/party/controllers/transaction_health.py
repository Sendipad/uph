# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

"""
Transaction Health Monitor

Detects Party Masters with problematic transactional states:
- Draft vouchers (docstatus=0)
- Cancelled but not amended vouchers (docstatus=2, amended_from IS NULL)

Provides paginated queries and drill-down for the Data Quality Dashboard.
"""

import json
import frappe
from frappe import _
from frappe.utils import add_days, cint, now_datetime

from uph.party.controllers.party_issue_utils import create_party_issue_if_missing
from uph.party.controllers.cache_utils import (
    get_doctypes_functional_fields_mapping_as_dict,
)


@frappe.whitelist()
def get_transaction_health(
    limit: int = 20,
    offset: int = 0,
    party_master: str = None,
    reference_doctype: str = None,
):
    """
    Find Party Masters with open Transaction Policy issues.
    Returns paginated list aggregated by (party, reference_doctype), sorted by doctype.
    Severity is determined by per-doctype warn_not_submitted_document setting.
    """
    limit = cint(limit) or 20
    offset = cint(offset) or 0

    # Read per-doctype warn_not_submitted_document from settings child table
    warn_doctypes = set()
    try:
        settings = frappe.get_cached_doc("Party Master Settings")
        for d in settings.document_types or []:
            if getattr(d, "warn_not_submitted_document", 0):
                dt = d.get("document_type")
                parent_dt = d.get("parent_doctype") or dt
                warn_doctypes.add(dt)
                warn_doctypes.add(parent_dt)
    except Exception as e:
        frappe.log_error(
            title="Transaction Health: Failed to load warn_not_submitted_document settings",
            message=str(e),
        )

    # ── SQL aggregation: GROUP BY party, reference_doctype ──
    # Use JSON_EXTRACT to classify each issue by its sub-type directly
    # in SQL, drastically reducing Python-side work.
    party_filter = ""
    params = {}
    if party_master:
        party_filter += " AND pi.party_master = %(party_master)s"
        params["party_master"] = party_master

    if reference_doctype:
        party_filter += " AND pi.reference_doctype = %(reference_doctype)s"
        params["reference_doctype"] = reference_doctype

    agg_rows = frappe.db.sql(
        f"""
        SELECT
            pi.party_master,
            pi.reference_doctype,
            SUM(CASE WHEN JSON_UNQUOTE(JSON_EXTRACT(pi.details_json, '$.issue')) = 'draft_overdue' THEN 1 ELSE 0 END) AS draft_count,
            SUM(CASE WHEN JSON_UNQUOTE(JSON_EXTRACT(pi.details_json, '$.issue')) = 'cancelled_referenced' THEN 1 ELSE 0 END) AS cancelled_unamended_count,
            SUM(CASE WHEN JSON_UNQUOTE(JSON_EXTRACT(pi.details_json, '$.issue')) = 'party_master_mismatch' THEN 1 ELSE 0 END) AS mismatch_count,
            COUNT(*) AS total_issues
        FROM `tabParty Issue` pi
        WHERE pi.issue_type = 'Transaction Policy'
          AND pi.status IN ('Open', 'Under Review')
          AND pi.party_master IS NOT NULL
          AND pi.party_master != ''
          {party_filter}
        GROUP BY pi.party_master, pi.reference_doctype
        """,
        params,
        as_dict=True,
    )

    if not agg_rows:
        return {"parties": [], "total": 0}

    # Bulk-fetch party details
    pm_names = list(set(r.party_master for r in agg_rows))
    pm_details = {}
    for pm in frappe.get_all(
        "Party Master",
        filters={"name": ["in", pm_names]},
        fields=["name", "party_name", "party_type", "party_number"],
    ):
        pm_details[pm.name] = pm

    results = []
    for row in agg_rows:
        detail = pm_details.get(row.party_master, {})
        ref_dt = row.reference_doctype or ""
        total = cint(row.total_issues)

        # Per-doctype severity: if warn_not_submitted_document is checked
        # for this doctype, severity is always High
        if ref_dt in warn_doctypes:
            severity = "High"
        else:
            severity = "High" if total >= 10 else ("Medium" if total >= 3 else "Low")

        results.append(
            {
                "party_master": row.party_master,
                "party_name": detail.get("party_name", row.party_master),
                "party_type": detail.get("party_type", ""),
                "party_number": detail.get("party_number", ""),
                "reference_doctype": ref_dt,
                "draft_count": cint(row.draft_count),
                "cancelled_unamended_count": cint(row.cancelled_unamended_count),
                "total_issues": total,
                "severity": severity,
            }
        )

    # Sort: High severity first, then by reference_doctype, then total_issues desc
    severity_order = {"High": 0, "Medium": 1, "Low": 2}
    results.sort(
        key=lambda x: (
            severity_order.get(x["severity"], 9),
            x["reference_doctype"],
            -x["total_issues"],
        )
    )
    total_count = len(results)
    paginated = results[offset : offset + limit]

    return {"parties": paginated, "total": total_count}


@frappe.whitelist()
def get_party_health_detail(party_master: str, reference_doctype: str = None):
    """
    Drill-down: list individual policy issues for a given Party Master.
    """
    if not frappe.db.exists("Party Master", party_master):
        frappe.throw(_("Party Master {0} does not exist").format(party_master))

    filters = {
        "issue_type": "Transaction Policy",
        "status": ["in", ["Open", "Under Review"]],
        "party_master": party_master,
    }
    if reference_doctype:
        filters["reference_doctype"] = reference_doctype

    issues = frappe.get_all(
        "Party Issue",
        filters=filters,
        fields=["name", "reference_doctype", "reference_name", "details_json"],
        limit_page_length=0,
    )

    vouchers = []
    for issue in issues:
        issue_type = "Policy"
        if issue.details_json:
            try:
                details = json.loads(issue.details_json)
            except Exception:
                details = {}
            code = details.get("issue")
            if code == "draft_overdue":
                issue_type = "Draft Overdue"
            elif code == "cancelled_referenced":
                issue_type = "Cancelled Referenced"
            elif code == "party_master_mismatch":
                issue_type = "Party Master Mismatch"

        vouchers.append(
            {
                "doctype": issue.reference_doctype,
                "name": issue.reference_name,
                "issue_type": issue_type,
                "issue_code": code,
                "issue_name": issue.name,
                "docstatus": (
                    frappe.db.get_value(
                        issue.reference_doctype, issue.reference_name, "docstatus"
                    )
                    if frappe.db.exists(issue.reference_doctype, issue.reference_name)
                    else None
                ),
                "creation": (
                    frappe.db.get_value(
                        issue.reference_doctype, issue.reference_name, "creation"
                    )
                    if frappe.db.exists(issue.reference_doctype, issue.reference_name)
                    else None
                ),
            }
        )

    return {"vouchers": vouchers, "total": len(vouchers)}


@frappe.whitelist()
def resolve_health_issue(issue_name: str, action: str):
    """
    Resolve a specific transaction health issue (e.g. submit draft, cancel).
    Action can be 'submit', 'cancel', or 'dismiss'.
    """
    if not frappe.has_permission("Party Issue", "write"):
        frappe.throw(_("Not permitted to write Party Issue"))

    issue = frappe.get_doc("Party Issue", issue_name)
    if not issue or issue.issue_type != "Transaction Policy":
        frappe.throw(_("Invalid Party Issue"))

    dt = issue.reference_doctype
    dn = issue.reference_name
    now = now_datetime()

    try:
        if action == "submit":
            if not frappe.db.exists(dt, dn):
                frappe.throw(_("{0} {1} no longer exists").format(dt, dn))
            doc = frappe.get_doc(dt, dn)
            if doc.docstatus == 0:
                doc.submit()
            issue.status = "Resolved"
            issue.resolved_on = now
            issue.resolved_by = frappe.session.user
            issue.save(ignore_permissions=True)
            return {
                "success": True,
                "message": _("{0} submitted successfully").format(dn),
            }

        elif action == "cancel":
            if not frappe.db.exists(dt, dn):
                frappe.throw(_("{0} {1} no longer exists").format(dt, dn))
            doc = frappe.get_doc(dt, dn)
            if doc.docstatus == 1:
                doc.cancel()
            issue.status = "Resolved"
            issue.resolved_on = now
            issue.resolved_by = frappe.session.user
            issue.save(ignore_permissions=True)
            return {
                "success": True,
                "message": _("{0} cancelled successfully").format(dn),
            }

        elif action == "dismiss":
            issue.status = "Ignored"
            issue.resolved_on = now
            issue.resolved_by = frappe.session.user

            details = {}
            if issue.details_json:
                try:
                    details = json.loads(issue.details_json)
                except:
                    pass
            details["dismiss_reason"] = "Dismissed from Dashboard"
            issue.details_json = json.dumps(details)
            issue.save(ignore_permissions=True)
            return {"success": True, "message": _("Issue dismissed")}

        else:
            frappe.throw(_("Unknown action {0}").format(action))

    except Exception as e:
        frappe.log_error(title="Failed to resolve health issue", message=str(e))
        return {"success": False, "message": str(e)}


def enqueue_transaction_policy_scan():
    """
    Enqueue transaction policy scan (async).
    """
    frappe.enqueue(
        "uph.party.controllers.transaction_health.run_transaction_policy_scan",
        queue="long",
        timeout=1800,
        job_id="uph_transaction_policy_scan",
        deduplicate=True,
    )


def run_transaction_policy_scan():
    """
    Generate Party Issue entries for transaction policy violations.
    - Draft older than configured X days
    - Cancelled voucher still referenced in GL
    - Status inconsistency detected (party_master mismatch)
    """
    settings = frappe.get_cached_doc("Party Master Settings")
    draft_days = cint(getattr(settings, "transaction_policy_draft_days", 30) or 30)
    cancelled_grace_days = cint(
        getattr(settings, "transaction_policy_cancelled_reference_days", 0) or 0
    )

    tx_doctypes = _get_transaction_doctypes()
    if not tx_doctypes:
        return

    cutoff_draft = add_days(now_datetime(), -draft_days)
    cutoff_cancelled = (
        add_days(now_datetime(), -cancelled_grace_days)
        if cancelled_grace_days
        else None
    )

    mappings = get_doctypes_functional_fields_mapping_as_dict()

    for dt_info in tx_doctypes:
        dt = dt_info.get("document_type")
        parent_dt = dt_info.get("parent_doctype") or dt
        track = dt_info.get("track_transaction_health", "Include")
        configured_severity = dt_info.get("transaction_health_severity", "High")

        if track == "Ignore":
            continue

        if not dt or not frappe.db.exists("DocType", dt):
            continue

        meta = frappe.get_meta(dt)
        if meta.issingle or meta.is_virtual:
            continue
        if not meta.has_field("party_master"):
            continue

        is_child = dt != parent_dt
        # For child table, we use 'parent' field as the reference name
        ref_field = "parent" if is_child else "name"

        # Draft older than threshold
        start = 0
        page_len = 500
        while True:
            drafts = frappe.get_all(
                dt,
                filters={
                    "docstatus": 0,
                    "party_master": ["is", "set"],
                    "creation": ["<=", cutoff_draft],
                },
                fields=["name", "party_master", "creation", ref_field],
                limit_start=start,
                limit_page_length=page_len,
                order_by="creation asc",
            )
            if not drafts:
                break
            for d in drafts:
                age_days = max(1, (now_datetime() - d.creation).days)
                create_party_issue_if_missing(
                    party_master=d.party_master,
                    issue_type="Transaction Policy",
                    severity=configured_severity,
                    status="Open",
                    source_engine="transaction_health",
                    reference_doctype=parent_dt,
                    reference_name=d.get(ref_field),
                    details={"issue": "draft_overdue", "age_days": age_days},
                )
            start += page_len

        # Cancelled voucher not amended
        # For child records, we must check 'amended_from' on the PARENT
        has_amended_from = False
        if is_child:
            has_amended_from = frappe.get_meta(parent_dt).has_field("amended_from")
        else:
            has_amended_from = meta.has_field("amended_from")

        if has_amended_from:
            if is_child:
                # Subquery/Join logic for child tables
                # We want cancelled vouchers (docstatus=2) where parent's amended_from is null
                # We use frappe.get_all but we need to fetch 'parent' to check against amended parents
                filters = [
                    ["docstatus", "=", 2],
                    ["party_master", "is", "set"],
                ]
                if cutoff_cancelled:
                    filters.append(["modified", "<=", cutoff_cancelled])

                cancelled = frappe.get_all(
                    dt,
                    filters=filters,
                    fields=["party_master", "parent", "modified"],
                )

                if cancelled:
                    parent_names = list(set(r.parent for r in cancelled))
                    amended_parents = frappe.get_all(
                        parent_dt,
                        filters={
                            "name": ["in", parent_names],
                            "amended_from": ["is", "set"],
                        },
                        pluck="name",
                    )

                    for r in cancelled:
                        if r.parent in amended_parents:
                            continue

                        create_party_issue_if_missing(
                            party_master=r.party_master,
                            issue_type="Transaction Policy",
                            severity=configured_severity,
                            status="Open",
                            source_engine="transaction_health",
                            reference_doctype=parent_dt,
                            reference_name=r.parent,
                            details={"issue": "cancelled_referenced"},
                        )
            else:
                filters = {
                    "docstatus": 2,
                    "party_master": ["is", "set"],
                    "amended_from": ["in", [None, ""]],
                }
                if cutoff_cancelled:
                    filters["modified"] = ["<=", cutoff_cancelled]

                cancelled_start = 0
                while True:
                    cancelled = frappe.get_all(
                        dt,
                        filters=filters,
                        fields=["name", "party_master", "modified"],
                        limit_start=cancelled_start,
                        limit_page_length=page_len,
                        order_by="modified asc",
                    )
                    if not cancelled:
                        break

                    for row in cancelled:
                        create_party_issue_if_missing(
                            party_master=row.party_master,
                            issue_type="Transaction Policy",
                            severity=configured_severity,
                            status="Open",
                            source_engine="transaction_health",
                            reference_doctype=parent_dt,
                            reference_name=row.get(ref_field),
                            details={"issue": "cancelled_referenced"},
                        )
                    cancelled_start += page_len

        # Status inconsistency: party_master mismatch vs party record
        map_conf = mappings.get(dt)
        if map_conf and not map_conf.get("is_dynamic_party_type"):
            party_fieldname = map_conf.get("party_fieldname")
            party_type = map_conf.get("party_type")
            if (
                party_fieldname
                and party_type
                and frappe.db.exists("DocType", party_type)
            ):
                parent_select = ", dt.parent" if is_child else ""
                rows = frappe.db.sql(
                    f"""
                    SELECT dt.name {parent_select}, dt.party_master, p.party_master AS expected_pm
                    FROM `tab{dt}` dt
                    INNER JOIN `tab{party_type}` p ON p.name = dt.`{party_fieldname}`
                    WHERE dt.docstatus = 1
                      AND dt.party_master IS NOT NULL
                      AND dt.party_master != ''
                      AND p.party_master IS NOT NULL
                      AND p.party_master != ''
                      AND dt.party_master != p.party_master
                """,
                    as_dict=True,
                )
                for row in rows or []:
                    create_party_issue_if_missing(
                        party_master=row.party_master,
                        issue_type="Transaction Policy",
                        severity=configured_severity,
                        status="Open",
                        source_engine="transaction_health",
                        reference_doctype=parent_dt,
                        reference_name=row.get(ref_field),
                        details={
                            "issue": "party_master_mismatch",
                            "expected_pm": row.expected_pm,
                        },
                    )

    # Sync and auto-resolve issues that are no longer valid
    sync_transaction_health_issues()


def sync_transaction_health_issues():
    """
    Auto-resolve issues that have been fixed outside the dashboard.
    Also syncs severity with current settings.
    """
    open_issues = frappe.get_all(
        "Party Issue",
        filters={
            "issue_type": "Transaction Policy",
            "status": ["in", ["Open", "Under Review"]],
        },
        fields=[
            "name",
            "reference_doctype",
            "reference_name",
            "details_json",
            "severity",
        ],
    )

    if not open_issues:
        return

    # Cache settings to avoid redundant DB calls
    severity_map = {
        d["document_type"]: d["transaction_health_severity"]
        for d in _get_transaction_doctypes()
    }

    now = now_datetime()
    resolved_count = 0
    updated_count = 0

    for issue in open_issues:
        dt = issue.reference_doctype
        dn = issue.reference_name

        # 1. Check if the document still exists
        if not frappe.db.exists(dt, dn):
            frappe.db.set_value(
                "Party Issue",
                issue.name,
                {
                    "status": "Resolved",
                    "resolved_on": now,
                    "resolved_by": "Administrator",
                    "dismiss_reason": "Orphaned: Document no longer exists",
                },
            )
            resolved_count += 1
            continue

        # 2. Check if the issue is still valid
        details = {}
        if issue.details_json:
            try:
                details = json.loads(issue.details_json)
            except:
                pass

        code = details.get("issue")
        is_resolved = False

        doc = frappe.get_doc(dt, dn)

        if code == "draft_overdue":
            if doc.docstatus != 0:
                is_resolved = True
        elif code == "cancelled_referenced":
            has_amended_from = False
            if hasattr(doc, "amended_from") and doc.amended_from:
                has_amended_from = True

            if doc.docstatus != 2 or has_amended_from:
                is_resolved = True
        elif code == "party_master_mismatch":
            # For mismatch, we need to re-verify the expected party_master
            # Note: This logic depends on the specific mapping for the doctype
            mappings = get_doctypes_functional_fields_mapping_as_dict()
            map_conf = mappings.get(dt)
            if map_conf and not map_conf.get("is_dynamic_party_type"):
                party_fieldname = map_conf.get("party_fieldname")
                party_type = map_conf.get("party_type")
                if party_fieldname and party_type:
                    current_pm = doc.get("party_master")
                    party_record_pm = frappe.db.get_value(
                        party_type, doc.get(party_fieldname), "party_master"
                    )
                    if current_pm == party_record_pm:
                        is_resolved = True

        if is_resolved:
            frappe.db.set_value(
                "Party Issue",
                issue.name,
                {
                    "status": "Resolved",
                    "resolved_on": now,
                    "resolved_by": "Administrator",
                },
            )
            resolved_count += 1
        else:
            # 3. If not resolved, sync severity
            current_severity = severity_map.get(dt, "High")
            if issue.severity != current_severity:
                frappe.db.set_value(
                    "Party Issue", issue.name, "severity", current_severity
                )
                updated_count += 1

    if resolved_count or updated_count:
        frappe.logger("uph").info(
            f"Health Sync: Resolved {resolved_count} issues, updated severity for {updated_count} issues"
        )


def get_health_counts():
    """Get aggregate health counts for dashboard stats. Uses Redis cache."""
    cache_key = "uph:health_counts"
    if cached := frappe.cache.get_value(cache_key):
        return cached

    tx_doctypes = _get_transaction_doctypes()
    draft_total = 0
    cancelled_total = 0

    for dt_info in tx_doctypes:
        dt = dt_info.get("document_type")
        parent_dt = dt_info.get("parent_doctype") or dt

        if not dt or not frappe.db.exists("DocType", dt):
            continue

        meta = frappe.get_meta(dt)
        if not meta.has_field("party_master"):
            continue

        is_child = dt != parent_dt

        # Draft count
        d_cnt = frappe.db.count(
            dt,
            {
                "docstatus": 0,
                "party_master": ["is", "set"],
            },
        )
        draft_total += d_cnt

        # Cancelled-unamended count
        has_amended_from = False
        if is_child:
            has_amended_from = frappe.get_meta(parent_dt).has_field("amended_from")
        else:
            has_amended_from = meta.has_field("amended_from")

        if has_amended_from:
            table = frappe.qb.DocType(dt)
            if is_child:
                parent_table = frappe.qb.DocType(parent_dt)
                result = (
                    frappe.qb.from_(table)
                    .join(parent_table)
                    .on(table.parent == parent_table.name)
                    .select(frappe.query_builder.functions.Count(table.name).as_("cnt"))
                    .where(
                        (table.docstatus == 2)
                        & (table.party_master.isnotnull())
                        & (table.party_master != "")
                        & (
                            (parent_table.amended_from.isnull())
                            | (parent_table.amended_from == "")
                        )
                    )
                    .run(as_dict=True)
                )
            else:
                result = (
                    frappe.qb.from_(table)
                    .select(frappe.query_builder.functions.Count("*").as_("cnt"))
                    .where(
                        (table.docstatus == 2)
                        & (table.party_master.isnotnull())
                        & (table.party_master != "")
                        & ((table.amended_from.isnull()) | (table.amended_from == ""))
                    )
                    .run(as_dict=True)
                )
            c_cnt = result[0]["cnt"] if result else 0
            cancelled_total += c_cnt

    counts = {
        "draft_voucher_count": draft_total,
        "cancelled_unamended_count": cancelled_total,
    }

    frappe.cache.set_value(cache_key, counts, expires_in_sec=300)
    return counts


def rebuild_health_cache():
    """Scheduled job: refresh the health counts cache."""
    frappe.cache.delete_value("uph:health_counts")
    get_health_counts()
    frappe.logger("uph").info("Transaction health cache rebuilt")


def _get_transaction_doctypes():
    """
    Get the list of transaction DocTypes configured in Party Master Settings.
    Returns list of dicts with 'document_type', 'parent_doctype', 'track_transaction_health',
    and 'transaction_health_severity' keys.
    """
    try:
        settings = frappe.get_cached_doc("Party Master Settings")
        tx_doctypes = []
        for d in settings.document_types or []:
            dt = d.get("document_type")
            parent_dt = d.get("parent_doctype") or dt
            track = d.get("track_transaction_health", "Include")
            severity = d.get("transaction_health_severity", "High")

            if dt and not frappe.get_meta(dt).issingle:
                tx_doctypes.append(
                    {
                        "document_type": dt,
                        "parent_doctype": parent_dt,
                        "track_transaction_health": track,
                        "transaction_health_severity": severity,
                    }
                )

        # Fallback to sensible defaults when nothing is configured
        if not tx_doctypes:
            return _get_fallback_transaction_doctypes()

        # Deduplicate by document_type
        seen = set()
        unique = []
        for d in tx_doctypes:
            if d["document_type"] not in seen:
                seen.add(d["document_type"])
                unique.append(d)
        return unique
    except Exception:
        # Fallback
        return _get_fallback_transaction_doctypes()


def _get_fallback_transaction_doctypes():
    defaults = [
        {"document_type": "Sales Invoice", "parent_doctype": "Sales Invoice"},
        {"document_type": "Purchase Invoice", "parent_doctype": "Purchase Invoice"},
        {"document_type": "Payment Entry", "parent_doctype": "Payment Entry"},
        {"document_type": "Journal Entry Account", "parent_doctype": "Journal Entry"},
    ]
    for d in defaults:
        d["track_transaction_health"] = "Include"
        d["transaction_health_severity"] = "High"
    return defaults
