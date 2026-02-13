# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime


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
    if not frappe.has_permission("Party Master", "read"):
        frappe.throw(_("Not permitted to read Party Master"), frappe.PermissionError)

    limit = int(limit)
    offset = int(offset)
    min_score = float(min_score)
    target_size = max(0, offset + limit)

    # Pre-load all excluded pairs into a set for O(1) lookup
    excluded_pairs = _get_excluded_pairs_set()
    seen_pairs = set()

    # Use blocking strategy: group by first 2 characters for speed
    block_len = 2
    chunk_size = 250  # process.cdist chunk size to cap memory

    # Handle missing normalized names in a small side batch
    missing_by_prefix = _get_missing_normalized_parties(block_len)

    prefixes = _get_normalized_prefixes(block_len)
    if not prefixes and not missing_by_prefix:
        return {"duplicates": [], "total": 0, "limit": limit, "offset": offset}

    # Keep only top-N by score to reduce memory pressure
    import heapq
    import itertools

    top_matches = []
    total_matches = 0
    counter = itertools.count()

    def consider_match(data, score):
        nonlocal total_matches
        total_matches += 1
        if target_size <= 0:
            return
        item = (score, next(counter), data)
        if len(top_matches) < target_size:
            heapq.heappush(top_matches, item)
        elif score > top_matches[0][0]:
            heapq.heapreplace(top_matches, item)

    for prefix in prefixes:
        block_parties = _get_parties_by_prefix(prefix, block_len)
        if prefix in missing_by_prefix:
            block_parties.extend(missing_by_prefix.pop(prefix))

        _process_duplicate_block(
            block_parties,
            min_score,
            chunk_size,
            excluded_pairs,
            seen_pairs,
            consider_match,
        )

    # Process any remaining missing prefixes not present in stored prefixes
    for leftover in missing_by_prefix.values():
        _process_duplicate_block(
            leftover,
            min_score,
            chunk_size,
            excluded_pairs,
            seen_pairs,
            consider_match,
        )

    # Sort by score descending and paginate
    top_matches.sort(key=lambda x: x[0], reverse=True)
    duplicates = [d for _, __, d in top_matches]
    paginated = duplicates[offset : offset + limit]

    return {
        "duplicates": paginated,
        "total": total_matches,
        "limit": limit,
        "offset": offset,
    }


def _get_normalized_prefixes(block_len: int) -> list[str]:
    """Get distinct normalized name prefixes directly from the DB."""
    rows = frappe.db.sql(
        """
        SELECT DISTINCT SUBSTRING(normalized_party_name, 1, %s) AS prefix
        FROM `tabParty Master`
        WHERE is_group = 0
          AND normalized_party_name IS NOT NULL
          AND normalized_party_name != ''
        ORDER BY prefix
        """,
        (block_len,),
        as_dict=True,
    )
    return [r.prefix for r in rows if r.prefix]


def _get_missing_normalized_parties(block_len: int) -> dict:
    """Compute normalized names for parties missing precomputed value."""
    from uph.party.controllers.normalization import NormalizationUtils

    missing = frappe.get_all(
        "Party Master",
        filters={"is_group": 0, "normalized_party_name": ["is", "not set"]},
        fields=["name", "party_name", "party_type", "party_number"],
        order_by="party_name",
    )

    grouped = {}
    for p in missing or []:
        norm_name = NormalizationUtils.normalize_party_name(p.party_name or "")
        if not norm_name:
            continue
        prefix = norm_name[:block_len] if len(norm_name) >= block_len else norm_name
        grouped.setdefault(prefix or "_", []).append(
            {
                "name": p.name,
                "party_name": p.party_name,
                "party_type": p.party_type,
                "party_number": p.party_number,
                "normalized_name": norm_name,
            }
        )
    return grouped


def _get_parties_by_prefix(prefix: str, block_len: int) -> list[dict]:
    """Fetch parties by normalized name prefix and prepare block entries."""
    parties = frappe.get_all(
        "Party Master",
        filters={
            "is_group": 0,
            "normalized_party_name": ["like", f"{prefix}%"],
        },
        fields=[
            "name",
            "party_name",
            "party_type",
            "party_number",
            "normalized_party_name",
        ],
        order_by="normalized_party_name",
    )

    result = []
    for p in parties or []:
        result.append(
            {
                "name": p.name,
                "party_name": p.party_name,
                "party_type": p.party_type,
                "party_number": p.party_number,
                "normalized_name": p.normalized_party_name or "",
            }
        )
    return result


def _process_duplicate_block(
    block_parties: list[dict],
    min_score: float,
    chunk_size: int,
    excluded_pairs: set,
    seen_pairs: set,
    consider_match,
):
    try:
        from rapidfuzz import fuzz, process
    except ImportError:
        frappe.throw(
            _(
                "rapidfuzz is required for duplicate detection. Install with: pip install rapidfuzz"
            )
        )

    if not block_parties or len(block_parties) < 2:
        return

    names = [p.get("normalized_name") or "" for p in block_parties]
    if not any(names):
        return

    for i in range(len(block_parties) - 1):
        p1 = block_parties[i]
        p1_norm = names[i]
        if not p1_norm:
            continue

        start = i + 1
        while start < len(block_parties):
            chunk_names = names[start : start + chunk_size]
            scores = process.cdist(
                [p1_norm],
                chunk_names,
                scorer=fuzz.ratio,
                score_cutoff=min_score,
            )
            if scores is None:
                start += chunk_size
                continue
            if hasattr(scores, "size") and scores.size == 0:
                start += chunk_size
                continue

            row = scores[0]
            for j, score in enumerate(row):
                if score < min_score:
                    continue
                p2 = block_parties[start + j]
                pair_key = tuple(sorted([p1["name"], p2["name"]]))
                if pair_key in seen_pairs or pair_key in excluded_pairs:
                    continue
                seen_pairs.add(pair_key)
                consider_match(
                    {
                        "party_1": {
                            "name": p1["name"],
                            "party_name": p1.get("party_name"),
                            "party_type": p1.get("party_type"),
                            "party_number": p1.get("party_number"),
                        },
                        "party_2": {
                            "name": p2["name"],
                            "party_name": p2.get("party_name"),
                            "party_type": p2.get("party_type"),
                            "party_number": p2.get("party_number"),
                        },
                        "similarity_score": round(float(score), 1),
                        "normalized_name_1": p1_norm,
                        "normalized_name_2": p2.get("normalized_name") or "",
                    },
                    float(score),
                )
            start += chunk_size


