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
    Merge secondary party into primary party.

    Args:
        primary_party: The party to keep (receives data)
        secondary_party: The party to merge and delete
        fields_to_keep: Dict of fields to copy from secondary to primary

    Returns:
        Success message
    """
    import json

    if isinstance(fields_to_keep, str):
        fields_to_keep = json.loads(fields_to_keep) if fields_to_keep else {}

    if not frappe.has_permission("Party Master", "write"):
        frappe.throw(_("Insufficient permissions to merge parties"))

    if primary_party == secondary_party:
        frappe.throw(_("Cannot merge a party with itself"))

    primary_doc = frappe.get_doc("Party Master", primary_party)
    secondary_doc = frappe.get_doc("Party Master", secondary_party)

    # Transfer linked parties from secondary to primary
    for party_row in secondary_doc.linked_party:
        if not frappe.db.exists(
            "Party Master Parties", {"parent": primary_party, "party": party_row.party}
        ):
            primary_doc.append(
                "linked_party",
                {"party": party_row.party, "party_type": party_row.party_type},
            )

    # Transfer accounts from secondary to primary
    for acc_row in secondary_doc.accounts:
        if not frappe.db.exists(
            "Party Master Accounts",
            {"parent": primary_party, "company": acc_row.company},
        ):
            primary_doc.append(
                "accounts",
                {
                    "company": acc_row.company,
                    "account": acc_row.account,
                    "default_currency": acc_row.default_currency,
                },
            )

    # Copy specified fields from secondary to primary
    if fields_to_keep:
        for field, value in fields_to_keep.items():
            if value and not primary_doc.get(field):
                primary_doc.set(field, value)

    primary_doc.save(ignore_permissions=True)

    # Update references to secondary party in transactions
    _update_party_master_references(secondary_party, primary_party)

    # Delete secondary party (or mark as merged)
    secondary_doc.flags.ignore_permissions = True
    secondary_doc.delete()

    # Create exclusion to prevent future detection
    frappe.get_doc(
        {
            "doctype": "Duplicate Exclusion",
            "party_1": primary_party,
            "party_2": secondary_party,  # Will be normalized
            "dismissed_reason": _("Merged into {0}").format(primary_party),
        }
    ).insert(ignore_permissions=True)

    frappe.db.commit()

    return {
        "success": True,
        "message": _("{0} has been merged into {1}").format(
            secondary_party, primary_party
        ),
    }


def _update_party_master_references(old_party: str, new_party: str):
    """Update all transaction documents to point to the new party master."""
    # Get all configured DocTypes
    from uph.party.controllers.cache_utils import get_pm_doctypes

    doctypes = get_pm_doctypes()

    for dt_info in doctypes:
        dt = dt_info[0] if isinstance(dt_info, (list, tuple)) else dt_info

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
