# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint
import json


@frappe.whitelist()
def get_potential_duplicates(limit: int = 50, offset: int = 0, min_score: float = 0):
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

    duplicates = frappe.get_all(
        "Party Issue",
        fields=["party", "party_secondary", "score", "status"],
        filters=filters,
        order_by="score desc",
        limit_start=offset,
        limit_page_length=limit,
    )

    # Bulk-fetch party names to avoid N+1 queries
    if duplicates:
        all_party_ids = set()
        for d in duplicates:
            all_party_ids.add(d.party)
            if d.party_secondary:
                all_party_ids.add(d.party_secondary)

        party_names = {
            p.name: p.party_name
            for p in frappe.get_all(
                "Party Master",
                filters={"name": ["in", list(all_party_ids)]},
                fields=["name", "party_name"],
            )
        }

        for d in duplicates:
            d.party_1 = d.party
            d.party_2 = d.party_secondary
            d.party_1_name = party_names.get(d.party_1, d.party_1)
            d.party_2_name = party_names.get(d.party_2, d.party_2)
            d.normalized_name_1 = d.party_1_name
            d.normalized_name_2 = d.party_2_name
            d.similarity_score = d.score

    total = frappe.db.count("Party Issue", filters)

    return {"duplicates": duplicates, "total": total, "limit": limit, "offset": offset}


@frappe.whitelist()
def get_dashboard_stats():
    """
    Get summary statistics. Delegates to canonical modules for health and unlinked
    counts to avoid duplicating logic from transaction_health.py and unlinked_resolver.py.
    """
    def _cached_int(key, fallback):
        val = frappe.cache.get_value(key)
        if val is None:
            return fallback
        try:
            return int(val)
        except Exception:
            return fallback

    stats = {
        "total_parties": _cached_int(
            "uph:stats:total_parties",
            frappe.db.count("Party Master", {"is_group": 0}),
        ),
        "total_groups": _cached_int(
            "uph:stats:total_groups",
            frappe.db.count("Party Master", {"is_group": 1}),
        ),
        "potential_duplicates": _cached_int(
            "uph:stats:duplicate_open",
            frappe.db.count(
                "Party Issue",
                {"issue_type": "Duplicate", "status": ["in", ["Open", "Under Review"]]},
            ),
        ),
        "total_dismissed": _cached_int(
            "uph:stats:duplicate_ignored",
            frappe.db.count(
                "Party Issue", {"issue_type": "Duplicate", "status": "Ignored"}
            ),
        ),
        "total_merged": _cached_int(
            "uph:stats:duplicate_resolved",
            frappe.db.count(
                "Party Issue", {"issue_type": "Duplicate", "status": "Resolved"}
            ),
        ),
        "unlinked_count": _cached_int(
            "uph:stats:unlinked_open",
            frappe.db.count(
                "Party Issue",
                {"issue_type": "Unlinked", "status": ["in", ["Open", "Under Review"]]},
            ),
        ),
        "draft_voucher_count": _cached_int("uph:stats:policy_draft", 0),
        "cancelled_unamended_count": _cached_int("uph:stats:policy_cancelled", 0),
        "unlinked_transaction_count": _cached_int(
            "uph:stats:policy_mismatch", 0
        ),
        "incomplete_parties": _cached_int("uph:stats:incomplete_count", 0),
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
    Dismiss a duplicate issue by setting status to Ignored.
    """
    if not frappe.has_permission("Party Issue", "write"):
        frappe.throw(_("Insufficient permissions to dismiss duplicates"))

    from uph.party.controllers.party_issue_utils import normalize_party_pair

    party_1, party_2 = normalize_party_pair(party_1, party_2)
    issue_name = frappe.db.get_value(
        "Party Issue",
        {
            "party": party_1,
            "party_secondary": party_2,
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
    frappe.db.commit()

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
                "party": party_1,
                "party_secondary": party_2,
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
