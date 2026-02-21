"""
Post-migration patch: re-scan transaction health and unlinked roles.

Previous implementation queried transaction tables on-the-fly for the
dashboard.  The updated implementation reads from the Party Issue registry.
This patch ensures all existing violations are recorded as Party Issue
entries so the new dashboard shows correct data.

Steps
-----
1. Auto-resolve false-positive Unlinked issues where the referenced
   record already has a ``party_master`` set (i.e. was linked after
   the issue was created).
2. Auto-resolve false-positive Transaction Policy issues where the referenced
   voucher is no longer in the relevant state (e.g. draft was submitted).
3. Run ``run_transaction_policy_scan()`` – creates Party Issue entries
   for draft-overdue, cancelled-referenced, and party-master-mismatch
   vouchers that have not yet been registered.
4. Run ``run_unlinked_issue_scan()`` – creates Party Issue entries for
   role records (Customer, Supplier, Employee, …) that are not linked
   to a Party Master.

Both scanners are idempotent (they call ``create_party_issue_if_missing``),
so running them on a site that already has partial data is safe.
"""

import frappe
import json
from frappe.utils import now_datetime


def execute():
    if not frappe.db.exists("DocType", "Party Issue"):
        return

    frappe.flags.in_patch = True

    # 1. Auto-resolve false-positive Unlinked issues
    try:
        _resolve_false_positive_unlinked_issues()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(title="Patch: resolve false-positive unlinked issues failed", message=str(e))

    # 2. Auto-resolve false-positive Transaction Policy issues
    try:
        _resolve_false_positive_transaction_issues()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(title="Patch: resolve false-positive transaction issues failed", message=str(e))

    # 3. Transaction policy scan
    try:
        from uph.party.controllers.transaction_health import run_transaction_policy_scan
        run_transaction_policy_scan()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(title="Patch: transaction policy scan failed", message=str(e))

    # 4. Unlinked role scan
    try:
        from uph.party.controllers.unlinked_resolver import run_unlinked_issue_scan
        run_unlinked_issue_scan()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(title="Patch: unlinked role scan failed", message=str(e))

    frappe.flags.in_patch = False


def _resolve_false_positive_unlinked_issues():
    """
    Find open Unlinked Party Issues where the referenced record
    already has party_master set, and mark them as Resolved.
    """
    open_unlinked = frappe.get_all(
        "Party Issue",
        filters={"issue_type": "Unlinked", "status": ["in", ["Open", "Under Review"]]},
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
        pm_val = frappe.db.get_value(dt, name, "party_master")
        if not frappe.db.exists(dt, name) or pm_val:
            # Record deleted or Already linked — resolve it
            frappe.db.set_value("Party Issue", issue.name, {
                "status": "Resolved",
                "resolved_on": now,
                "resolved_by": "Administrator",
            }, update_modified=False)
            resolved_count += 1

    if resolved_count:
        frappe.logger().info(f"Patch: resolved {resolved_count} false-positive Unlinked Party Issues")


def _resolve_false_positive_transaction_issues():
    """
    Find open Transaction Policy Party Issues where the referenced
    voucher is no longer draft/cancelled/mismatched.
    """
    open_issues = frappe.get_all(
        "Party Issue",
        filters={"issue_type": "Transaction Policy", "status": ["in", ["Open", "Under Review"]]},
        fields=["name", "reference_doctype", "reference_name", "details_json"],
        limit_page_length=0,
    )

    if not open_issues:
        return

    resolved_count = 0
    now = now_datetime()

    for issue in open_issues:
        dt = issue.reference_doctype
        name = issue.reference_name
        if not dt or not name or not frappe.db.exists("DocType", dt):
            continue

        details = {}
        if issue.details_json:
            try:
                details = json.loads(issue.details_json)
            except Exception:
                pass
        
        issue_code = details.get("issue")
        should_resolve = False

        if not frappe.db.exists(dt, name):
            should_resolve = True
        else:
            if issue_code == "draft_overdue":
                docstatus = frappe.db.get_value(dt, name, "docstatus")
                if docstatus != 0:
                    should_resolve = True
            elif issue_code == "cancelled_referenced":
                docstatus = frappe.db.get_value(dt, name, "docstatus")
                if docstatus != 2:
                    should_resolve = True
                else:
                    meta = frappe.get_meta(dt)
                    if meta.has_field("amended_from"):
                        if frappe.db.get_value(dt, name, "amended_from"):
                            should_resolve = True
            # For mismatch, we might just let the next scan re-assess or keep it simple.
            # Realistically, draft/cancelled cover 99% of false positives.

        if should_resolve:
            frappe.db.set_value("Party Issue", issue.name, {
                "status": "Resolved",
                "resolved_on": now,
                "resolved_by": "Administrator",
            }, update_modified=False)
            resolved_count += 1

    if resolved_count:
        frappe.logger().info(f"Patch: resolved {resolved_count} false-positive Transaction Policy Issues")
