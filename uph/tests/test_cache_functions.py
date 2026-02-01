import frappe
from frappe.tests.utils import FrappeTestCase
import uph
from uph.party.controllers.cache_utils import SmartCache, clear_all_caches


class TestCacheFunctions(FrappeTestCase):
    def setUp(self):
        clear_all_caches()

    def test_smart_cache_keys(self):
        # Test SmartCache key generation directly
        self.assertEqual(SmartCache.make_key("MySpace", "MyId"), "UPH:MySpace|MyId")

    def test_smart_cache_set_get(self):
        key = SmartCache.make_key("Test", "Value")

        # Should be None initially
        self.assertIsNone(SmartCache.get_cached_value(key))

        # Test generator
        def gen():
            return "generated_value"

        val = SmartCache.get_cached_value(key, generator=gen)
        self.assertEqual(val, "generated_value")

        # Should be cached now (check without generator)
        self.assertEqual(SmartCache.get_cached_value(key), "generated_value")

        # Delete
        SmartCache.delete_cached_value(key)
        self.assertIsNone(SmartCache.get_cached_value(key))

    def test_get_party_type_list(self):
        # Ensure it returns a list and has expected types
        result = SmartCache.get_party_type_list()
        self.assertIsInstance(result, list)
        if "Customer" in frappe.get_all("DocType", pluck="name"):
            self.assertIn("Customer", result)

    def test_l1_cache_layer(self):
        # Test that L1 cache works within request
        key = SmartCache.make_key("L1", "Test")

        frappe.local.uph_cache[key] = "l1_value"
        # Should return L1 value even if nothing in Redis
        self.assertEqual(SmartCache.get_cached_value(key), "l1_value")

        # Clear L1
        del frappe.local.uph_cache[key]
        self.assertIsNone(SmartCache.get_cached_value(key))

    def test_party_master_integration(self):
        # Create a dummy Party Master if not exists or use existing
        if not frappe.db.exists("Party Master", "Test PM Cache"):
            pm = frappe.get_doc(
                {
                    "doctype": "Party Master",
                    "party_name": "Test PM Cache",
                    "party_type": "Customer",
                }
            ).insert()
        else:
            pm = frappe.get_doc("Party Master", "Test PM Cache")

        # Test cache update
        SmartCache.update_party_master_parties(pm.name)

        # Verify key exists (though hard to verify internal redis state directly without mocking,
        # we can verify retrieval works)
        # We can mock the DB call to ensure it hits cache if we really wanted to,
        # but for integration tests, functional correctness is key.

        parties = SmartCache.get_party_master_parties(pm.name)
        self.assertIsInstance(parties, list)
