# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime

from rapidfuzz import fuzz, process

from uph.party.doctype.duplicate_exclusion.duplicate_exclusion import is_excluded_pair


@frappe.whitelist()
def get_potential_duplicates(limit: int = 50, offset: int = 0, min_score: float = 70.0):
    """
    Get potential duplicate Party Masters based on similarity scoring.

    Uses optimized batch processing with rapidfuzz for performance.
    Leverages pre-computed normalized_party_name from Party Master.

    Args:
        limit: Maximum number of pairs to return
        offset: Pagination offset
        min_score: Minimum similarity score threshold (0-100)

    Returns:
        List of potential duplicate pairs with similarity scores
    """
    limit = int(limit)
    offset = int(offset)
    min_score = float(min_score)

    # Get all party masters with pre-computed normalized_party_name
    parties = frappe.get_all(
        "Party Master",
        filters={"is_group": 0},
        fields=[
            "name",
            "party_name",
            "party_type",
            "party_number",
            "normalized_party_name",
        ],
        order_by="party_name",
    )

    if not parties or len(parties) < 2:
        return {"duplicates": [], "total": 0}

    # Build lookup dictionaries for fast access
    party_by_name = {p.name: p for p in parties}

    # Get normalized names (use pre-computed or compute on-the-fly)
    normalized_names = {}
    for p in parties:
        norm_name = p.normalized_party_name or ""
        if not norm_name and p.party_name:
            # Fallback: compute normalization if not stored
            from uph.party.controllers.normalization import NormalizationUtils

            norm_name = NormalizationUtils.normalize_party_name(p.party_name)
        normalized_names[p.name] = norm_name

    # Filter out parties without normalized names
    valid_parties = [
        (p.name, normalized_names[p.name])
        for p in parties
        if normalized_names.get(p.name)
    ]

    if len(valid_parties) < 2:
        return {"duplicates": [], "total": 0}

    # Pre-load all excluded pairs into a set for O(1) lookup
    excluded_pairs = _get_excluded_pairs_set()

    # Use blocking strategy: group by first 2 characters for dramatic speedup
    # Only compare parties within the same block or similar blocks
    duplicates = []
    seen_pairs = set()

    # Build blocks based on first 2 chars of normalized name
    blocks = {}
    for party_name, norm_name in valid_parties:
        if len(norm_name) >= 2:
            block_key = norm_name[:2]
        else:
            block_key = norm_name or "_"
        blocks.setdefault(block_key, []).append((party_name, norm_name))

    # Process each block - compare within blocks
    for block_key, block_parties in blocks.items():
        if len(block_parties) < 2:
            continue

        # Extract names for rapidfuzz batch processing
        names_list = [norm for _, norm in block_parties]
        party_names_list = [pname for pname, _ in block_parties]

        # Use rapidfuzz.process.cdist for efficient pairwise comparison
        # This is O(n*m) but highly optimized in C
        for i, (p1_name, p1_norm) in enumerate(block_parties):
            # Compare with remaining parties in the block
            remaining = [(pname, norm) for pname, norm in block_parties[i + 1 :]]
            if not remaining:
                continue

            remaining_names = [norm for _, norm in remaining]
            remaining_party_names = [pname for pname, _ in remaining]

            # Batch extract matches above threshold
            matches = process.extract(
                p1_norm,
                remaining_names,
                scorer=fuzz.ratio,
                score_cutoff=min_score,
                limit=None,  # Return all matches above threshold
            )

            for match_norm, score, match_idx in matches:
                p2_name = remaining_party_names[match_idx]

                # Create canonical pair key for deduplication
                pair_key = tuple(sorted([p1_name, p2_name]))

                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                # Check exclusion using set lookup O(1)
                if pair_key in excluded_pairs:
                    continue

                p1 = party_by_name[p1_name]
                p2 = party_by_name[p2_name]

                duplicates.append(
                    {
                        "party_1": p1,
                        "party_2": p2,
                        "similarity_score": round(score, 1),
                        "normalized_name_1": p1_norm,
                        "normalized_name_2": normalized_names[p2_name],
                    }
                )

    # Sort by score descending
    duplicates.sort(key=lambda x: x["similarity_score"], reverse=True)

    total = len(duplicates)

    # Apply pagination
    paginated = duplicates[offset : offset + limit]

    return {"duplicates": paginated, "total": total, "limit": limit, "offset": offset}


def _get_excluded_pairs_set():
    """Load all excluded pairs into a set for O(1) lookup."""
    exclusions = frappe.get_all("Duplicate Exclusion", fields=["party_1", "party_2"])
    excluded_set = set()
    for exc in exclusions:
        pair_key = tuple(sorted([exc.party_1, exc.party_2]))
        excluded_set.add(pair_key)
    return excluded_set


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
