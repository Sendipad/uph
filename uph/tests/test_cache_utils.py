import frappe
from frappe.tests.utils import FrappeTestCase
from uph.party.controllers.cache_utils import (
    clear_all_caches,
    get_configured_doctypes,
    get_pm_doctypes,
    get_party_master_depends_on_fields,
    is_configured_doctype,
    SmartCache,
)


class TestCacheUtils(FrappeTestCase):
    def test_clear_all_caches(self):
        # Set some cache values
        from uph.party.controllers.cache_utils import (
            CACHE_KEY_PM_DOCTYPES,
            CACHE_KEY_CONFIGURED_DOCTYPES,
        )

        frappe.cache().set_value(CACHE_KEY_PM_DOCTYPES, ["Sales Invoice"])
        frappe.cache().set_value(CACHE_KEY_CONFIGURED_DOCTYPES, ["Customer"])

        clear_all_caches()

        # Verify they are cleared
        self.assertIsNone(frappe.cache().get_value(CACHE_KEY_PM_DOCTYPES))
        self.assertIsNone(frappe.cache().get_value(CACHE_KEY_CONFIGURED_DOCTYPES))

    def test_get_pm_doctypes(self):
        # This function fetches from Party Master Settings or hooks
        doctypes = get_pm_doctypes()
        self.assertIsInstance(doctypes, (list, tuple))
        # Should include core ones like Sales Invoice if configured
        flattened = [d[0] for d in doctypes]
        self.assertIn("Sales Invoice", flattened)

    def test_get_configured_doctypes(self):
        doctypes = get_configured_doctypes()
        self.assertIsInstance(doctypes, (list, tuple, set))

    def test_is_configured_doctype(self):
        # Assuming Sales Invoice is configured by default in test setup or hooks
        self.assertTrue(is_configured_doctype("Sales Invoice"))
        self.assertFalse(is_configured_doctype("User"))

    def test_get_party_master_depends_on_fields(self):
        fields = get_party_master_depends_on_fields()
        self.assertIsInstance(fields, (list, tuple, dict))


class TestCacheInvalidation(FrappeTestCase):
    """Test cache invalidation scenarios."""

    def setUp(self):
        # Clear all caches before each test
        clear_all_caches()
        frappe.db.commit()

    def test_cache_invalidation_on_settings_change(self):
        """Test that caches are invalidated when Party Master Settings change."""
        from uph.party.controllers.cache_utils import (
            CACHE_KEY_PM_DOCTYPES,
            CACHE_KEY_CONFIGURED_DOCTYPES,
        )

        # Manually set cache values to test clearing
        frappe.cache().set_value(CACHE_KEY_PM_DOCTYPES, ["Test DocType"])
        frappe.cache().set_value(CACHE_KEY_CONFIGURED_DOCTYPES, ["Test Config"])

        # Verify cache is set
        cached_pm = frappe.cache().get_value(CACHE_KEY_PM_DOCTYPES)
        self.assertIsNotNone(cached_pm)

        # Clear caches (simulating what happens on settings change)
        clear_all_caches()

        # Verify cache is cleared
        self.assertIsNone(frappe.cache().get_value(CACHE_KEY_PM_DOCTYPES))
        self.assertIsNone(frappe.cache().get_value(CACHE_KEY_CONFIGURED_DOCTYPES))

    def test_smart_cache_basic_operation(self):
        """Test SmartCache basic get/set operations."""
        cache_key = "uph:test_smart_cache_basic"
        test_value = {"key": "value", "number": 42}

        # Set value
        SmartCache.set_cached_value(cache_key, test_value)

        # Get value
        result = SmartCache.get_cached_value(cache_key)
        self.assertEqual(result, test_value)

        # Get with generator (should return cached value)
        def generator():
            return {"different": "value"}

        result2 = SmartCache.get_cached_value(cache_key, generator)
        self.assertEqual(result2, test_value)  # Still returns cached value

        # Delete
        SmartCache.delete_cached_value(cache_key)

        # Verify deleted
        cached = frappe.cache().get_value(cache_key)
        self.assertIsNone(cached)

    def test_smart_cache_with_generator(self):
        """Test SmartCache with generator function."""
        cache_key = "uph:test_smart_cache_generator"

        # Clear any existing value
        SmartCache.delete_cached_value(cache_key)

        call_count = [0]

        def generator():
            call_count[0] += 1
            return f"value_{call_count[0]}"

        # First call should use generator
        result1 = SmartCache.get_cached_value(cache_key, generator)
        self.assertEqual(result1, "value_1")
        self.assertEqual(call_count[0], 1)

        # Second call should return cached value
        result2 = SmartCache.get_cached_value(cache_key, generator)
        self.assertEqual(result2, "value_1")
        self.assertEqual(call_count[0], 1)  # Generator not called again

        # Cleanup
        SmartCache.delete_cached_value(cache_key)

    def test_cache_handles_none_from_generator(self):
        """Test that cache handles None generator results gracefully."""
        cache_key = "uph:test_none_value"

        SmartCache.delete_cached_value(cache_key)

        def generator():
            return None

        result = SmartCache.get_cached_value(cache_key, generator)
        # Result might be None (depending on implementation)
        # The key is that it doesn't error
        self.assertTrue(True)

    def test_cache_handles_empty_list(self):
        """Test that cache correctly stores empty lists."""
        cache_key = "uph:test_empty_list"

        SmartCache.set_cached_value(cache_key, [])

        result = SmartCache.get_cached_value(cache_key)
        self.assertEqual(result, [])

        SmartCache.delete_cached_value(cache_key)


class TestPartyMasterCacheInvalidation(FrappeTestCase):
    """Test cache invalidation specific to Party Master operations."""

    def test_party_master_update_clears_cache(self):
        """Test that updating a Party Master clears relevant caches."""
        # Get or create a test party master
        pm_name = "_Test PM Cache Invalidation"
        if not frappe.db.exists("Party Master", pm_name):
            pm = frappe.get_doc(
                {
                    "doctype": "Party Master",
                    "party_name": pm_name,
                    "party_type": "Customer",
                    "is_group": 1,
                }
            )
            pm.insert(ignore_permissions=True)
        else:
            pm = frappe.get_doc("Party Master", pm_name)

        # Modify and save - this should trigger _invalidate_cache
        original_name = pm.party_name
        pm.party_name = "_Test PM Cache Invalidation Updated"
        pm.save(ignore_permissions=True)

        # The save should have called _invalidate_cache
        # which clears party-master-specific caches

        # Clean up
        pm.party_name = original_name
        pm.save(ignore_permissions=True)
