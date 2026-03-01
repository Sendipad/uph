# Copyright (c) 2026, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

"""
Tests for the unlinked resolver module.

Verifies that linking/creating Party Masters from unlinked role records
correctly updates the party_master field on existing transactional vouchers.
"""

import random
import string

import frappe
from frappe.tests.utils import FrappeTestCase
from uph.tests.setup_mixin import AccountsTestMixin


def _unique_party_number(length=10):
    return "".join(random.choices(string.digits, k=length))


class TestUnlinkedResolver(FrappeTestCase, AccountsTestMixin):
    def setUp(self):
        self.create_company()
        self.create_item()

        # Ensure Sales Invoice is configured in Party Master Settings
        settings = frappe.get_doc("Party Master Settings", "Party Master Settings")
        if not any(d.document_type == "Sales Invoice" for d in settings.document_types):
            settings.append(
                "document_types",
                {
                    "document_type": "Sales Invoice",
                    "party_fieldname": "customer",
                    "party_type": "Customer",
                    "parent_doctype": "Sales Invoice",
                },
            )
            settings.save()
            from uph.party.controllers.cache_utils import clear_all_caches

            clear_all_caches()

        # Remove DB delete calls here to avoid breaking other tests

    def _create_unlinked_customer(self):
        """Create a Customer WITHOUT a party_master (unlinked)."""
        suffix = "".join(random.choices(string.ascii_lowercase, k=6))
        customer_name = f"_Test Unlinked Customer {suffix}"
        customer = frappe.new_doc("Customer")
        customer.customer_name = customer_name
        customer.type = "Individual"
        # Explicitly no party_master
        customer.flags.ignore_validate = True
        customer.save()
        return customer

    def _create_sales_invoice(self, customer_name):
        """Create a draft Sales Invoice for the given customer with no party_master."""
        si = frappe.new_doc("Sales Invoice")
        si.company = self.company
        si.customer = customer_name
        si.debit_to = self.debit_to
        si.currency = self.currency
        si.posting_date = frappe.utils.today()
        si.due_date = frappe.utils.today()
        si.conversion_rate = 1
        si.plc_conversion_rate = 1
        si.append(
            "items",
            {
                "item_code": "_Test Item",
                "qty": 1,
                "rate": 100,
                "income_account": self.income_account,
                "cost_center": self.cost_center,
            },
        )
        try:
            frappe.flags.in_patch = True
            si.insert(ignore_permissions=True)
        finally:
            frappe.flags.in_patch = False
        return si

    def _create_party_master_for_customer_role(self):
        """Create a Party Master suitable for linking a Customer."""
        root_name = frappe.db.exists(
            "Party Master",
            {"is_group": 1, "parent_party_master": ["is", "not set"]},
        )
        if not root_name:
            root = frappe.get_doc(
                {
                    "doctype": "Party Master",
                    "party_name": "Root Group",
                    "is_group": 1,
                    "party_type": "Customer",
                }
            ).insert(ignore_permissions=True)
            root_name = root.name

        pm = frappe.new_doc("Party Master")
        pm.party_name = f"_Test PM {_unique_party_number(6)}"
        pm.parent_party_master = root_name
        pm.party_type = "Customer"
        pm.type = "Individual"
        pm.party_number = _unique_party_number()
        pm.insert(ignore_permissions=True)
        return pm

    def test_link_to_party_master_updates_vouchers(self):
        """
        When linking an unlinked Customer to a Party Master via link_to_party_master,
        existing Sales Invoices for that Customer should get party_master updated.
        """
        from uph.party.controllers.unlinked_resolver import link_to_party_master

        # 1. Create an unlinked customer
        customer = self._create_unlinked_customer()

        # 2. Create a Sales Invoice for this customer (party_master should be NULL)
        si = self._create_sales_invoice(customer.name)
        si_pm = frappe.db.get_value("Sales Invoice", si.name, "party_master")
        self.assertFalse(si_pm, "SI should start with no party_master")

        # 3. Create a Party Master
        pm = self._create_party_master_for_customer_role()

        # 4. Link the customer to the party master
        result = link_to_party_master(
            role_doctype="Customer",
            role_name=customer.name,
            party_master=pm.name,
        )
        self.assertTrue(result.get("success"))

        # 5. Verify the Sales Invoice's party_master was updated
        updated_pm = frappe.db.get_value("Sales Invoice", si.name, "party_master")
        self.assertEqual(
            updated_pm,
            pm.name,
            f"Sales Invoice {si.name} party_master should be {pm.name}, got {updated_pm}",
        )

    def test_create_party_master_from_unlinked_role_updates_vouchers(self):
        """
        When creating a new Party Master from an unlinked Customer via
        create_party_master_from_unlinked_role, existing Sales Invoices
        should get party_master updated.
        """
        from uph.party.controllers.unlinked_resolver import (
            create_party_master_from_unlinked_role,
        )

        # 1. Create an unlinked customer
        customer = self._create_unlinked_customer()

        # 2. Create a Sales Invoice for this customer (party_master should be NULL)
        si = self._create_sales_invoice(customer.name)
        si_pm = frappe.db.get_value("Sales Invoice", si.name, "party_master")
        self.assertFalse(si_pm, "SI should start with no party_master")

        # 3. Ensure a root group exists for the function to find a parent
        root_name = frappe.db.exists(
            "Party Master",
            {"is_group": 1, "parent_party_master": ["is", "not set"]},
        )
        if not root_name:
            frappe.get_doc(
                {
                    "doctype": "Party Master",
                    "party_name": "Root Group",
                    "is_group": 1,
                    "party_type": "Customer",
                }
            ).insert(ignore_permissions=True)

        # 4. Create PM from unlinked role
        result = create_party_master_from_unlinked_role(
            role_doctype="Customer",
            role_name=customer.name,
        )
        self.assertTrue(result.get("success"))
        new_pm = result.get("party_master")
        self.assertTrue(new_pm)

        # 5. Verify the Customer is linked
        customer_pm = frappe.db.get_value("Customer", customer.name, "party_master")
        self.assertEqual(customer_pm, new_pm)

        # 6. Verify the Sales Invoice's party_master was updated
        updated_pm = frappe.db.get_value("Sales Invoice", si.name, "party_master")
        self.assertEqual(
            updated_pm,
            new_pm,
            f"Sales Invoice {si.name} party_master should be {new_pm}, got {updated_pm}",
        )
