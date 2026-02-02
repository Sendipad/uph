import frappe
from frappe.tests.utils import FrappeTestCase
from uph.party.controllers.party import (
    check_duplicate_voucher_party_master,
    allow_duplicate_submission,
)
from uph.tests.setup_mixin import AccountsTestMixin


class TestDuplicateBypass(FrappeTestCase, AccountsTestMixin):
    def setUp(self):
        super().setUp()
        self.create_company()
        self.create_customer()
        self.create_item()

        # Cleanup
        frappe.db.delete(
            "Sales Invoice", {"company": self.company, "customer": self.customer}
        )
        frappe.db.delete("Party Master", {"party_name": "Bypass Test PM"})

        self.settings = frappe.get_doc("Party Master Settings")
        self.settings.check_party_master_duplicate_vouchers = 1
        self.settings.duplicate_voucher_action = "Warn"
        self.settings.role_to_bypass_duplicate_voucher = None
        self.settings.save()

        # Create a Party Master
        self.pm = frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": "Bypass Test PM",
                "party_type": "Customer",
                "default_customer": self.customer,
            }
        ).insert()

        # Link Customer to PM and set currency to avoid exchange rate errors
        frappe.db.set_value(
            "Customer",
            self.customer,
            {"party_master": self.pm.name, "default_currency": self.currency},
        )

        # Create a Sales Invoice
        self.si = frappe.get_doc(
            {
                "doctype": "Sales Invoice",
                "company": self.company,
                "customer": self.customer,
                "party_master": self.pm.name,
                "posting_date": "2025-01-01",
                "currency": self.currency,
                "update_stock": 0,
                "items": [
                    {
                        "item_code": self.item,
                        "qty": 1,
                        "rate": 100,
                        "income_account": self.income_account,
                        "cost_center": self.cost_center,
                    }
                ],
            }
        ).insert()

        frappe.db.commit()
        # Refresh SI to get actual posting date (might have been overridden to today)
        self.si.reload()

    def test_duplicate_check_disabled(self):
        self.settings.check_party_master_duplicate_vouchers = 0
        self.settings.save()

        res = check_duplicate_voucher_party_master(
            self.pm.name, "Sales Invoice", self.si.posting_date
        )
        self.assertEqual(len(res["duplicates"]), 0)

    def test_duplicate_check_enabled_warn(self):
        self.settings.check_party_master_duplicate_vouchers = 1
        self.settings.duplicate_voucher_action = "Warn"
        self.settings.save()

        res = check_duplicate_voucher_party_master(
            self.pm.name, "Sales Invoice", self.si.posting_date, current_name="New SI"
        )
        self.assertEqual(len(res["duplicates"]), 1)
        self.assertEqual(res["settings"]["action"], "Warn")
        self.assertEqual(res["settings"]["has_bypass"], False)  # No role set

    def test_duplicate_check_stop_no_bypass(self):
        self.settings.check_party_master_duplicate_vouchers = 1
        self.settings.duplicate_voucher_action = "Stop"
        self.settings.role_to_bypass_duplicate_voucher = "Non-Existent Role"
        self.settings.flags.ignore_links = True
        self.settings.save()

        res = check_duplicate_voucher_party_master(
            self.pm.name, "Sales Invoice", self.si.posting_date, current_name="New SI"
        )
        self.assertEqual(res["settings"]["action"], "Stop")
        self.assertEqual(res["settings"]["has_bypass"], False)

    def test_duplicate_check_stop_with_bypass(self):
        self.settings.check_party_master_duplicate_vouchers = 1
        self.settings.duplicate_voucher_action = "Stop"
        self.settings.role_to_bypass_duplicate_voucher = "System Manager"
        self.settings.save()

        # Test user usually has System Manager
        res = check_duplicate_voucher_party_master(
            self.pm.name, "Sales Invoice", self.si.posting_date, current_name="New SI"
        )
        self.assertEqual(res["settings"]["action"], "Stop")
        self.assertEqual(res["settings"]["has_bypass"], True)
