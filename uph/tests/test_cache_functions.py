import frappe
from frappe.tests.utils import FrappeTestCase
import uph

class TestCacheFunctions(FrappeTestCase):
    def test_make_key(self):
        self.assertEqual(uph.make_key("test"), "UPH:test")

    def test_get_cached_key_valid(self):
        self.assertEqual(uph.get_cached_key("parties"), "UPH_hash:PartyMaster|List_Parties")

    def test_get_cached_key_invalid_raises(self):
        with self.assertRaises(ValueError):
            uph.get_cached_key("invalid_key")

    def test_get_pm_parties_key(self):
        self.assertEqual(uph.get_pm_parties_key(), "PartyMaster|List_Parties")

    def test_get_party_to_pm_key(self):
        self.assertEqual(uph.get_party_to_pm_key("Customer"), "PartyToPartyMaster | Customer")

    def test_get_party_type_list(self):
        result = uph.get_party_type_list()
        self.assertIsInstance(result, list)
        self.assertIn("Customer", result)

    def test_get_cached_party_to_pm_map_none(self):
        result = uph.get_cached_party_to_pm_map("Customer", "NonExistent123")
        self.assertIsNone(result)
