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

Both scanners are idempotent (they call ``create_party_issue_if_missing``),
so running them on a site that already has partial data is safe.
"""

import frappe


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

    frappe.flags.in_patch = False
