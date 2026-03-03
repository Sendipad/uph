import random
import string
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from uph.party.controllers.party import (
    get_party_type_validation_rule,
    is_valide_party_master_to_party,
    get_functional_document_types,
    get_doctypes_functional_fields_mapping_as_dict,
)
from uph.party.controllers.queries import party_master_link_query


from uph.tests.setup_mixin import AccountsTestMixin


def _unique_party_number(length=10):
    while True:
        value = "".join(random.choices(string.digits, k=length))
        if not frappe.db.exists("Party Master", value):
            return value


class TestPartyControllers(FrappeTestCase, AccountsTestMixin):
    def setUp(self):
        self.create_company()
        self.create_item()
        self.create_party_master()
        self.create_customer(party_master=self.party_master)

        # Ensure Sales Invoice is configured
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

    def test_get_party_type_validation_rule(self):
        result = get_party_type_validation_rule("Customer")
        self.assertIsNotNone(result)

    def test_is_valide_party_master_to_party(self):
        self.assertTrue(is_valide_party_master_to_party(self.party_master, "Customer"))

    def test_get_functional_document_types(self):
        result = get_functional_document_types()
        self.assertIsInstance(result, (list, type(None)))

    def test_get_doctypes_functional_fields_mapping(self):
        result = get_doctypes_functional_fields_mapping_as_dict()
        self.assertIsInstance(result, (dict, type(None)))

    def test_validate_party_master_on_document(self):
        # Create a Sales Invoice and test validation
        si = frappe.new_doc("Sales Invoice")
        si.company = self.company
        si.customer = self.customer
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
        # If party_master is not set but exists for customer, it might be fetched
        si.run_method("validate")
        self.assertEqual(si.party_master, self.party_master)

    def test_validate_party_master_on_target_party_type(self):
        from uph.party.controllers.party import (
            validate_party_master_on_target_party_type,
        )

        cust = frappe.get_doc("Customer", self.customer)
        # Test validate method
        validate_party_master_on_target_party_type(cust, "validate")

        # Test mandatory check
        settings = frappe.get_doc("Party Master Settings", "Party Master Settings")
        customer_pt = None
        for d in settings.party_types:
            if d.party_type == "Customer":
                customer_pt = d
                break

        if customer_pt:
            old_reqd = customer_pt.reqd
            try:
                customer_pt.reqd = 1
                settings.save(ignore_permissions=True)
                from uph.party.controllers.cache_utils import clear_all_caches

                clear_all_caches()
                frappe.clear_cache()

                cust_no_pm = frappe.get_doc("Customer", self.customer)
                cust_no_pm.party_master = None
                cust_no_pm.force_validate_party_master = True
                self.assertRaises(
                    frappe.ValidationError,
                    validate_party_master_on_target_party_type,
                    cust_no_pm,
                    "validate",
                )
            finally:
                customer_pt.reqd = old_reqd
                settings.save(ignore_permissions=True)
                clear_all_caches()
                frappe.clear_cache()

    def test_on_change_party_master_update_transactional_document_types(self):
        from uph.party.controllers.party import (
            on_change_party_master_update_transactional_document_types,
        )

        # Create a Sales Invoice linked to current customer and party_master
        si = frappe.new_doc("Sales Invoice")
        si.company = self.company
        si.customer = self.customer
        si.party_master = self.party_master
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
        si.insert()
        si_name = si.name

        # Create a second Party Master (unique to avoid collisions)
        existing_pm = frappe.get_doc("Party Master", self.party_master)
        parent_group = existing_pm.parent_party_master

        new_pm = frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": f"_Test New PM {frappe.generate_hash(length=6)}",
                "parent_party_master": parent_group,
                "is_group": 0,
                "party_type": "Customer",
                "type": "Individual",
            }
        )
        new_pm.party_number = _unique_party_number()
        new_pm.insert(ignore_permissions=True)
        new_pm_name = new_pm.name

        # Update customer's party master
        customer_doc = frappe.get_doc("Customer", self.customer)
        old_pm = customer_doc.party_master
        customer_doc.party_master = new_pm_name
        customer_doc.save()

        # Call the update function (normally handled by hooks)
        on_change_party_master_update_transactional_document_types(
            party=customer_doc, old_party_master=old_pm, counts_only=False
        )

        # Refresh SI and check party_master
        updated_si_pm = frappe.db.get_value("Sales Invoice", si_name, "party_master")
        self.assertEqual(updated_si_pm, new_pm_name)

    def test_on_change_party_master_does_not_commit_in_controller(self):
        from uph.party.controllers.party import (
            on_change_party_master_update_transactional_document_types,
        )

        si = frappe.new_doc("Sales Invoice")
        si.company = self.company
        si.customer = self.customer
        si.party_master = self.party_master
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
        si.insert()

        existing_pm = frappe.get_doc("Party Master", self.party_master)
        parent_group = existing_pm.parent_party_master
        new_pm = frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": f"_Test New PM {frappe.generate_hash(length=6)}",
                "parent_party_master": parent_group,
                "is_group": 0,
                "party_type": "Customer",
                "type": "Individual",
            }
        )
        new_pm.party_number = _unique_party_number()
        new_pm.insert(ignore_permissions=True)

        customer_doc = frappe.get_doc("Customer", self.customer)
        old_pm = customer_doc.party_master
        customer_doc.party_master = new_pm.name
        customer_doc.save()

        with patch.object(frappe.db, "commit") as mock_commit:
            on_change_party_master_update_transactional_document_types(
                party=customer_doc, old_party_master=old_pm, counts_only=False
            )
            mock_commit.assert_not_called()

    def test_check_duplicate_voucher_party_master(self):
        from uph.party.controllers.party import check_duplicate_voucher_party_master

        # This function checks if a voucher with same party_master and date exists
        # Create a Sales Invoice
        si = frappe.new_doc("Sales Invoice")
        si.company = self.company
        si.customer = self.customer
        si.party_master = self.party_master
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
        si.insert()
        si.submit()

        # check_duplicate should return True or raise error depending on implementation
        # Actually it returns a list of duplicates
        duplicates = check_duplicate_voucher_party_master(
            self.party_master, "Sales Invoice", si.posting_date, current_name=None
        )
        self.assertTrue(len(duplicates) > 0)

    def test_set_party_as_default_for_party_master(self):
        from uph.party.controllers.party import set_party_as_default_for_party_master

        set_party_as_default_for_party_master(
            self.customer, "Customer", self.party_master, 1
        )
        cust_doc = frappe.get_doc("Customer", self.customer)
        self.assertEqual(cust_doc.is_default_for_party_master, 1)
