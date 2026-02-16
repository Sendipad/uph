# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint
import json


@frappe.whitelist()
def get_potential_duplicates(limit: int = 50, offset: int = 0, min_score: float = 0):
    """
    Get potential duplicate Party Masters from pre-computed Potential Duplicate table.
    """
    if not frappe.has_permission("Party Master", "read"):
        frappe.throw(_("Not permitted to read Party Master"), frappe.PermissionError)

    limit = cint(limit) or 50
    offset = cint(offset) or 0

    filters = {"status": "Detected"}
    if float(min_score) > 0:
        filters["similarity_score"] = [">=", float(min_score)]

    duplicates = frappe.get_all(
        "Potential Duplicate",
        fields=["party_1", "party_2", "similarity_score", "status"],
        filters=filters,
        order_by="similarity_score desc",
        limit_start=offset,
        limit_page_length=limit,
    )

    # Bulk-fetch party names to avoid N+1 queries
    if duplicates:
        all_party_ids = set()
        for d in duplicates:
            all_party_ids.add(d.party_1)
            all_party_ids.add(d.party_2)

        party_names = {
            p.name: p.party_name
            for p in frappe.get_all(
                "Party Master",
                filters={"name": ["in", list(all_party_ids)]},
                fields=["name", "party_name"],
            )
        }

        for d in duplicates:
            d.party_1_name = party_names.get(d.party_1, d.party_1)
            d.party_2_name = party_names.get(d.party_2, d.party_2)
            d.normalized_name_1 = d.party_1_name
            d.normalized_name_2 = d.party_2_name

    total = frappe.db.count("Potential Duplicate", filters)

    return {"duplicates": duplicates, "total": total, "limit": limit, "offset": offset}


@frappe.whitelist()
def get_dashboard_stats():
    """
    Get summary statistics. Delegates to canonical modules for health and unlinked
    counts to avoid duplicating logic from transaction_health.py and unlinked_resolver.py.
    """
    from uph.party.controllers.transaction_health import get_health_counts
    from uph.party.controllers.unlinked_resolver import get_unlinked_count

    # Health counts from canonical module (uses its own Redis cache)
    health = get_health_counts()

    stats = {
        "total_parties": frappe.db.count("Party Master", {"is_group": 0}),
        "total_groups": frappe.db.count("Party Master", {"is_group": 1}),
        "unlinked_count": get_unlinked_count(),
        "draft_voucher_count": health.get("draft_voucher_count", 0),
        "cancelled_unamended_count": health.get("cancelled_unamended_count", 0),
        "incomplete_parties": cint(
            frappe.cache.get_value("uph:stats:incomplete_count") or 0
        ),
        "potential_duplicates": frappe.db.count(
            "Potential Duplicate", {"status": "Detected"}
        ),
        "total_dismissed": frappe.db.count("Duplicate Exclusion"),
        "total_merged": frappe.db.count("Potential Duplicate", {"status": "Merged"}),
        "last_updated": frappe.cache.get_value("uph:stats:last_updated"),
    }
    return stats


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
    Dismiss a potential duplicate pair.
    Updates 'Potential Duplicate' status and creates 'Duplicate Exclusion' record.
    """
    if not frappe.has_permission("Duplicate Exclusion", "create"):
        frappe.throw(_("Insufficient permissions to dismiss duplicates"))

    # 1. Update Potential Duplicate if exists
    # Check both directions just in case
    potential = frappe.db.get_value(
        "Potential Duplicate", {"party_1": party_1, "party_2": party_2}, "name"
    )

    if not potential:
        potential = frappe.db.get_value(
            "Potential Duplicate", {"party_1": party_2, "party_2": party_1}, "name"
        )

    if potential:
        frappe.db.set_value("Potential Duplicate", potential, "status", "Dismissed")

    # 2. Link to existing Duplicate Exclusion logic
    # Check if already excluded
    from uph.party.doctype.duplicate_exclusion.duplicate_exclusion import (
        is_excluded_pair,
    )

    if is_excluded_pair(party_1, party_2):
        return {"success": True, "message": _("This pair is already excluded")}

    # Normalize order for Exclusion
    if party_1 > party_2:
        party_1, party_2 = party_2, party_1

    # Insert into Duplicate Exclusion
    doc = frappe.get_doc(
        {
            "doctype": "Duplicate Exclusion",
            "party_1": party_1,
            "party_2": party_2,
            "status": "Dismissed",
            "dismissed_by": frappe.session.user,
            "dismissed_on": frappe.utils.today(),
            "dismissed_reason": reason or _("Manually dismissed"),
        }
    )
    doc.insert(ignore_permissions=True)

    # Decrement cache count immediately for UX
    count = cint(frappe.cache.get_value("uph:stats:duplicate_count") or 0)
    if count > 0:
        frappe.cache.set_value("uph:stats:duplicate_count", count - 1)

    return {"success": True, "message": _("Duplicate pair has been dismissed")}


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
        # Update Potential Duplicate status
        potential = frappe.db.get_value(
            "Potential Duplicate",
            {
                "party_1": ["in", [primary_party, secondary_party]],
                "party_2": ["in", [primary_party, secondary_party]],
            },
            "name",
        )
        if potential:
            frappe.db.set_value("Potential Duplicate", potential, "status", "Merged")

        # Trigger stats refresh
        trigger_refresh()

    return result
