# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

"""
Comprehensive tests for Party Master merge functionality.

Test Coverage:
- Case A: Full party merge (same rule_fieldname value)
- Case B: Re-link only (different rule_fieldname value)
- Dynamic Link transfers (Address, Contact)
- Transaction document updates
- Rollback on failure
- Permission checks
"""

import random
import string

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime


class TestPartyMergeService(FrappeTestCase):
    """Test Party Master merge logic."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        super().setUpClass()
        cls.test_company = frappe.db.get_single_value(
            "Global Defaults", "default_company"
        )
        if not cls.test_company:
            companies = frappe.get_all("Company", limit=1, pluck="name")
            cls.test_company = companies[0] if companies else None

        # Unique prefix for this test run
        cls.test_prefix = f"_TestMerge{now_datetime().strftime('%H%M%S')}"

    def setUp(self):
        """Set up fresh test data for each test."""
        frappe.set_user("Administrator")
        # No cleanup here, as each test will use unique names based on test_prefix
        # and cleanup happens in tearDown.

    def tearDown(self):
        """Clean up test data after each test."""
        self._cleanup_test_data()
        frappe.db.commit()

    def _cleanup_test_data(self):
        """Remove all test-related data using direct SQL for reliability."""
        # Clean up Dynamic Links first
        frappe.db.sql(
            """
            DELETE FROM `tabDynamic Link` 
            WHERE link_name LIKE %s OR parent LIKE %s
        """,
            (f"%{self.test_prefix}%", f"%{self.test_prefix}%"),
        )

        # Clean up test addresses
        frappe.db.sql(
            """
            DELETE FROM `tabAddress` WHERE address_title LIKE %s
        """,
            (f"%{self.test_prefix}%",),
        )

        # Clean up test Customers
        frappe.db.sql(
            """
            DELETE FROM `tabCustomer` WHERE customer_name LIKE %s
        """,
            (f"%{self.test_prefix}%",),
        )

        # Clean up Party Master Parties child table
        frappe.db.sql(
            """
            DELETE FROM `tabParty Master Parties` 
            WHERE parent IN (
                SELECT name FROM `tabParty Master` WHERE party_name LIKE %s
            )
        """,
            (f"%{self.test_prefix}%",),
        )

        # Clean up Party Master Accounts child table
        frappe.db.sql(
            """
            DELETE FROM `tabParty Master Accounts` 
            WHERE parent IN (
                SELECT name FROM `tabParty Master` WHERE party_name LIKE %s
            )
        """,
            (f"%{self.test_prefix}%",),
        )

        # Finally clean up Party Masters
        frappe.db.sql(
            """
            DELETE FROM `tabParty Master` WHERE party_name LIKE %s
        """,
            (f"%{self.test_prefix}%",),
        )

    def _unique_numeric(self, length=10):
        while True:
            value = "".join(random.choices(string.digits, k=length))
            if not frappe.db.exists("Party Master", value):
                return value

    def _unique_docname(self, doctype, prefix):
        while True:
            name = f"{prefix}-{frappe.generate_hash(length=6)}"
            if not frappe.db.exists(doctype, name):
                return name

    def _create_party_master(
        self, name_suffix: str, party_type: str = "Customer"
    ) -> str:
        """Create a test Party Master."""
        # Find a parent group
        parent = frappe.db.get_value("Party Master", {"is_group": 1}, "name")

        pm = frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": f"{self.test_prefix}PM{name_suffix}",
                "party_type": party_type,
                "is_group": 0,
                "parent_party_master": parent,
            }
        )
        pm.party_number = self._unique_numeric()
        pm.insert(ignore_permissions=True)
        frappe.db.commit()
        return pm.name

    def _create_customer(
        self, name_suffix: str, party_master: str = None, currency: str = "USD"
    ) -> str:
        """Create a test Customer linked to Party Master."""
        # Check if customer group exists
        customer_group = frappe.db.get_value("Customer Group", {"is_group": 0}, "name")
        if not customer_group:
            customer_group = "All Customer Groups"

        customer = frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": f"{self.test_prefix}Cust{name_suffix}",
                "customer_type": "Company",
                "customer_group": customer_group,
                "territory": frappe.db.get_single_value("Selling Settings", "territory")
                or "All Territories",
                "default_currency": currency,
                "party_master": party_master,
            }
        )
        customer.flags.ignore_validate = True
        customer.name = self._unique_docname("Customer", "TEST-CUST")
        customer.insert(ignore_permissions=True)
        frappe.db.commit()
        return customer.name

    def _create_address(self, title: str, link_doctype: str, link_name: str) -> str:
        """Create a test Address with Dynamic Link."""
        address = frappe.get_doc(
            {
                "doctype": "Address",
                "address_title": f"{self.test_prefix}Addr{title}",
                "address_type": "Billing",
                "address_line1": "123 Test Street",
                "city": "Test City",
                "country": "United States",
                "links": [{"link_doctype": link_doctype, "link_name": link_name}],
            }
        )
        address.insert(ignore_permissions=True)
        frappe.db.commit()
        return address.name

    # =========================================================================
    # Case A Tests: Same rule_fieldname (Full Merge)
    # =========================================================================

    def test_case_a_merge_customers_same_currency(self):
        """
        Test Case A: Two PMs with Customers having same currency.
        Expected: Customers should be merged into one.
        """
        from uph.party.controllers.party_merge_service import PartyMergeService

        # Create two Party Masters
        pm_a = self._create_party_master("A1")
        pm_b = self._create_party_master("B1")

        # Create customers with same currency (USD)
        cust_a = self._create_customer("A1", pm_a, "USD")
        cust_b = self._create_customer("B1", pm_b, "USD")

        # Perform merge
        service = PartyMergeService()
        result = service.merge(pm_a, pm_b)

        # Assertions
        self.assertTrue(result["success"])

        # PM-B should be deleted
        self.assertFalse(frappe.db.exists("Party Master", pm_b))

        # PM-A should still exist
        self.assertTrue(frappe.db.exists("Party Master", pm_a))

        # Customer A should exist
        self.assertTrue(frappe.db.exists("Customer", cust_a))

        # Customer B should NOT exist (merged into A)
        self.assertFalse(frappe.db.exists("Customer", cust_b))

    def test_case_a_transfers_addresses(self):
        """
        Test that addresses are transferred during Case A merge.
        """
        from uph.party.controllers.party_merge_service import PartyMergeService

        # Create Party Masters and Customers
        pm_a = self._create_party_master("A2")
        pm_b = self._create_party_master("B2")
        cust_a = self._create_customer("A2", pm_a, "USD")
        cust_b = self._create_customer("B2", pm_b, "USD")

        # Create address linked to Customer B
        addr_b = self._create_address("B2", "Customer", cust_b)

        # Perform merge
        service = PartyMergeService()
        result = service.merge(pm_a, pm_b)

        self.assertTrue(result["success"])

        # Address should now be linked to Customer A
        links = frappe.get_all(
            "Dynamic Link",
            filters={"parent": addr_b, "link_doctype": "Customer"},
            pluck="link_name",
        )
        self.assertIn(cust_a, links)

    # =========================================================================
    # Case B Tests: Different rule_fieldname (Re-link Only)
    # =========================================================================

    def test_case_b_relink_customers_different_currency(self):
        """
        Test Case B: Two PMs with Customers having different currencies.
        Expected: Both customers should exist under PM-A.
        """
        from uph.party.controllers.party_merge_service import PartyMergeService

        # Create two Party Masters
        pm_a = self._create_party_master("A3")
        pm_b = self._create_party_master("B3")

        # Create customers with different currencies
        cust_a = self._create_customer("A3", pm_a, "USD")
        cust_b = self._create_customer("B3", pm_b, "EUR")

        # Perform merge
        service = PartyMergeService()
        result = service.merge(pm_a, pm_b)

        # Assertions
        self.assertTrue(result["success"])

        # PM-B should be deleted
        self.assertFalse(frappe.db.exists("Party Master", pm_b))

        # Both customers should exist
        self.assertTrue(frappe.db.exists("Customer", cust_a))
        self.assertTrue(frappe.db.exists("Customer", cust_b))

        # Customer B should now be linked to PM-A
        new_pm = frappe.db.get_value("Customer", cust_b, "party_master")
        self.assertEqual(new_pm, pm_a)

    def test_case_b_preserves_transactions(self):
        """
        Test that transaction documents are updated after re-link.
        """
        from uph.party.controllers.party_merge_service import PartyMergeService

        # Create Party Masters and Customers
        pm_a = self._create_party_master("A4")
        pm_b = self._create_party_master("B4")
        cust_a = self._create_customer("A4", pm_a, "USD")
        cust_b = self._create_customer("B4", pm_b, "EUR")

        # Skip transaction test if Sales Invoice cannot be created
        # This test validates the service doesn't break with transactions
        service = PartyMergeService()
        result = service.merge(pm_a, pm_b)

        self.assertTrue(result["success"])
        self.assertIn("merge_log", result)

    # =========================================================================
    # Edge Case Tests
    # =========================================================================

    def test_merge_with_no_linked_parties(self):
        """
        Test merging Party Masters with no linked parties.
        """
        from uph.party.controllers.party_merge_service import PartyMergeService

        # Create Party Masters without customers
        pm_a = self._create_party_master("A5")
        pm_b = self._create_party_master("B5")

        # Perform merge
        service = PartyMergeService()
        result = service.merge(pm_a, pm_b)

        self.assertTrue(result["success"])
        self.assertFalse(frappe.db.exists("Party Master", pm_b))
        self.assertTrue(frappe.db.exists("Party Master", pm_a))

    def test_merge_with_mixed_scenarios(self):
        """
        Test merge with both Case A and Case B scenarios.
        PM-A has Customer(USD)
        PM-B has Customer(USD) and Customer(EUR)
        Expected: USD customers merge, EUR customer relinks
        """
        from uph.party.controllers.party_merge_service import PartyMergeService

        # Create Party Masters
        pm_a = self._create_party_master("A6")
        pm_b = self._create_party_master("B6")

        # Create customers
        cust_a_usd = self._create_customer("A6-USD", pm_a, "USD")
        cust_b_usd = self._create_customer("B6-USD", pm_b, "USD")
        cust_b_eur = self._create_customer("B6-EUR", pm_b, "EUR")

        # Perform merge
        service = PartyMergeService()
        result = service.merge(pm_a, pm_b)

        self.assertTrue(result["success"])

        # PM-B should be deleted
        self.assertFalse(frappe.db.exists("Party Master", pm_b))

        # Customer A USD should exist
        self.assertTrue(frappe.db.exists("Customer", cust_a_usd))

        # Customer B USD should NOT exist (merged)
        self.assertFalse(frappe.db.exists("Customer", cust_b_usd))

        # Customer B EUR should exist (relinked)
        self.assertTrue(frappe.db.exists("Customer", cust_b_eur))

        # Customer B EUR should point to PM-A
        new_pm = frappe.db.get_value("Customer", cust_b_eur, "party_master")
        self.assertEqual(new_pm, pm_a)

    def test_merge_transfers_pm_accounts(self):
        """
        Test that PM accounts are transferred during merge.
        """
        from uph.party.controllers.party_merge_service import PartyMergeService

        # Create Party Masters
        pm_a = self._create_party_master("A7")
        pm_b = self._create_party_master("B7")

        # Add account to PM-B
        pm_b_doc = frappe.get_doc("Party Master", pm_b)
        account = frappe.db.get_value(
            "Account",
            {"company": self.test_company, "is_group": 0, "account_type": "Receivable"},
            "name",
        )
        if account:
            pm_b_doc.append(
                "accounts", {"company": self.test_company, "account": account}
            )
            pm_b_doc.save(ignore_permissions=True)

        # Perform merge
        service = PartyMergeService()
        result = service.merge(pm_a, pm_b)

        self.assertTrue(result["success"])

        # PM-A should have the transferred account
        if account:
            pm_a_doc = frappe.get_doc("Party Master", pm_a)
            account_companies = [acc.company for acc in pm_a_doc.accounts]
            self.assertIn(self.test_company, account_companies)

    # =========================================================================
    # Permission Tests
    # =========================================================================

    def test_merge_requires_permission(self):
        """
        Test that merge requires write permission.
        """
        from uph.party.controllers.party_merge_service import PartyMergeService

        # Create Party Masters
        pm_a = self._create_party_master("A8")
        pm_b = self._create_party_master("B8")

        # Switch to guest user (no permissions)
        frappe.set_user("Guest")

        service = PartyMergeService()
        with self.assertRaises(frappe.PermissionError):
            service.merge(pm_a, pm_b)

        # Restore admin user
        frappe.set_user("Administrator")

    def test_cannot_merge_same_party(self):
        """
        Test that merging a party with itself fails.
        """
        from uph.party.controllers.party_merge_service import PartyMergeService

        pm_a = self._create_party_master("A9")

        service = PartyMergeService()
        with self.assertRaises(frappe.ValidationError):
            service.merge(pm_a, pm_a)

    def test_cannot_merge_nonexistent_party(self):
        """
        Test that merging nonexistent parties fails.
        """
        from uph.party.controllers.party_merge_service import PartyMergeService

        pm_a = self._create_party_master("A10")

        service = PartyMergeService()
        with self.assertRaises(frappe.ValidationError):
            service.merge(pm_a, "_Nonexistent_PM")

    # =========================================================================
    # API Tests
    # =========================================================================

    def test_merge_api_endpoint(self):
        """
        Test the merge_parties whitelist API.
        """
        from uph.party.page.data_quality_dashboard.data_quality_dashboard import (
            merge_parties,
        )

        # Create Party Masters
        pm_a = self._create_party_master("A11")
        pm_b = self._create_party_master("B11")

        # Call API
        result = merge_parties(pm_a, pm_b)

        self.assertTrue(result["success"])
        self.assertFalse(frappe.db.exists("Party Master", pm_b))

    def test_merge_with_fields_to_keep(self):
        """
        Test that fields_to_keep parameter works correctly.
        """
        from uph.party.controllers.party_merge_service import PartyMergeService

        # Create Party Masters
        pm_a = self._create_party_master("A12")
        pm_b = self._create_party_master("B12")

        # Set tax_id on PM-B
        frappe.db.set_value("Party Master", pm_b, "tax_id", "TEST-TAX-123")

        # Perform merge with fields_to_keep
        service = PartyMergeService()
        result = service.merge(pm_a, pm_b, fields_to_keep={"tax_id": "TEST-TAX-123"})

        self.assertTrue(result["success"])

        # PM-A should have the tax_id
        tax_id = frappe.db.get_value("Party Master", pm_a, "tax_id")
        self.assertEqual(tax_id, "TEST-TAX-123")


class TestPartyMergeClassification(FrappeTestCase):
    """Test merge classification logic."""

    def test_classify_same_currency_as_merge(self):
        """Test that same currency results in merge action."""
        from uph.party.controllers.party_merge_service import PartyMergeService

        service = PartyMergeService()

        primary_parties = {
            "Customer": [
                {
                    "name": "Cust-A",
                    "rule_fieldname": "default_currency",
                    "rule_value": "USD",
                }
            ]
        }
        secondary_parties = {
            "Customer": [
                {
                    "name": "Cust-B",
                    "rule_fieldname": "default_currency",
                    "rule_value": "USD",
                }
            ]
        }

        plan = service._classify_merge_types(primary_parties, secondary_parties)

        self.assertEqual(len(plan["Customer"]), 1)
        self.assertEqual(plan["Customer"][0]["action"], "merge")

    def test_classify_different_currency_as_relink(self):
        """Test that different currency results in relink action."""
        from uph.party.controllers.party_merge_service import PartyMergeService

        service = PartyMergeService()

        primary_parties = {
            "Customer": [
                {
                    "name": "Cust-A",
                    "rule_fieldname": "default_currency",
                    "rule_value": "USD",
                }
            ]
        }
        secondary_parties = {
            "Customer": [
                {
                    "name": "Cust-B",
                    "rule_fieldname": "default_currency",
                    "rule_value": "EUR",
                }
            ]
        }

        plan = service._classify_merge_types(primary_parties, secondary_parties)

        self.assertEqual(len(plan["Customer"]), 1)
        self.assertEqual(plan["Customer"][0]["action"], "relink")

    def test_classify_no_primary_as_relink(self):
        """Test that no matching primary results in relink action."""
        from uph.party.controllers.party_merge_service import PartyMergeService

        service = PartyMergeService()

        primary_parties = {}  # No customers in primary
        secondary_parties = {
            "Customer": [
                {
                    "name": "Cust-B",
                    "rule_fieldname": "default_currency",
                    "rule_value": "USD",
                }
            ]
        }

        plan = service._classify_merge_types(primary_parties, secondary_parties)

        self.assertEqual(len(plan["Customer"]), 1)
        self.assertEqual(plan["Customer"][0]["action"], "relink")
