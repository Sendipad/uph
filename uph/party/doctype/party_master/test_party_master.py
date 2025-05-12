# Copyright (c) 2024, Abdo Ruzaqi and Contributors
# See license.txt
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime
from uph.party.controllers.test.test_create_pm_records import (
    create_initial_records,
    create_party_master,
)

# Please Check test in /uph/party/controllers/test for All test methods


def unique_party_name(base="Test Party"):
    return f"{base} {now_datetime().strftime('%H%M%S%f')}"


class TestPartyMaster(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_initial_records()

    def setUp(self):
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
        parent = frappe.get_doc("Party Master", {"party_name": "Debitor"})
        with self.assertRaises(frappe.UniqueValidationError):
            create_party_master(
                party_name="Debitor",  # Same name triggers unique constraint
                is_group=1,
                parent_party_master=parent.name,
                party_type="Customer",
            )

    def test_party_number_should_start_with_parent_number(self):
        child = frappe.get_doc("Party Master", self.child_party_master.name)
        parent = frappe.get_doc("Party Master", child.parent_party_master)
        self.assertTrue(child.party_number.startswith(parent.party_number))

    def test_party_number_changes_when_parent_changes(self):
        new_parent = create_party_master(
            party_name=unique_party_name("New Parent"),
            is_group=1,
            party_type="Customer",
        )

        old_number = self.child_party_master.party_number
        self.child_party_master.parent_party_master = new_parent.name
        self.child_party_master.save()

        self.assertNotEqual(self.child_party_master.party_number, old_number)
        self.assertTrue(
            self.child_party_master.party_number.startswith(new_parent.party_number)
        )

    def test_parent_change_updates_existing_party_number_reference(self):
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

    def test_rename_party_master_with_merge_should_fail_if_linked(self):
        # Create another Party Master to be target of merge
        target_pm = create_party_master(
            party_name=unique_party_name("Target PM"),
            is_group=0,
            party_type="Customer",
            parent_party_master=self.parent_party_master.name,
        )

        # Link current child PM to a Customer
        frappe.get_doc(
            {
                "doctype": "Customer",
                "default_currency": "USD",
                "customer_name": unique_party_name("Customer"),
                "party_master": self.child_party_master.name,
            }
        ).insert(ignore_links=True)

        # Attempt to rename with merge=True → should fail
        with self.assertRaises(frappe.ValidationError):
            frappe.rename_doc(
                doctype="Party Master",
                old=self.child_party_master.name,
                new=target_pm.name,
                merge=True,
                force=True,  # usually needed in tests
            )

    def test_delete_party_master_fails_if_linked_to_customer(self):
        frappe.get_doc(
            {
                "doctype": "Customer",
                "default_currency": "USD",
                "customer_name": unique_party_name("Delete Test Customer"),
                "party_master": self.child_party_master.name,
            }
        ).insert(ignore_links=True) 

        with self.assertRaises(frappe.LinkExistsError):
            frappe.delete_doc("Party Master", self.child_party_master.name)
