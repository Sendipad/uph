# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

"""
Tests for Data Quality Dashboard API.
"""

import frappe
from frappe.tests.utils import FrappeTestCase


class TestDataQualityDashboard(FrappeTestCase):
    """Test suite for Data Quality Dashboard functionality."""

    def test_get_potential_duplicates(self):
        """Test get_potential_duplicates API."""
        from uph.party.page.data_quality_dashboard.data_quality_dashboard import (
            get_potential_duplicates,
        )

        result = get_potential_duplicates(limit=50, min_score=50)

        self.assertIn("duplicates", result)
        self.assertIn("total", result)
        self.assertIsInstance(result["duplicates"], list)

    def test_get_dashboard_stats(self):
        """Test get_dashboard_stats API."""
        from uph.party.page.data_quality_dashboard.data_quality_dashboard import (
            get_dashboard_stats,
        )

        stats = get_dashboard_stats()

        self.assertIn("total_parties", stats)
        self.assertIn("total_groups", stats)
        self.assertIn("total_dismissed", stats)
        self.assertIn("total_merged", stats)
        self.assertIn("incomplete_parties", stats)
        self.assertIn("potential_duplicates", stats)
        self.assertIn("unlinked_count", stats)
        self.assertIn("draft_voucher_count", stats)
        self.assertIn("cancelled_unamended_count", stats)

        # Should have some parties
        self.assertGreaterEqual(stats["total_parties"], 0)


class TestDuplicateExclusion(FrappeTestCase):
    """Tests for Duplicate Exclusion DocType."""

    def setUp(self):
        # Clean up any existing test exclusions before each test
        frappe.db.delete(
            "Duplicate Exclusion", {"dismissed_reason": ["like", "%Test%"]}
        )
        frappe.db.commit()

    def tearDown(self):
        frappe.db.delete(
            "Duplicate Exclusion", {"dismissed_reason": ["like", "%Test%"]}
        )
        frappe.db.commit()

    def test_create_exclusion(self):
        """Test creating a duplicate exclusion."""
        parties = frappe.get_all("Party Master", limit=2, pluck="name")
        if len(parties) < 2:
            self.skipTest("Need at least 2 Party Masters for this test")

        # Make sure this pair doesn't exist
        frappe.db.delete(
            "Duplicate Exclusion", {"party_1": parties[0], "party_2": parties[1]}
        )
        frappe.db.delete(
            "Duplicate Exclusion", {"party_1": parties[1], "party_2": parties[0]}
        )
        frappe.db.commit()

        doc = frappe.get_doc(
            {
                "doctype": "Duplicate Exclusion",
                "party_1": parties[0],
                "party_2": parties[1],
                "status": "Dismissed",
                "dismissed_reason": "Test exclusion",
            }
        )
        doc.insert(ignore_permissions=True)

        self.assertTrue(frappe.db.exists("Duplicate Exclusion", doc.name))

    def test_same_party_prevented(self):
        """Test that same party in both fields is prevented."""
        parties = frappe.get_all("Party Master", limit=1, pluck="name")
        if not parties:
            self.skipTest("Need at least 1 Party Master for this test")

        doc = frappe.get_doc(
            {
                "doctype": "Duplicate Exclusion",
                "party_1": parties[0],
                "party_2": parties[0],
            }
        )

        self.assertRaises(frappe.ValidationError, doc.insert)

    def test_is_excluded_pair_function(self):
        """Test is_excluded_pair helper function."""
        from uph.party.doctype.duplicate_exclusion.duplicate_exclusion import (
            is_excluded_pair,
        )

        parties = frappe.get_all("Party Master", limit=2, pluck="name")
        if len(parties) < 2:
            self.skipTest("Need at least 2 Party Masters for this test")

        # Clean up any existing exclusion for this pair
        frappe.db.delete(
            "Duplicate Exclusion",
            {
                "party_1": min(parties[0], parties[1]),
                "party_2": max(parties[0], parties[1]),
            },
        )
        frappe.db.commit()

        # Create exclusion
        frappe.get_doc(
            {
                "doctype": "Duplicate Exclusion",
                "party_1": parties[0],
                "party_2": parties[1],
                "status": "Dismissed",
                "dismissed_reason": "Test is_excluded_pair",
            }
        ).insert(ignore_permissions=True)
        frappe.db.commit()

        # Check both orderings
        self.assertTrue(is_excluded_pair(parties[0], parties[1]))
        self.assertTrue(is_excluded_pair(parties[1], parties[0]))

        # Check non-excluded pair
        self.assertFalse(is_excluded_pair("_Nonexistent_A", "_Nonexistent_B"))
