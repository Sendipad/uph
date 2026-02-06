# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime

from uph.party.controllers.normalization import NormalizationUtils
from uph.party.doctype.duplicate_exclusion.duplicate_exclusion import is_excluded_pair


@frappe.whitelist()
def get_potential_duplicates(limit: int = 50, offset: int = 0, min_score: float = 70.0):
    """
    Get potential duplicate Party Masters based on similarity scoring.

    Args:
        limit: Maximum number of pairs to return
        offset: Pagination offset
        min_score: Minimum similarity score threshold (0-100)

    Returns:
        List of potential duplicate pairs with similarity scores
    """
    # Get all party masters with party_name
    parties = frappe.get_all(
        "Party Master",
        filters={"is_group": 0},  # Only leaf nodes
        fields=["name", "party_name", "party_type", "party_number"],
        order_by="party_name",
    )

    if not parties:
        return {"duplicates": [], "total": 0}

    # Build normalized name cache
    name_cache = {}
    for p in parties:
        name_cache[p.name] = {
            "original": p,
            "normalized": NormalizationUtils.normalize(p.party_name or ""),
        }

    # Find potential duplicates
    duplicates = []
    seen_pairs = set()

    party_list = list(name_cache.keys())

    for i, p1_name in enumerate(party_list):
        p1_data = name_cache[p1_name]
        if not p1_data["normalized"]:
            continue

        for p2_name in party_list[i + 1 :]:
            p2_data = name_cache[p2_name]
            if not p2_data["normalized"]:
                continue

            # Skip if already checked or excluded
            pair_key = tuple(sorted([p1_name, p2_name]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            # Check if excluded
            if is_excluded_pair(p1_name, p2_name):
                continue

            # Calculate similarity
            score = NormalizationUtils.get_similarity_score(
                p1_data["normalized"], p2_data["normalized"]
            )

            if score >= min_score:
                duplicates.append(
                    {
                        "party_1": p1_data["original"],
                        "party_2": p2_data["original"],
                        "similarity_score": round(score, 1),
                        "normalized_name_1": p1_data["normalized"],
                        "normalized_name_2": p2_data["normalized"],
                    }
                )

    # Sort by score descending
    duplicates.sort(key=lambda x: x["similarity_score"], reverse=True)

    total = len(duplicates)

    # Apply pagination
    paginated = duplicates[offset : offset + limit]

    return {"duplicates": paginated, "total": total, "limit": limit, "offset": offset}


@frappe.whitelist()
def merge_parties(
    primary_party: str, secondary_party: str, fields_to_keep: dict = None
):
    """
    Merge secondary Party Master into primary Party Master.

    Delegates to PartyMergeService which handles:
    - Case A: Full party merge when rule_fieldname values match
    - Case B: Re-linking when rule_fieldname values differ
    - Address/Contact transfer via Dynamic Links
    - Transaction document updates
    - Rollback on failure

    Args:
        primary_party: The Party Master to keep (receives data)
        secondary_party: The Party Master to merge and delete
        fields_to_keep: Dict of fields to copy from secondary to primary

    Returns:
        dict with success status and merge details
    """
    import json

    from uph.party.controllers.party_merge_service import PartyMergeService

    if isinstance(fields_to_keep, str):
        fields_to_keep = json.loads(fields_to_keep) if fields_to_keep else {}

    service = PartyMergeService()
    return service.merge(primary_party, secondary_party, fields_to_keep)


def _update_party_master_references(old_party: str, new_party: str):
    """Update all transaction documents to point to the new party master."""
    # Get all configured DocTypes
    from uph.party.controllers.cache_utils import get_pm_doctypes

    doctypes = get_pm_doctypes()

    for dt_info in doctypes:
        dt = dt_info[0] if isinstance(dt_info, (list, tuple)) else dt_info

        if frappe.get_meta(dt).issingle or frappe.get_meta(dt).is_virtual:
            continue

        if not frappe.db.has_column(dt, "party_master"):
            continue

        frappe.db.sql(
            """
            UPDATE `tab{doctype}`
            SET party_master = %s
            WHERE party_master = %s
        """.format(
                doctype=dt
            ),
            (new_party, old_party),
        )


@frappe.whitelist()
def dismiss_duplicate(party_1: str, party_2: str, reason: str = None):
    """
    Dismiss a potential duplicate pair (mark as non-duplicate).

    Args:
        party_1: First party name
        party_2: Second party name
        reason: Optional reason for dismissal

    Returns:
        Success message
    """
    if not frappe.has_permission("Duplicate Exclusion", "create"):
        frappe.throw(_("Insufficient permissions to dismiss duplicates"))

    # Check if already excluded
    if is_excluded_pair(party_1, party_2):
        return {"success": True, "message": _("This pair has already been excluded")}

    doc = frappe.get_doc(
        {
            "doctype": "Duplicate Exclusion",
            "party_1": party_1,
            "party_2": party_2,
            "dismissed_reason": reason or _("Manually dismissed"),
        }
    )
    doc.insert(ignore_permissions=True)

    frappe.db.commit()

    return {"success": True, "message": _("Duplicate pair has been dismissed")}


@frappe.whitelist()
def get_dashboard_stats():
    """
    Get summary statistics for the data quality dashboard.

    Returns:
        Dict with dashboard metrics
    """
    total_parties = frappe.db.count("Party Master", {"is_group": 0})
    total_groups = frappe.db.count("Party Master", {"is_group": 1})
    total_exclusions = frappe.db.count("Duplicate Exclusion")

    # Count parties without party_number
    incomplete_parties = frappe.db.count(
        "Party Master", {"party_number": ["in", [None, ""]]}
    )

    # Count potential duplicates (cached or calculated)
    potential_dups = _get_potential_duplicate_count()

    return {
        "total_parties": total_parties,
        "total_groups": total_groups,
        "total_exclusions": total_exclusions,
        "incomplete_parties": incomplete_parties,
        "potential_duplicates": potential_dups,
    }


def _get_potential_duplicate_count():
    """Get count of potential duplicates (simplified check)."""
    # Use a sampling approach for performance
    result = get_potential_duplicates(limit=100, min_score=80.0)
    return result.get("total", 0)
