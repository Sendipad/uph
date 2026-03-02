# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from uph.party.controllers.transaction_health import (
    sync_transaction_health_issues,
    get_health_counts,
)


class TestTransactionHealth(FrappeTestCase):
    def setUp(self):
        # Create a parent party master group
        self.parent = frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": f"Test Parent Group {frappe.generate_hash(length=8)}",
                "is_group": 1,
            }
        ).insert(ignore_permissions=True)

        # Create a party master
        self.party = frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": f"Test Health {frappe.generate_hash(length=8)}",
                "party_type": "Customer",
                "parent_party_master": self.parent.name,
                "is_group": 0,
            }
        ).insert(ignore_permissions=True)
        self.party.db_set("status", "Active")

        # Create a custom customer for this test, then link to the party master
        # without validation to avoid duplicate PM linkage issues on dirty test sites.
        self.customer = frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": f"Test Customer {frappe.generate_hash(length=8)}",
                "customer_group": frappe.get_all("Customer Group", limit=1)[0].name,
                "territory": frappe.get_all("Territory", limit=1)[0].name,
            }
        ).insert(ignore_permissions=True)
        self.customer.db_set("party_master", self.party.name)

        frappe.db.commit()

    def tearDown(self):
        frappe.db.rollback()

    def test_cancelled_amended_logic(self):
        # Create an original invoice
        si1 = frappe.get_doc(
            {
                "doctype": "Sales Invoice",
                "customer": self.customer.name,
                "party_master": self.party.name,
                "docstatus": 1,
                "items": [
                    {
                        "item_code": frappe.get_all("Item", limit=1)[0].name,
                        "qty": 1,
                        "rate": 100,
                    }
                ],
                "set_posting_time": 1,
            }
        ).insert(ignore_permissions=True)
        si1.reload()
        si1.submit()

        # Cancel the original invoice
        si1.cancel()

        # At this point, it's canceled and unamended
        frappe.cache.delete_value("uph:health_counts")
        counts_before = get_health_counts()
        self.assertGreaterEqual(counts_before["cancelled_unamended_count"], 1)

        # Create a party issue for it
        issue = frappe.get_doc(
            {
                "doctype": "Party Issue",
                "party_master": self.party.name,
                "issue_type": "Transaction Policy",
                "reference_doctype": "Sales Invoice",
                "reference_name": si1.name,
                "severity": "High",
                "status": "Open",
                "source_engine": "test",
                "details_json": '{"issue": "cancelled_referenced"}',
            }
        ).insert(ignore_permissions=True)

        # Create an amended invoice
        si2 = frappe.copy_doc(si1)
        si2.docstatus = 0
        si2.amended_from = si1.name
        si2.insert(ignore_permissions=True)
        si2.reload()
        si2.submit()

        # The new logic should now see that si1 was amended
        frappe.cache.delete_value("uph:health_counts")
        counts_after = get_health_counts()
        self.assertLess(
            counts_after["cancelled_unamended_count"],
            counts_before["cancelled_unamended_count"],
        )

        # Sync should auto-resolve the issue
        sync_transaction_health_issues()
        issue.reload()
        self.assertEqual(issue.status, "Resolved")
