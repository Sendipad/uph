import frappe
from frappe.tests.utils import FrappeTestCase
from uph.controllers.party import get_party_type_validation_rule, is_valide_party_master_to_party, get_functional_document_types, get_doctypes_functional_fields_mapping_as_dict

class TestPartyControllers(FrappeTestCase):
    def test_get_party_type_validation_rule(self):
        result = get_party_type_validation_rule("Customer")
        self.assertIsNotNone(result)

    def test_is_valide_party_master_to_party(self):
        pm = frappe.get_all("Party Master", filters={"is_group": 0, "party_type": "Customer"}, limit=1, pluck="name")
        if pm:
            self.assertTrue(is_valide_party_master_to_party(pm[0], "Customer"))

    def test_get_functional_document_types(self):
        result = get_functional_document_types()
        self.assertIsInstance(result, (list, type(None)))

    def test_get_doctypes_functional_fields_mapping(self):
        result = get_doctypes_functional_fields_mapping_as_dict()
        self.assertIsInstance(result, (dict, type(None)))
