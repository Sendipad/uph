"""
Post-migration patch: re-scan transaction health and unlinked roles.

Previous implementation queried transaction tables on-the-fly for the
dashboard.  The updated implementation reads from the Party Issue registry.
This patch ensures all existing violations are recorded as Party Issue
entries so the new dashboard shows correct data.

Steps
-----
1. Run ``run_transaction_policy_scan()`` – creates Party Issue entries
   for draft-overdue, cancelled-referenced, and party-master-mismatch
   vouchers that have not yet been registered.
2. Run ``run_unlinked_issue_scan()`` – creates Party Issue entries for
   role records (Customer, Supplier, Employee, …) that are not linked
   to a Party Master.
3. Auto-resolve false-positive Unlinked issues where the referenced
   record already has a ``party_master`` set (i.e. was linked after
   the issue was created).

Both scanners are idempotent (they call ``create_party_issue_if_missing``),
so running them on a site that already has partial data is safe.
"""

import frappe
from frappe.utils import now_datetime


def execute():
    if not frappe.db.exists("DocType", "Party Issue"):
        return

    frappe.flags.in_patch = True

    # 1. Transaction policy scan
    try:
        from uph.party.controllers.transaction_health import (
            run_transaction_policy_scan,
        )

        run_transaction_policy_scan()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(
            title="Patch: transaction policy scan failed",
            message=str(e),
        )

    # 2. Unlinked role scan
    try:
        from uph.party.controllers.unlinked_resolver import (
            run_unlinked_issue_scan,
        )

        run_unlinked_issue_scan()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(
            title="Patch: unlinked role scan failed",
            message=str(e),
        )

    # 3. Auto-resolve false-positive Unlinked issues
    #    (records that have been linked to a Party Master after the issue was created)
    try:
        _resolve_false_positive_unlinked_issues()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(
            title="Patch: resolve false-positive unlinked issues failed",
            message=str(e),
        )

    frappe.flags.in_patch = False


def _resolve_false_positive_unlinked_issues():
    """
    Find open Unlinked Party Issues where the referenced record
    already has party_master set, and mark them as Resolved.
    """
    open_unlinked = frappe.get_all(
        "Party Issue",
        filters={
            "issue_type": "Unlinked",
            "status": ["in", ["Open", "Under Review"]],
        },
        fields=["name", "reference_doctype", "reference_name"],
        limit_page_length=0,
    )

    if not open_unlinked:
        return

    resolved_count = 0
    now = now_datetime()

    for issue in open_unlinked:
        dt = issue.reference_doctype
        name = issue.reference_name
        if not dt or not name:
            continue
        if not frappe.db.exists("DocType", dt):
            continue

        meta = frappe.get_meta(dt)
        if not meta.has_field("party_master"):
            continue

        # Check if the record still exists
        if not frappe.db.exists(dt, name):
            # Record deleted — resolve the issue
            frappe.db.set_value(
                "Party Issue",
                issue.name,
                {
                    "status": "Resolved",
                    "resolved_on": now,
                    "resolved_by": "Administrator",
                },
                update_modified=False,
            )
            resolved_count += 1
            continue

        pm_val = frappe.db.get_value(dt, name, "party_master")
        if pm_val:
            # Already linked — this is a false positive, resolve it
            frappe.db.set_value(
                "Party Issue",
                issue.name,
                {
                    "status": "Resolved",
                    "resolved_on": now,
                    "resolved_by": "Administrator",
                },
                update_modified=False,
            )
            resolved_count += 1

    if resolved_count:
        frappe.logger().info(
            f"Patch: resolved {resolved_count} false-positive Unlinked Party Issues"
        )
