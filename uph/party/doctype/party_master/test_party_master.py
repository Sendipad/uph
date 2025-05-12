# Copyright (c) 2024, Abdo Ruzaqi and Contributors
# See license.txt
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime
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
        cls.test_customer = frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": unique_party_name("Test Customer"),
                "default_currency": "USD",
                "party_master": "Ruzaqi",  # From initial records
            }
        ).insert(ignore_permissions=True)

    def setUp(self):
        """Create fresh test data for each test"""
        self.parent_party_master = create_party_master(
            party_name=unique_party_name("Parent PM"), is_group=1, party_type="Customer"
        )
        self.child_party_master = create_party_master(
            party_name=unique_party_name("Child PM"),
            is_group=0,
            party_type="Customer",
            parent_party_master=self.parent_party_master.name,
        )

    def tearDown(self):
        frappe.db.rollback()

    def test_duplicate_party_name_should_raise_error(self):
        """Test that duplicate party names are not allowed"""
        with self.assertRaises(frappe.DuplicateEntryError):
            create_party_master(
                party_name="Ruzaqi",  # From initial records
                is_group=0,
                party_type="Customer",
            )

    def test_party_number_should_start_with_parent_number(self):
        """Test child party numbering inherits parent numbering"""
        child = frappe.get_doc("Party Master", self.child_party_master.name)
        parent = frappe.get_doc("Party Master", child.parent_party_master)
        self.assertTrue(
            child.party_number.startswith(parent.party_number),
            "Child party number should start with parent's number",
        )

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
            "Party number should change after parent change",
        )
        self.assertTrue(
            self.child_party_master.party_number.startswith(new_parent.party_number),
            "New party number should start with new parent's number",
        )

    def test_parent_change_updates_existing_party_number_reference(self):
        """Test that changing parent updates references correctly"""
        existing = frappe.get_doc("Party Master", {"party_name": "Ruzaqi"})
        old_parent = frappe.get_doc("Party Master", existing.parent_party_master)

        new_parent = create_party_master(
            party_name=unique_party_name("Alt Parent"),
            is_group=1,
            parent_party_master="Debitor",
            party_type="Customer",
        )

        new_child = create_party_master(
            party_name=unique_party_name("Swappable Child"),
            is_group=0,
            parent_party_master=new_parent.name,
            party_type="Customer",
        )

        new_child.parent_party_master = old_parent.name
        new_child.save()

        self.assertTrue(new_child.party_number.startswith(old_parent.party_number))

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
            frappe.rename_doc("Party Master", "Ruzaqi", target_pm.name, merge=True)
