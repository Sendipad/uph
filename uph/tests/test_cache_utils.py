import frappe
from frappe.tests.utils import FrappeTestCase
from uph.party.controllers.cache_utils import (
    clear_all_caches,
    get_configured_doctypes,
    get_pm_doctypes,
    get_party_master_depends_on_fields,
    is_configured_doctype,
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
