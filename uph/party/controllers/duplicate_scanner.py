# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

"""
Background Duplicate Scanning Job

Runs periodically (daily) to scan all Party Masters for potential duplicates
and store results in Party Issue (issue_type=Duplicate).

Uses blocking strategy (first N characters) + rapidfuzz for efficient
similarity detection without O(n²) runtime overhead on the dashboard.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime

from uph.party.controllers.party_issue_utils import (
    create_party_issue_if_missing,
    get_issue_status,
    normalize_party_pair,
    TERMINAL_STATUSES,
)
from uph.party.controllers.cache_utils import invalidate_dashboard_stats


def run_duplicate_scan(
    min_score: float = 80.0, block_len: int = 2, chunk_size: int = 250
):
    """
    Background job to scan all Party Masters for duplicates.
    Creates Party Issue records (Duplicate) for new detections only.

    Designed to be called via frappe.enqueue() or scheduler_events.
    """
    try:
        from rapidfuzz import fuzz, process
    except ImportError:
        frappe.log_error(
            title=_("Duplicate Scan Skipped"),
            message=_(
                "rapidfuzz is not installed. Install with: pip install rapidfuzz"
            ),
        )
        return

    from uph.party.controllers.normalization import NormalizationUtils

    frappe.publish_realtime(
        "duplicate_scan_progress",
        {"status": "started", "timestamp": str(now_datetime())},
    )

    # Load all non-group parties
    parties = frappe.get_all(
        "Party Master",
        filters={"is_group": 0},
        fields=["name", "party_name", "party_type", "normalized_party_name"],
        order_by="normalized_party_name",
    )

    if not parties:
        return

    # Build normalized names for parties missing them
    for p in parties:
        if not p.normalized_party_name:
            p.normalized_party_name = NormalizationUtils.normalize_party_name(
                p.party_name or ""
            )

    # Group by prefix blocks
    blocks = {}
    for p in parties:
        norm = p.normalized_party_name or ""
        if not norm:
            continue
        prefix = norm[:block_len] if len(norm) >= block_len else norm
        blocks.setdefault(prefix, []).append(p)

    total_found = 0
    total_blocks = len(blocks)

    for idx, (prefix, block) in enumerate(blocks.items()):
        if len(block) < 2:
            continue

        names = [p.normalized_party_name or "" for p in block]

        for i in range(len(block) - 1):
            p1 = block[i]
            p1_norm = names[i]
            if not p1_norm:
                continue

            start = i + 1
            while start < len(block):
                chunk_names = names[start : start + chunk_size]
                scores = process.cdist(
                    [p1_norm],
                    chunk_names,
                    scorer=fuzz.ratio,
                    score_cutoff=min_score,
                )

                for j, score in enumerate(scores[0]):
                    if score <= 0:
                        continue

                    p2 = block[start + j]
                    party_1, party_2 = normalize_party_pair(p1.name, p2.name)
                    pair_key = (party_1, party_2)

                    existing_issue = get_issue_status(
                        party_master=party_1,
                        reference_doctype="Party Master",
                        reference_name=party_2,
                        issue_type="Duplicate",
                    )
                    if existing_issue:
                        # Do not re-open Ignored/Resolved duplicates
                        if existing_issue.status in TERMINAL_STATUSES:
                            continue
                        # Open/Under Review already exists
                        continue

                    total_found += 1
                    severity = (
                        "Critical"
                        if score >= 95
                        else (
                            "High"
                            if score >= 90
                            else ("Medium" if score >= 80 else "Low")
                        )
                    )
                    create_party_issue_if_missing(
                        party_master=party_1,
                        issue_type="Duplicate",
                        severity=severity,
                        status="Open",
                        score=float(score),
                        source_engine="duplicate_scanner",
                        reference_doctype="Party Master",
                        reference_name=party_2,
                        details={
                            "blocking_key": prefix,
                            "normalized_name_1": p1_norm,
                            "normalized_name_2": p2.normalized_party_name or "",
                        },
                    )

                start += chunk_size

        # Progress update every 10 blocks
        if idx % 10 == 0:
            frappe.publish_realtime(
                "duplicate_scan_progress",
                {
                    "status": "scanning",
                    "progress": f"{idx + 1}/{total_blocks} blocks",
                    "found": total_found,
                },
            )

    # Invalidate dashboard stats cache
    invalidate_dashboard_stats()

    frappe.publish_realtime(
        "duplicate_scan_progress",
        {
            "status": "completed",
            "total_found": total_found,
            "timestamp": str(now_datetime()),
        },
    )

    frappe.logger("uph").info(
        f"Duplicate scan completed: {total_found} candidates found across {total_blocks} blocks"
    )

    # Sync and auto-resolve issues that are no longer valid
    sync_duplicate_issues()


def sync_duplicate_issues():
    """
    Auto-resolve Duplicate issues that have been fixed outside the dashboard
    (e.g., merged directly via Python API or one party was deleted).
    """
    open_issues = frappe.get_all(
        "Party Issue",
        filters={
            "issue_type": "Duplicate",
            "status": ["in", ["Open", "Under Review"]],
        },
        fields=[
            "name",
            "party_master",
            "reference_doctype",
            "reference_name",
        ],
    )

    if not open_issues:
        return

    now = frappe.utils.now_datetime()
    resolved_count = 0

    for issue in open_issues:
        party_1 = issue.party_master
        party_2 = issue.reference_name

        if not party_1 or not party_2:
            continue

        p1_exists = frappe.db.exists("Party Master", party_1)
        p2_exists = frappe.db.exists("Party Master", party_2)

        # 1. Check if either document no longer exists
        if not p1_exists or not p2_exists:
            frappe.db.set_value(
                "Party Issue",
                issue.name,
                {
                    "status": "Resolved",
                    "resolved_on": now,
                    "resolved_by": "Administrator",
                    "dismiss_reason": "Orphaned: One or both parties no longer exist",
                },
            )
            resolved_count += 1
            continue

        # 2. Check if one is an alias of another (merged)
        # Note: In ERPNext, merging usually renames one document to the other
        # If they are merged, they become the same document name
        if party_1 == party_2:
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

    if resolved_count:
        frappe.logger("uph").info(f"Duplicate Sync: Resolved {resolved_count} issues")


@frappe.whitelist()
def enqueue_duplicate_scan(min_score: float = 80.0):
    """
    API endpoint to trigger a background duplicate scan.
    Enqueues the scan job to run asynchronously.
    """
    if not frappe.has_permission("Party Master", "write"):
        frappe.throw(
            _("Insufficient permissions to run duplicate scan"),
            frappe.PermissionError,
        )

    frappe.enqueue(
        run_duplicate_scan,
        min_score=float(min_score),
        queue="long",
        timeout=1800,
        job_id="uph_duplicate_scan",
        deduplicate=True,
    )

    return {"success": True, "message": _("Duplicate scan has been queued")}