def _get_excluded_pairs_set():
    """Load Dismissed/Merged pairs into a set for O(1) lookup during scanning."""
    exclusions = frappe.get_all(
        "Duplicate Exclusion",
        filters={"status": ["in", ["Dismissed", "Merged"]]},
        fields=["party_1", "party_2"],
    )
    excluded_set = set()
    for exc in exclusions:
        pair_key = tuple(sorted([exc.party_1, exc.party_2]))
        excluded_set.add(pair_key)
    return excluded_set


@frappe.whitelist()
def merge_parties(
    primary_party: str,
    secondary_party: str,
    fields_to_keep: dict = None,
    ignore_validation: bool = False,
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
    return service.merge(
        primary_party,
        secondary_party,
        fields_to_keep,
        ignore_validation=ignore_validation,
    )


def _update_party_master_references(old_party: str, new_party: str):
    """Update all transaction documents to point to the new party master."""
    # Get all configured DocTypes
    from uph.party.controllers.cache_utils import get_pm_doctypes

    doctypes = get_pm_doctypes()

    for dt_info in doctypes:
        dt = dt_info[0] if isinstance(dt_info, (list, tuple)) else dt_info

        meta = frappe.get_meta(dt)
        if meta.issingle or meta.is_virtual:
            continue

        if not frappe.db.has_column(dt, "party_master"):
            continue

        # Use frappe.qb instead of raw SQL .format() for table safety
        table = frappe.qb.DocType(dt)
        frappe.qb.update(table).set(table.party_master, new_party).where(
            table.party_master == old_party
        ).run()


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

    from uph.party.doctype.duplicate_exclusion.duplicate_exclusion import (
        is_excluded_pair,
    )

    # Check if already excluded
    if is_excluded_pair(party_1, party_2):
        return {"success": True, "message": _("This pair has already been excluded")}

    # Normalize order
    if party_1 > party_2:
        party_1, party_2 = party_2, party_1

    # Check if there's a Detected record to update
    existing = frappe.db.get_value(
        "Duplicate Exclusion",
        {"party_1": party_1, "party_2": party_2, "status": "Detected"},
        "name",
    )

    if existing:
        frappe.db.set_value(
            "Duplicate Exclusion",
            existing,
            {
                "status": "Dismissed",
                "dismissed_by": frappe.session.user,
                "dismissed_on": frappe.utils.today(),
                "dismissed_reason": reason or _("Manually dismissed"),
            },
        )
    else:
        doc = frappe.get_doc(
            {
                "doctype": "Duplicate Exclusion",
                "party_1": party_1,
                "party_2": party_2,
                "status": "Dismissed",
                "dismissed_reason": reason or _("Manually dismissed"),
            }
        )
        doc.insert(ignore_permissions=True)

    # Invalidate dashboard stats cache
    frappe.cache.delete_value("uph:dashboard_stats")

    return {"success": True, "message": _("Duplicate pair has been dismissed")}


@frappe.whitelist()
def get_dashboard_stats():
    """
    Get summary statistics for the data quality dashboard.
    Uses Redis cache with 5-minute TTL to avoid repeated DB queries.

    Returns:
        Dict with dashboard metrics
    """
    cache_key = "uph:dashboard_stats"
    if cached := frappe.cache.get_value(cache_key):
        return cached

    total_parties = frappe.db.count("Party Master", {"is_group": 0})
    total_groups = frappe.db.count("Party Master", {"is_group": 1})
    total_dismissed = frappe.db.count("Duplicate Exclusion", {"status": "Dismissed"})
    total_merged = frappe.db.count("Duplicate Exclusion", {"status": "Merged"})

    # Count parties without party_number
    incomplete_parties = frappe.db.count(
        "Party Master", {"party_number": ["in", [None, ""]]}
    )

    # Count potential duplicates from Duplicate Exclusion (Detected status)
    potential_dups = frappe.db.count("Duplicate Exclusion", {"status": "Detected"})

    # Unlinked role records count
    from uph.party.controllers.unlinked_resolver import get_unlinked_count

    unlinked_count = get_unlinked_count()

    # Transaction health counts
    from uph.party.controllers.transaction_health import get_health_counts

    health = get_health_counts()

    stats = {
        "total_parties": total_parties,
        "total_groups": total_groups,
        "total_dismissed": total_dismissed,
        "total_merged": total_merged,
        "incomplete_parties": incomplete_parties,
        "potential_duplicates": potential_dups,
        "unlinked_count": unlinked_count,
        "draft_voucher_count": health.get("draft_voucher_count", 0),
        "cancelled_unamended_count": health.get("cancelled_unamended_count", 0),
    }

    frappe.cache.set_value(cache_key, stats, expires_in_sec=300)
    return stats
