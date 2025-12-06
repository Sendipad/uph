import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime

def unique_name(base="Test"):
    return f"{base}_{now_datetime().strftime('%H%M%S%f')}"

class TestPartyMaster(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.root_group = frappe.get_all("Party Master", filters={"is_group": 1, "parent_party_master": ["is", "not set"]}, limit=1, pluck="name")
        cls.root_group = cls.root_group[0] if cls.root_group else None

    def test_create_party_master(self):
        if not self.root_group: self.skipTest("No root group")
        pm = frappe.get_doc({"doctype": "Party Master", "party_name": unique_name("Test PM"), "party_type": "Customer", "parent_party_master": self.root_group, "is_group": 0})
        pm.insert(ignore_permissions=True)
        self.assertTrue(frappe.db.exists("Party Master", pm.name))
        self.assertIsNotNone(pm.party_number)

    def test_duplicate_party_name_throws(self):
        if not self.root_group: self.skipTest("No root group")
        name = unique_name("Dup Test")
        frappe.get_doc({"doctype": "Party Master", "party_name": name, "party_type": "Customer", "parent_party_master": self.root_group}).insert(ignore_permissions=True)
        with self.assertRaises(frappe.exceptions.ValidationError):
            frappe.get_doc({"doctype": "Party Master", "party_name": name, "party_type": "Supplier", "parent_party_master": self.root_group}).insert(ignore_permissions=True)

    def test_disputed_status_requires_reason(self):
        if not self.root_group: self.skipTest("No root group")
        pm = frappe.get_doc({"doctype": "Party Master", "party_name": unique_name("Disputed"), "party_type": "Customer", "parent_party_master": self.root_group, "status": "Disputed"})
        with self.assertRaises(frappe.exceptions.ValidationError):
            pm.insert(ignore_permissions=True)

    def test_validate_roles_no_duplicate(self):
        if not self.root_group: self.skipTest("No root group")
        pm = frappe.get_doc({"doctype": "Party Master", "party_name": unique_name("Role"), "party_type": "Customer", "parent_party_master": self.root_group, "has_secondary_role_party": 1, "roles": [{"party_type_role": "Supplier"}, {"party_type_role": "Supplier"}]})
        pm.insert(ignore_permissions=True)
        self.assertEqual(len(pm.roles), 1)

    def test_normalized_party_name(self):
        if not self.root_group: self.skipTest("No root group")
        pm = frappe.get_doc({"doctype": "Party Master", "party_name": "  Test Normalize  ", "party_type": "Customer", "parent_party_master": self.root_group})
        pm.insert(ignore_permissions=True)
        self.assertIsNotNone(pm.normalized_party_name)
