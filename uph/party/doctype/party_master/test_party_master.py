# Copyright (c) 2024, Abdo Ruzaqi and Contributors
# See license.txt
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime, random_string
from uph.party.controllers.test.test_create_pm_records import (
    create_initial_records,
    create_party_master,
)

def unique_party_name(base="Test Party"):
    """Generate a unique party name for testing"""
    return f"{base} {now_datetime().strftime('%H%M%S%f')}"

class TestPartyMaster(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        """Create initial test data once for all tests"""
        super().setUpClass()
        create_initial_records()
        cls.setup_test_customers()

    @classmethod
    def setup_test_customers(cls):
        """Create test customers linked to party masters"""
        cls.test_customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": unique_party_name("Test Customer"),
            "default_currency": "USD",
            "party_master": "Ruzaqi"  # From initial records
        }).insert(ignore_permissions=True)

    def setUp(self):
        """Create fresh test data for each test"""
        self.parent_party_master = create_party_master(
            party_name=unique_party_name("Parent PM"), 
            is_group=1, 
            party_type="Customer"
        )
        self.child_party_master = create_party_master(
            party_name=unique_party_name("Child PM"),
            is_group=0,
            party_type="Customer",
            parent_party_master=self.parent_party_master.name,
        )

    def tearDown(self):
        frappe.db.rollback()

    # Test Case 1: Validation Tests
    def test_duplicate_party_name_should_raise_error(self):
        """Test that duplicate party names are not allowed"""
        with self.assertRaises(frappe.DuplicateEntryError):
            create_party_master(
                party_name="Ruzaqi",  # From initial records
                is_group=0,
                party_type="Customer",
            )

    def test_invalid_party_type_should_raise_error(self):
        """Test that invalid party types are rejected"""
        with self.assertRaises(frappe.ValidationError):
            create_party_master(
                party_name=unique_party_name("Invalid Type"),
                is_group=0,
                party_type="InvalidType",  # Not a valid party type
            )

    # Test Case 2: Numbering Tests
    def test_party_number_should_start_with_parent_number(self):
        """Test child party numbering inherits parent numbering"""
        child = frappe.get_doc("Party Master", self.child_party_master.name)
        parent = frappe.get_doc("Party Master", child.parent_party_master)
        self.assertTrue(child.party_number.startswith(parent.party_number),
            "Child party number should start with parent's number"

    def test_party_number_changes_when_parent_changes(self):
        """Test that changing parent updates the party number"""
        new_parent = create_party_master(
            party_name=unique_party_name("New Parent"),
            is_group=1,
            party_type="Customer",
        )

        old_number = self.child_party_master.party_number
        self.child_party_master.parent_party_master = new_parent.name
        self.child_party_master.save()

        self.assertNotEqual(
            self.child_party_master.party_number, 
            old_number,
            "Party number should change after parent change"
        )
        self.assertTrue(
            self.child_party_master.party_number.startswith(new_parent.party_number),
            "New party number should start with new parent's number"
        )

    # Test Case 3: Hierarchy Tests
    def test_cannot_set_child_as_parent(self):
        """Test circular reference prevention"""
        grandchild = create_party_master(
            party_name=unique_party_name("Grandchild"),
            is_group=0,
            party_type="Customer",
            parent_party_master=self.child_party_master.name,
        )

        with self.assertRaises(frappe.ValidationError):
            self.parent_party_master.parent_party_master = grandchild.name
            self.parent_party_master.save()

    def test_cannot_set_non_group_as_parent(self):
        """Test that only group-type parties can be parents"""
        non_group = create_party_master(
            party_name=unique_party_name("Non-Group"),
            is_group=0,
            party_type="Customer",
        )

        with self.assertRaises(frappe.ValidationError):
            create_party_master(
                party_name=unique_party_name("Invalid Child"),
                is_group=0,
                party_type="Customer",
                parent_party_master=non_group.name,
            )

    # Test Case 4: Link Protection Tests
    def test_delete_party_master_fails_if_linked_to_customer(self):
        """Test that linked Party Masters cannot be deleted"""
        with self.assertRaises(frappe.LinkExistsError):
            frappe.delete_doc("Party Master", "Ruzaqi")  # Linked in setUpClass

    def test_rename_party_master_with_merge_fails_if_linked(self):
        """Test that linked Party Masters cannot be merged"""
        target_pm = create_party_master(
            party_name=unique_party_name("Target PM"),
            is_group=0,
            party_type="Customer",
        )

        with self.assertRaises(frappe.LinkExistsError):
            frappe.rename_doc(
                "Party Master",
                "Ruzaqi",
                target_pm.name,
                merge=True
            )

    # Test Case 5: API Tests
    def test_get_party_master_options(self):
        """Test API for getting party master options"""
        from uph.party.doctype.party_master.party_master import get_party_master_options
        
        options = get_party_master_options("Customer")
        self.assertIn("Ruzaqi", options,
            "Initial test record should be in options")
        self.assertIn(self.child_party_master.name, options,
            "Newly created party should be in options")

    # Test Case 6: Bulk Operations
    def test_bulk_party_creation(self):
        """Test creation of multiple parties in hierarchy"""
        names = [unique_party_name(f"Bulk {i}") for i in range(5)]
        
        # Create hierarchy
        top = create_party_master(
            party_name=names[0],
            is_group=1,
            party_type="Customer"
        )
        
        mid = create_party_master(
            party_name=names[1],
            is_group=1,
            party_type="Customer",
            parent_party_master=top.name
        )
        
        leaves = [
            create_party_master(
                party_name=name,
                is_group=0,
                party_type="Customer",
                parent_party_master=mid.name
            )
            for name in names[2:]
        ]
        
        # Verify numbering hierarchy
        for leaf in leaves:
            doc = frappe.get_doc("Party Master", leaf.name)
            self.assertTrue(doc.party_number.startswith(mid.party_number))
            self.assertTrue(mid.party_number.startswith(top.party_number))