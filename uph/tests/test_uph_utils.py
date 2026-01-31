import frappe
from frappe.tests.utils import FrappeTestCase
from uph.party.utils import (
    get_mapped_fieldnames,
    get_party_type_currency_field,
    get_party_type_name_field,
    get_transactional_doctype_list_to_add_pm,
    get_party_field_in_doctype,
    get_party_type_from_doctype,
    normalize_text,
)


class TestUphUtils(FrappeTestCase):
    def test_get_mapped_fieldnames(self):
        res = get_mapped_fieldnames("Sales Invoice")
        self.assertEqual(res.party_fieldname, "customer")
        self.assertEqual(res.party_type, "Customer")

    def test_get_party_type_currency_field(self):
        self.assertEqual(get_party_type_currency_field("Customer"), "default_currency")
        self.assertEqual(get_party_type_currency_field("Employee"), "salary_currency")

    def test_get_party_type_name_field(self):
        self.assertEqual(get_party_type_name_field("Customer"), "customer_name")
        self.assertEqual(get_party_type_name_field("Supplier"), "supplier_name")

    def test_get_transactional_doctype_list(self):
        dt_list = get_transactional_doctype_list_to_add_pm()
        self.assertIn("Sales Invoice", dt_list)
        self.assertIn("Payment Entry", dt_list)

    def test_get_party_field_in_doctype(self):
        self.assertEqual(get_party_field_in_doctype("Sales Invoice"), "customer")
        self.assertEqual(get_party_field_in_doctype("Payment Entry"), "party")

    def test_get_party_type_from_doctype(self):
        self.assertEqual(get_party_type_from_doctype("Sales Invoice"), "Customer")
        self.assertEqual(get_party_type_from_doctype("Purchase Order"), "Supplier")

    def test_normalize_text(self):
        # Test Arabic normalization
        self.assertEqual(normalize_text("أحمد"), "احمد")
        self.assertEqual(normalize_text("محرّشة"), "محرشه")
        # Test Persian
        self.assertEqual(normalize_text("كتاب"), "کتاب")
        # Test Latin accents
        self.assertEqual(normalize_text("Café"), "cafe")
