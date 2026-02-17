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
from uph.party.controllers.cache_utils import get_doctypes_functional_fields_mapping_as_dict


@frappe.whitelist()
def get_transaction_health(limit: int = 20, offset: int = 0):
    """
    Find Party Masters with open Transaction Policy issues.
    Returns paginated list of parties with problem counts.
    """
    limit = cint(limit) or 20
    offset = cint(offset) or 0

    issues = frappe.get_all(
        "Party Issue",
        filters={"issue_type": "Transaction Policy", "status": ["in", ["Open", "Under Review"]]},
        fields=["party", "details_json"],
        limit_page_length=0,
    )

    if not issues:
        return {"parties": [], "total": 0}

    party_problems = {}
    for issue in issues:
        pm = issue.party
        if not pm:
            continue
        party_problems.setdefault(
            pm,
            {"draft_count": 0, "cancelled_unamended_count": 0, "mismatch_count": 0},
        )
        if issue.details_json:
            try:
                details = json.loads(issue.details_json)
            except Exception:
                details = {}
        else:
            details = {}
        code = details.get("issue")
        if code == "draft_overdue":
            party_problems[pm]["draft_count"] += 1
        elif code == "cancelled_referenced":
            party_problems[pm]["cancelled_unamended_count"] += 1
        elif code == "party_master_mismatch":
            party_problems[pm]["mismatch_count"] += 1

    pm_names = list(party_problems.keys())
    pm_details = {}
    for pm in frappe.get_all(
        "Party Master",
        filters={"name": ["in", pm_names]},
        fields=["name", "party_name", "party_type", "party_number"],
    ):
        pm_details[pm.name] = pm

    results = []
    for pm_name, counts in party_problems.items():
        detail = pm_details.get(pm_name, {})
        total_issues = (
            counts["draft_count"]
            + counts["cancelled_unamended_count"]
            + counts["mismatch_count"]
        )
        results.append(
            {
                "party_master": pm_name,
                "party_name": detail.get("party_name", pm_name),
                "party_type": detail.get("party_type", ""),
                "party_number": detail.get("party_number", ""),
                "draft_count": counts["draft_count"],
                "cancelled_unamended_count": counts["cancelled_unamended_count"],
                "total_issues": total_issues,
                "severity": (
                    "High"
                    if total_issues >= 10
                    else ("Medium" if total_issues >= 3 else "Low")
                ),
            }
        )

    results.sort(key=lambda x: x["total_issues"], reverse=True)
    total = len(results)
    paginated = results[offset : offset + limit]

    return {"parties": paginated, "total": total}


@frappe.whitelist()
def get_party_health_detail(party_master: str):
    """
    Drill-down: list individual policy issues for a given Party Master.
    """
    if not frappe.db.exists("Party Master", party_master):
        frappe.throw(_("Party Master {0} does not exist").format(party_master))

    issues = frappe.get_all(
        "Party Issue",
        filters={
            "issue_type": "Transaction Policy",
            "status": ["in", ["Open", "Under Review"]],
            "party": party_master,
        },
        fields=["reference_doctype", "reference_name", "details_json"],
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
            }
        )

    return {"vouchers": vouchers, "total": len(vouchers)}


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
        dt = dt_info.get("doctype")
        if not dt or not frappe.db.exists("DocType", dt):
            continue

        meta = frappe.get_meta(dt)
        if meta.issingle or meta.is_virtual:
            continue
        if not meta.has_field("party_master") or not meta.has_field("docstatus"):
            continue

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
                fields=["name", "party_master", "creation"],
                limit_start=start,
                limit_page_length=page_len,
                order_by="creation asc",
            )
            if not drafts:
                break
            for d in drafts:
                age_days = max(1, (now_datetime() - d.creation).days)
                severity = "Medium" if age_days <= draft_days * 2 else "High"
                create_party_issue_if_missing(
                    party=d.party_master,
                    issue_type="Transaction Policy",
                    severity=severity,
                    status="Open",
                    source_engine="transaction_health",
                    reference_doctype=dt,
                    reference_name=d.name,
                    details={"issue": "draft_overdue", "age_days": age_days},
                )
            start += page_len

        # Cancelled voucher still referenced in GL Entry
        cancelled_filters = "AND dt.modified <= %(cutoff)s" if cutoff_cancelled else ""
        cancelled_params = {
            "doctype": dt,
            "cutoff": cutoff_cancelled,
        }
        cancelled = frappe.db.sql(
            f"""
            SELECT dt.name, dt.party_master
            FROM `tab{dt}` dt
            INNER JOIN `tabGL Entry` gle
                ON gle.voucher_type = %(doctype)s
               AND gle.voucher_no = dt.name
               AND gle.is_cancelled = 0
            WHERE dt.docstatus = 2
              AND dt.party_master IS NOT NULL
              AND dt.party_master != ''
              {cancelled_filters}
        """,
            cancelled_params,
            as_dict=True,
        )
        for row in cancelled or []:
            create_party_issue_if_missing(
                party=row.party_master,
                issue_type="Transaction Policy",
                severity="High",
                status="Open",
                source_engine="transaction_health",
                reference_doctype=dt,
                reference_name=row.name,
                details={"issue": "cancelled_referenced"},
            )

        # Status inconsistency: party_master mismatch vs party record
        map_conf = mappings.get(dt)
        if map_conf and not map_conf.get("is_dynamic_party_type"):
            party_fieldname = map_conf.get("party_fieldname")
            party_type = map_conf.get("party_type")
            if party_fieldname and party_type and frappe.db.exists("DocType", party_type):
                rows = frappe.db.sql(
                    f"""
                    SELECT dt.name, dt.party_master, p.party_master AS expected_pm
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
                        party=row.party_master,
                        issue_type="Transaction Policy",
                        severity="High",
                        status="Open",
                        source_engine="transaction_health",
                        reference_doctype=dt,
                        reference_name=row.name,
                        details={
                            "issue": "party_master_mismatch",
                            "expected_pm": row.expected_pm,
                        },
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
        dt = dt_info.get("doctype")
        if not dt or not frappe.db.exists("DocType", dt):
            continue

        meta = frappe.get_meta(dt)
        if not meta.has_field("party_master") or not meta.has_field("docstatus"):
            continue

        # Draft count
        draft_total += frappe.db.count(
            dt,
            {
                "docstatus": 0,
                "party_master": ["is", "set"],
            },
        )

        # Cancelled-unamended count
        if meta.has_field("amended_from"):
            table = frappe.qb.DocType(dt)
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
            cancelled_total += result[0]["cnt"] if result else 0

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
    Returns list of dicts with 'doctype' key.
    """
    try:
        settings = frappe.get_cached_doc("Party Master Settings")
        tx_doctypes = []
        for d in settings.document_types or []:
            dt = d.get("parent_doctype") or d.get("document_type")
            if dt and not frappe.get_meta(dt).issingle:
                tx_doctypes.append({"doctype": dt})
        # Fallback to sensible defaults when nothing is configured
        if not tx_doctypes:
            return [
                {"doctype": "Sales Invoice"},
                {"doctype": "Purchase Invoice"},
                {"doctype": "Payment Entry"},
                {"doctype": "Journal Entry"},
            ]
        # Deduplicate
        seen = set()
        unique = []
        for dt in tx_doctypes:
            if dt["doctype"] not in seen:
                seen.add(dt["doctype"])
                unique.append(dt)
        return unique
    except Exception:
        # Fallback
        return [
            {"doctype": "Sales Invoice"},
            {"doctype": "Purchase Invoice"},
            {"doctype": "Payment Entry"},
            {"doctype": "Journal Entry"},
        ]
