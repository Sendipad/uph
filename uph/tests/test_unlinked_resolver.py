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

        # Clean up only OUR test records to ensure a fresh start
        frappe.db.delete(
            "Customer", {"customer_name": ["like", "_Test Unlinked Customer %"]}
        )
        frappe.db.delete("Party Master", {"party_name": ["like", "_Test PM %"]})
        frappe.db.commit()

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

    def _create_journal_entry(self, customer_name, amount=10):
        """Create a draft Journal Entry for the given customer."""
        je = frappe.new_doc("Journal Entry")
        je.company = self.company
        je.posting_date = frappe.utils.today()
        je.voucher_type = "Journal Entry"
        je.append(
            "accounts",
            {
                "account": self.debit_to,
                "party_type": "Customer",
                "party": customer_name,
                "debit_in_account_currency": amount,
                "debit": amount,
            },
        )
        je.append(
            "accounts",
            {
                "account": self.cash,
                "credit_in_account_currency": amount,
                "credit": amount,
            },
        )
        je.insert(ignore_permissions=True)
        return je

    def _create_payment_entry(self, customer_name, amount=10):
        """Create a draft Payment Entry for the given customer."""
        pe = frappe.new_doc("Payment Entry")
        pe.payment_type = "Receive"
        pe.company = self.company
        pe.party_type = "Customer"
        pe.party = customer_name
        pe.paid_from = self.debit_to
        pe.paid_to = self.cash
        pe.paid_amount = amount
        pe.received_amount = amount
        pe.source_exchange_rate = 1
        pe.target_exchange_rate = 1
        pe.posting_date = frappe.utils.today()
        pe.insert(ignore_permissions=True)
        return pe

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

    def test_link_customer_keeps_customer_name_and_updates_vouchers(self):
        """
        Ensure linking a Customer to a Party Master updates voucher party_master
        but does not alter existing Sales Invoice customer_name.
        """
        from uph.party.controllers.unlinked_resolver import link_to_party_master
        from uph.party.controllers.cache_utils import clear_all_caches

        settings = frappe.get_doc("Party Master Settings", "Party Master Settings")

        pt_row = next(
            (d for d in settings.party_types if d.party_type == "Customer"), None
        )
        added_pt = False
        if not pt_row:
            pt_row = settings.append(
                "party_types", {"party_type": "Customer", "reqd": 0, "allowed": 0}
            )
            added_pt = True
        old_pt_reqd = pt_row.reqd

        dt_row = next(
            (d for d in settings.document_types if d.document_type == "Sales Invoice"),
            None,
        )
        added_dt = False
        if not dt_row:
            dt_row = settings.append(
                "document_types",
                {
                    "document_type": "Sales Invoice",
                    "party_fieldname": "customer",
                    "party_type": "Customer",
                    "parent_doctype": "Sales Invoice",
                    "reqd": 0,
                },
            )
            added_dt = True
        old_dt_reqd = dt_row.reqd

        try:
            pt_row.reqd = 0
            dt_row.reqd = 0
            settings.save(ignore_permissions=True)
            clear_all_caches()

            customer = self._create_unlinked_customer()
            si = self._create_sales_invoice(customer.name)

            original_customer_name = frappe.db.get_value(
                "Sales Invoice", si.name, "customer_name"
            )

            pm = self._create_party_master_for_customer_role()
            result = link_to_party_master(
                role_doctype="Customer",
                role_name=customer.name,
                party_master=pm.name,
            )
            self.assertTrue(result.get("success"))

            updated_pm = frappe.db.get_value("Sales Invoice", si.name, "party_master")
            self.assertEqual(
                updated_pm,
                pm.name,
                f"Sales Invoice {si.name} party_master should be {pm.name}, got {updated_pm}",
            )

            updated_customer_name = frappe.db.get_value(
                "Sales Invoice", si.name, "customer_name"
            )
            self.assertEqual(
                updated_customer_name,
                original_customer_name,
                "Sales Invoice customer_name should remain unchanged after linking",
            )
        finally:
            settings = frappe.get_doc("Party Master Settings", "Party Master Settings")
            if added_dt:
                settings.document_types = [
                    d
                    for d in settings.document_types
                    if d.document_type != "Sales Invoice"
                ]
            else:
                for d in settings.document_types:
                    if d.document_type == "Sales Invoice":
                        d.reqd = old_dt_reqd
                        break

            if added_pt:
                settings.party_types = [
                    d for d in settings.party_types if d.party_type != "Customer"
                ]
            else:
                for d in settings.party_types:
                    if d.party_type == "Customer":
                        d.reqd = old_pt_reqd
                        break

            settings.save(ignore_permissions=True)
            clear_all_caches()

    def test_link_customer_updates_large_volume_vouchers(self):
        """
        Create a larger volume of vouchers (Journal Entry + Payment Entry)
        and ensure linking Customer updates party_master across them.
        """
        from uph.party.controllers.unlinked_resolver import link_to_party_master
        from uph.party.controllers.cache_utils import clear_all_caches
        from frappe.query_builder import DocType
        from frappe.query_builder.functions import Count

        settings = frappe.get_doc("Party Master Settings", "Party Master Settings")

        # Ensure Customer party type exists and is not required
        pt_row = next(
            (d for d in settings.party_types if d.party_type == "Customer"), None
        )
        added_pt = False
        if not pt_row:
            pt_row = settings.append(
                "party_types", {"party_type": "Customer", "reqd": 0, "allowed": 0}
            )
            added_pt = True
        old_pt_reqd = pt_row.reqd

        # Ensure Journal Entry Account mapping exists
        jea_row = next(
            (
                d
                for d in settings.document_types
                if d.document_type == "Journal Entry Account"
            ),
            None,
        )
        added_jea = False
        if not jea_row:
            jea_row = settings.append(
                "document_types",
                {
                    "document_type": "Journal Entry Account",
                    "parent_doctype": "Journal Entry",
                    "party_fieldname": "party",
                    "party_type_fieldname": "party_type",
                    "reqd": 0,
                },
            )
            added_jea = True
        old_jea_reqd = jea_row.reqd

        # Ensure Payment Entry mapping exists
        pe_row = next(
            (d for d in settings.document_types if d.document_type == "Payment Entry"),
            None,
        )
        added_pe = False
        if not pe_row:
            pe_row = settings.append(
                "document_types",
                {
                    "document_type": "Payment Entry",
                    "parent_doctype": "Payment Entry",
                    "party_fieldname": "party",
                    "party_type_fieldname": "party_type",
                    "reqd": 0,
                },
            )
            added_pe = True
        old_pe_reqd = pe_row.reqd

        old_sync_naming = settings.sync_erp_party_naming

        try:
            pt_row.reqd = 0
            jea_row.reqd = 0
            pe_row.reqd = 0
            settings.sync_erp_party_naming = 0
            settings.save(ignore_permissions=True)
            clear_all_caches()

            customer = self._create_unlinked_customer()

            for _ in range(100):
                self._create_journal_entry(customer.name, amount=10)

            for _ in range(10):
                self._create_payment_entry(customer.name, amount=10)

            jea = DocType("Journal Entry Account")
            pe = DocType("Payment Entry")

            jea_unlinked = (
                frappe.qb.from_(jea)
                .select(Count("*").as_("cnt"))
                .where(
                    (jea.party == customer.name)
                    & (jea.party_type == "Customer")
                    & ((jea.party_master.isnull()) | (jea.party_master == ""))
                )
                .run(as_dict=True)[0]["cnt"]
            )
            self.assertEqual(
                jea_unlinked,
                100,
                f"Expected 100 JE Account rows unlinked, got {jea_unlinked}",
            )

            pe_unlinked = (
                frappe.qb.from_(pe)
                .select(Count("*").as_("cnt"))
                .where(
                    (pe.party == customer.name)
                    & (pe.party_type == "Customer")
                    & ((pe.party_master.isnull()) | (pe.party_master == ""))
                )
                .run(as_dict=True)[0]["cnt"]
            )
            self.assertEqual(
                pe_unlinked,
                10,
                f"Expected 10 Payment Entries unlinked, got {pe_unlinked}",
            )

            pm = self._create_party_master_for_customer_role()
            result = link_to_party_master(
                role_doctype="Customer",
                role_name=customer.name,
                party_master=pm.name,
            )
            self.assertTrue(result.get("success"))

            jea_linked = (
                frappe.qb.from_(jea)
                .select(Count("*").as_("cnt"))
                .where(
                    (jea.party == customer.name)
                    & (jea.party_type == "Customer")
                    & (jea.party_master == pm.name)
                )
                .run(as_dict=True)[0]["cnt"]
            )
            self.assertEqual(
                jea_linked,
                100,
                f"Expected 100 JE Account rows linked, got {jea_linked}",
            )

            pe_linked = (
                frappe.qb.from_(pe)
                .select(Count("*").as_("cnt"))
                .where(
                    (pe.party == customer.name)
                    & (pe.party_type == "Customer")
                    & (pe.party_master == pm.name)
                )
                .run(as_dict=True)[0]["cnt"]
            )
            self.assertEqual(
                pe_linked,
                10,
                f"Expected 10 Payment Entries linked, got {pe_linked}",
            )
        finally:
            settings = frappe.get_doc("Party Master Settings", "Party Master Settings")

            if added_jea:
                settings.document_types = [
                    d
                    for d in settings.document_types
                    if d.document_type != "Journal Entry Account"
                ]
            else:
                for d in settings.document_types:
                    if d.document_type == "Journal Entry Account":
                        d.reqd = old_jea_reqd
                        break

            if added_pe:
                settings.document_types = [
                    d
                    for d in settings.document_types
                    if d.document_type != "Payment Entry"
                ]
            else:
                for d in settings.document_types:
                    if d.document_type == "Payment Entry":
                        d.reqd = old_pe_reqd
                        break

            if added_pt:
                settings.party_types = [
                    d for d in settings.party_types if d.party_type != "Customer"
                ]
            else:
                for d in settings.party_types:
                    if d.party_type == "Customer":
                        d.reqd = old_pt_reqd
                        break

            settings.sync_erp_party_naming = old_sync_naming
            settings.save(ignore_permissions=True)
            clear_all_caches()
