# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint
import json


@frappe.whitelist()
def get_duplicate_issues(
    limit: int = 50, offset: int = 0, min_score: float = 0, party_master: str = None
):
    """
    Get duplicate Party Issues from the governance registry.
    """
    if not frappe.has_permission("Party Master", "read"):
        frappe.throw(_("Not permitted to read Party Master"), frappe.PermissionError)

    limit = cint(limit) or 50
    offset = cint(offset) or 0

    filters = {"issue_type": "Duplicate", "status": ["in", ["Open", "Under Review"]]}
    if float(min_score) > 0:
        filters["score"] = [">=", float(min_score)]
    if party_master:
        filters["party_master"] = party_master

    duplicates = frappe.get_all(
        "Party Issue",
        fields=[
            "name",
            "party_master",
            "reference_doctype",
            "reference_name",
            "score",
            "status",
        ],
        filters=filters,
        order_by="score desc",
        limit_start=offset,
        limit_page_length=limit,
    )

    # Bulk-fetch party names to avoid N+1 queries
    if duplicates:
        all_party_ids = set()
        for d in duplicates:
            all_party_ids.add(d.party_master)
            if d.reference_doctype == "Party Master" and d.reference_name:
                all_party_ids.add(d.reference_name)

        party_names = {
            p.name: p.party_name
            for p in frappe.get_all(
                "Party Master",
                filters={"name": ["in", list(all_party_ids)]},
                fields=["name", "party_name"],
            )
        }

        for d in duplicates:
            d.party_1 = d.party_master
            d.party_2 = (
                d.reference_name if d.reference_doctype == "Party Master" else None
            )
            d.party_1_name = party_names.get(d.party_1, d.party_1)
            d.party_2_name = party_names.get(d.party_2, d.party_2) if d.party_2 else ""
            d.normalized_name_1 = d.party_1_name
            d.normalized_name_2 = d.party_2_name
            d.similarity_score = d.score

    total = frappe.db.count("Party Issue", filters)

    return {"duplicates": duplicates, "total": total, "limit": limit, "offset": offset}


@frappe.whitelist()
def get_dashboard_stats(party_master: str = None):
    """
    Get summary statistics sourced entirely from the Party Issue doctype.
    Uses a single aggregation query for all issue counts.
    Optionally filters by party_master.
    """
    if not frappe.has_permission("Party Issue", "read"):
        frappe.throw(_("Not permitted to read Party Issue"), frappe.PermissionError)

    party_filter = ""
    params = {}
    if party_master:
        party_filter = (
            "WHERE (party_master = %(party_master)s"
            " OR (reference_doctype = 'Party Master' AND reference_name = %(party_master)s))"
        )
        params["party_master"] = party_master

    # Single aggregation query on Party Issue
    issue_counts = frappe.db.sql(
        f"""
        SELECT issue_type, status, COUNT(*) as cnt
        FROM `tabParty Issue`
        {party_filter}
        GROUP BY issue_type, status
        """,
        params,
        as_dict=True,
    )

    # Build a lookup: (issue_type, status) -> count
    count_map = {}
    for row in issue_counts:
        count_map[(row.issue_type, row.status)] = row.cnt

    def _open_count(issue_type):
        return count_map.get((issue_type, "Open"), 0) + count_map.get(
            (issue_type, "Under Review"), 0
        )

    # All ignored/resolved counts (across all issue types)
    total_ignored = sum(v for (k, s), v in count_map.items() if s == "Ignored")

    stats = {
        "total_parties": frappe.db.count("Party Master", {"is_group": 0}),
        "total_groups": frappe.db.count("Party Master", {"is_group": 1}),
        # Duplicates
        "duplicate_issues": _open_count("Duplicate"),
        "total_dismissed": total_ignored,
        "total_merged": count_map.get(("Duplicate", "Resolved"), 0),
        # Unlinked roles
        "unlinked_count": _open_count("Unlinked"),
        # Transaction policy / health
        "draft_voucher_count": _open_count("Transaction Policy"),
        "cancelled_unamended_count": count_map.get(("Health", "Open"), 0)
        + count_map.get(("Health", "Under Review"), 0),
        "unlinked_transaction_count": _open_count("Unlinked"),
        "incomplete_parties": count_map.get(("Health", "Open"), 0),
        "last_updated": frappe.utils.now_datetime(),
    }
    return stats


