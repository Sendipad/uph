import frappe
from uph.party.controllers.test.setup_mixin import AccountsTestMixin
from frappe.tests.utils import FrappeTestCase
from uph.party.doctype.party_master.party_master import create_party_from_party_master


class TestPartyController(AccountsTestMixin, FrappeTestCase):
    def setUp(self):
        self.create_company()

    def tearDown(self):
        frappe.db.rollback()

    def disable_reqd_party_master_for_party(self, party_type="Customer"):
        settings = frappe.get_doc("Party Master Settings")
        for p in settings.party_types:
            if p.party_type == party_type:
                p.reqd = 0
                break
        settings.save()

    def test_create_party_without_party_master(self):
        # Ensure Party Master is mandatory for Customer
        settings = frappe.get_doc("Party Master Settings")
        updated = False
        for p in settings.party_types:
            if p.party_type == "Customer" and not p.reqd:
                p.reqd = 1
                updated = True
                break
        if updated:
            settings.save()
            
        self.assertRaises(frappe.ValidationError, self.create_customer)

    def test_duplicate_linked_party_to_party_master(self):
        self.create_party_master()
        customer = create_party_from_party_master(
            self.party_master,
            target_doctype="Customer",
            target_doc=None,
            rule_field_value="USD",
        )
        customer.save()
        another_customer = create_party_from_party_master(
            self.party_master,
            target_doctype="Customer",
            target_doc=None,
            rule_field_value="USD",
        )
        self.assertRaises(frappe.ValidationError, another_customer.save())

    def test_party_master_to_party(self):
        self.create_party_master()
        customer = create_party_from_party_master(
            self.party_master,
            target_doctype="Customer",
            target_doc=None,
            rule_field_value="YER",
        )
        customer.save()
