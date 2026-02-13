# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

"""
Transaction Health Monitor

Detects Party Masters with problematic transactional states:
- Draft vouchers (docstatus=0)
- Cancelled but not amended vouchers (docstatus=2, amended_from IS NULL)

Provides paginated queries and drill-down for the Data Quality Dashboard.
"""

import frappe
from frappe import _
from frappe.utils import cint
from pypika.functions import Coalesce


@frappe.whitelist()
def get_transaction_health(limit: int = 20, offset: int = 0):
    """
    Find Party Masters with draft or cancelled-unamended vouchers.

    Returns paginated list of parties with problem counts.
    """
    limit = cint(limit) or 20
    offset = cint(offset) or 0

    tx_doctypes = _get_transaction_doctypes()
    if not tx_doctypes:
        return {"parties": [], "total": 0}

    # Aggregate problems per party_master
    party_problems = {}

    for dt_info in tx_doctypes:
        dt = dt_info.get("doctype")
        if not dt or not frappe.db.exists("DocType", dt):
            continue

        meta = frappe.get_meta(dt)
        if not meta.has_field("party_master") or not meta.has_field("docstatus"):
            continue

        table = frappe.qb.DocType(dt)

        # Draft vouchers (docstatus=0)
        draft_q = (
            frappe.qb.from_(table)
            .select(
                table.party_master, frappe.query_builder.functions.Count("*").as_("cnt")
            )
            .where(
                (table.docstatus == 0)
                & (table.party_master.isnotnull())
                & (table.party_master != "")
            )
            .groupby(table.party_master)
        )

        for row in draft_q.run(as_dict=True):
            pm = row["party_master"]
            if pm not in party_problems:
                party_problems[pm] = {"draft_count": 0, "cancelled_unamended_count": 0}
            party_problems[pm]["draft_count"] += row["cnt"]

        # Cancelled-unamended (docstatus=2, amended_from IS NULL or empty)
        if meta.has_field("amended_from"):
            cancel_q = (
                frappe.qb.from_(table)
                .select(
                    table.party_master,
                    frappe.query_builder.functions.Count("*").as_("cnt"),
                )
                .where(
                    (table.docstatus == 2)
                    & (table.party_master.isnotnull())
                    & (table.party_master != "")
                    & ((table.amended_from.isnull()) | (table.amended_from == ""))
                )
                .groupby(table.party_master)
            )

            for row in cancel_q.run(as_dict=True):
                pm = row["party_master"]
                if pm not in party_problems:
                    party_problems[pm] = {
                        "draft_count": 0,
                        "cancelled_unamended_count": 0,
                    }
                party_problems[pm]["cancelled_unamended_count"] += row["cnt"]

    if not party_problems:
        return {"parties": [], "total": 0}

    # Enrich with party details
    pm_names = list(party_problems.keys())
    pm_details = {}
    for pm in frappe.get_all(
        "Party Master",
        filters={"name": ["in", pm_names]},
        fields=["name", "party_name", "party_type", "party_number"],
    ):
        pm_details[pm.name] = pm

    # Build result
    results = []
    for pm_name, counts in party_problems.items():
        detail = pm_details.get(pm_name, {})
        total_issues = counts["draft_count"] + counts["cancelled_unamended_count"]
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

    # Sort by severity (total_issues desc)
    results.sort(key=lambda x: x["total_issues"], reverse=True)

    total = len(results)
    paginated = results[offset : offset + limit]

    return {"parties": paginated, "total": total}


@frappe.whitelist()
def get_party_health_detail(party_master: str):
    """
    Drill-down: list individual problematic vouchers for a given Party Master.
    """
    if not frappe.db.exists("Party Master", party_master):
        frappe.throw(_("Party Master {0} does not exist").format(party_master))

    tx_doctypes = _get_transaction_doctypes()
    vouchers = []

    for dt_info in tx_doctypes:
        dt = dt_info.get("doctype")
        if not dt or not frappe.db.exists("DocType", dt):
            continue

        meta = frappe.get_meta(dt)
        if not meta.has_field("party_master") or not meta.has_field("docstatus"):
            continue

        # Draft vouchers
        drafts = frappe.get_all(
            dt,
            filters={
                "party_master": party_master,
                "docstatus": 0,
            },
            fields=["name", "owner", "creation"],
            limit_page_length=50,
        )

        for d in drafts:
            vouchers.append(
                {
                    "doctype": dt,
                    "name": d.name,
                    "issue_type": "Draft",
                    "owner": d.owner,
                    "creation": str(d.creation),
                }
            )

        # Cancelled-unamended
        if meta.has_field("amended_from"):
            cancelled = frappe.get_all(
                dt,
                filters={
                    "party_master": party_master,
                    "docstatus": 2,
                    "amended_from": ["in", [None, ""]],
                },
                fields=["name", "owner", "creation"],
                limit_page_length=50,
            )

            for c in cancelled:
                vouchers.append(
                    {
                        "doctype": dt,
                        "name": c.name,
                        "issue_type": "Cancelled (Unamended)",
                        "owner": c.owner,
                        "creation": str(c.creation),
                    }
                )

    return {"vouchers": vouchers, "total": len(vouchers)}


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
            parent_dt = d.get("parent_doctype")
            if parent_dt and not frappe.get_meta(parent_dt).issingle:
                tx_doctypes.append({"doctype": parent_dt})
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