@frappe.whitelist()
def get_unlinked_voucher_issues(
    limit: int = 20,
    offset: int = 0,
    party_master: str = None,
    reference_doctype: str = None,
):
    """
    Get unlinked vouchers by querying transaction tables directly.
    Finds vouchers where party_master is NULL or empty.
    Optionally filters by a specific party_master (for linked party checks).
    Optionally filters by specific reference_doctype.
    """
    if not frappe.has_permission("Party Issue", "read"):
        frappe.throw(_("Not permitted to read Party Issue"), frappe.PermissionError)

    limit = cint(limit) or 20
    offset = cint(offset) or 0

    from uph.party.controllers.transaction_health import _get_transaction_doctypes

    tx_doctypes = _get_transaction_doctypes()
    if not tx_doctypes:
        return {"unlinked": [], "total": 0}

    total = 0
    selects = []

    for dt_info in tx_doctypes:
        dt = dt_info.get("document_type")
        parent_dt = dt_info.get("parent_doctype") or dt
        if not dt or not frappe.db.exists("DocType", dt):
            continue

        # Apply doctype filter
        if (
            reference_doctype
            and dt != reference_doctype
            and parent_dt != reference_doctype
        ):
            continue

        meta = frappe.get_meta(dt)
        if not meta.has_field("party_master"):
            continue

        # Build the WHERE clause and count filters
        where_clause = "(party_master IS NULL OR party_master = '')"
        count_filters = {"party_master": ["in", [None, ""]]}
        if party_master:
            where_clause = "party_master = %(party_master)s"
            count_filters = {"party_master": party_master}

        # Count
        total += frappe.db.count(dt, count_filters)

        is_child = meta.istable

        if is_child:
            selects.append(
                f"""
                SELECT
                    `parenttype` AS role_doctype,
                    `parent` AS role_name,
                    CONCAT(`parenttype`, ': ', `parent`) AS display_name,
                    '' AS owner,
                    `creation` AS creation
                FROM `tab{dt}`
                WHERE {where_clause}
            """
            )
        else:
            owner_expr = "''"
            if meta.has_field("owner"):
                owner_expr = "COALESCE(`owner`, '')"

            selects.append(
                f"""
                SELECT
                    {frappe.db.escape(dt)} AS role_doctype,
                    `name` AS role_name,
                    CONCAT({frappe.db.escape(dt)}, ': ', `name`) AS display_name,
                    {owner_expr} AS owner,
                    `creation` AS creation
                FROM `tab{dt}`
                WHERE {where_clause}
            """
            )

    if not selects:
        return {"unlinked": [], "total": 0}

    union_query = " UNION ALL ".join(selects)
    final_query = f"""
        SELECT * FROM ({union_query}) AS combined
        ORDER BY creation DESC
        LIMIT %(limit)s OFFSET %(offset)s
    """

    rows = frappe.db.sql(
        final_query,
        {"limit": limit, "offset": offset, "party_master": party_master},
        as_dict=True,
    )

    if rows:
        # Bulk lookup Party Issues for these vouchers
        vouchers = [(r.role_doctype, r.role_name) for r in rows]
        issues = frappe.get_all(
            "Party Issue",
            filters={
                "issue_type": "Unlinked",
                "status": ["in", ["Open", "Under Review"]],
                "reference_doctype": ["in", [v[0] for v in vouchers]],
                "reference_name": ["in", [v[1] for v in vouchers]],
            },
            fields=["name", "reference_doctype", "reference_name"],
        )
        issue_map = {(i.reference_doctype, i.reference_name): i.name for i in issues}
        for r in rows:
            r.issue_name = issue_map.get((r.role_doctype, r.role_name))

    return {"unlinked": rows, "total": total}


@frappe.whitelist()
def trigger_refresh():
    """
    Manually trigger background refresh of stats.
    """
    frappe.enqueue("uph.tasks.refresh_dashboard_stats", queue="short")
    return {"message": _("Refresh started in background")}


@frappe.whitelist()
def dismiss_duplicate(party_1: str, party_2: str, reason: str = None):
    """
    Dismiss a duplicate issue by setting status to Ignored.
    """
    if not frappe.has_permission("Party Issue", "write"):
        frappe.throw(_("Insufficient permissions to dismiss duplicates"))

    from uph.party.controllers.party_issue_utils import normalize_party_pair

    party_1, party_2 = normalize_party_pair(party_1, party_2)
    issue_name = frappe.db.get_value(
        "Party Issue",
        {
            "party_master": party_1,
            "reference_doctype": "Party Master",
            "reference_name": party_2,
            "issue_type": "Duplicate",
            "status": ["in", ["Open", "Under Review"]],
        },
        "name",
    )
    if not issue_name:
        return {"success": True, "message": _("Duplicate issue not found")}

    updates = {
        "status": "Ignored",
        "resolved_on": frappe.utils.now_datetime(),
        "resolved_by": frappe.session.user,
    }

    if reason:
        updates["dismiss_reason"] = reason

    if reason:
        details = {}
        details_json = frappe.db.get_value("Party Issue", issue_name, "details_json")
        if details_json:
            try:
                details = json.loads(details_json) or {}
            except Exception:
                details = {}
        details["dismiss_reason"] = reason
        details["dismissed_by"] = frappe.session.user
        details["dismissed_on"] = str(frappe.utils.now_datetime())
        updates["details_json"] = json.dumps(details)

    frappe.db.set_value("Party Issue", issue_name, updates)

    trigger_refresh()
    return {"success": True, "message": _("Duplicate issue has been ignored")}


@frappe.whitelist()
def merge_parties(
    primary_party: str,
    secondary_party: str,
    fields_to_keep: dict = None,
    ignore_validation: bool = False,
):
    """
    Merge secondary Party Master into primary Party Master.
    Delegates to PartyMergeService.
    """
    from uph.party.controllers.party_merge_service import PartyMergeService

    if isinstance(fields_to_keep, str):
        fields_to_keep = json.loads(fields_to_keep) if fields_to_keep else {}

    service = PartyMergeService()
    result = service.merge(
        primary_party,
        secondary_party,
        fields_to_keep,
        ignore_validation=ignore_validation,
    )

    if result.get("success"):
        # Update Party Issue status
        from uph.party.controllers.party_issue_utils import normalize_party_pair

        party_1, party_2 = normalize_party_pair(primary_party, secondary_party)
        issue_name = frappe.db.get_value(
            "Party Issue",
            {
                "party_master": party_1,
                "reference_doctype": "Party Master",
                "reference_name": party_2,
                "issue_type": "Duplicate",
                "status": ["in", ["Open", "Under Review"]],
            },
            "name",
        )
        if issue_name:
            frappe.db.set_value(
                "Party Issue",
                issue_name,
                {
                    "status": "Resolved",
                    "resolved_on": frappe.utils.now_datetime(),
                    "resolved_by": frappe.session.user,
                },
            )

        # Trigger stats refresh
        trigger_refresh()

    return result
