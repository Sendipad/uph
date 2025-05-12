# Copyright (c) 2024, Abdo Ruzaqi and Contributors
# See license.txt
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime

def unique_party_name(base="Test Party"):
    return f"{base} {now_datetime().strftime('%H%M%S%f')}"

class TestPartyMaster(FrappeTestCase):
    def setUp(self):
        """Create fresh test data for each test"""
        # Create parent Party Master
        self.parent_pm = frappe.get_doc({
            "doctype": "Party Master",
            "party_name": unique_party_name("Parent PM"),
            "party_type": "Customer",
            "is_group": 1
        }).insert(ignore_permissions=True)

        # Create child Party Master
        self.child_pm = frappe.get_doc({
            "doctype": "Party Master",
            "party_name": unique_party_name("Child PM"),
            "party_type": "Customer",
            "parent_party_master": self.parent_pm.name,
            "is_group": 0
        }).insert(ignore_permissions=True)

        # Create linked Customer
        self.customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": unique_party_name("Test Customer"),
            "party_master": self.child_pm.name
        }).insert(ignore_permissions=True)

    def test_party_master_creation(self):
        """Test basic Party Master creation"""
        self.assertEqual(self.parent_pm.party_type, "Customer")
        self.assertTrue(self.parent_pm.is_group)
        self.assertEqual(self.child_pm.parent_party_master, self.parent_pm.name)

    def test_customer_link(self):
        """Test Customer-Party Master relationship"""
        customer = frappe.get_doc("Customer", self.customer.name)
        self.assertEqual(customer.party_master, self.child_pm.name)
        
        # Verify party master exists
        self.assertTrue(frappe.db.exists("Party Master", customer.party_master))

    def test_party_hierarchy(self):
        """Test party number hierarchy"""
        parent = frappe.get_doc("Party Master", self.parent_pm.name)
        child = frappe.get_doc("Party Master", self.child_pm.name)
        
        self.assertTrue(child.party_number.startswith(parent.party_number),
            "Child party number should inherit parent's numbering")

    def test_parent_change(self):
        """Test changing parent updates hierarchy"""
        new_parent = frappe.get_doc({
            "doctype": "Party Master",
            "party_name": unique_party_name("New Parent"),
            "party_type": "Customer",
            "is_group": 1
        }).insert(ignore_permissions=True)

        old_number = self.child_pm.party_number
        self.child_pm.parent_party_master = new_parent.name
        self.child_pm.save()

        self.assertNotEqual(self.child_pm.party_number, old_number)
        self.assertTrue(self.child_pm.party_number.startswith(new_parent.party_number))

    def test_delete_protection(self):
        """Test linked Party Master cannot be deleted"""
        with self.assertRaises(frappe.LinkExistsError):
            frappe.delete_doc("Party Master", self.child_pm.name)

    def tearDown(self):
        """Cleanup (handled automatically by Frappe)"""
        pass
