# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestPartyRelationship(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_test_relationship_types()
        cls._create_test_party_masters()

    @classmethod
    def _create_test_relationship_types(cls):
        """Create test relationship types."""
        # Create types one by one without reverse links first
        # Parent Company
        if not frappe.db.exists("Party Relationship Type", "Parent Company"):
            frappe.get_doc(
                {
                    "doctype": "Party Relationship Type",
                    "relationship_type_name": "Parent Company",
                    "is_hierarchical": 1,
                    "is_enabled": 1,
                }
            ).insert(ignore_permissions=True)

        # Subsidiary
        if not frappe.db.exists("Party Relationship Type", "Subsidiary"):
            frappe.get_doc(
                {
                    "doctype": "Party Relationship Type",
                    "relationship_type_name": "Subsidiary",
                    "is_hierarchical": 1,
                    "is_enabled": 1,
                }
            ).insert(ignore_permissions=True)

        # Partner
        if not frappe.db.exists("Party Relationship Type", "Partner"):
            frappe.get_doc(
                {
                    "doctype": "Party Relationship Type",
                    "relationship_type_name": "Partner",
                    "is_hierarchical": 0,
                    "is_enabled": 1,
                }
            ).insert(ignore_permissions=True)

        # Now update the reverse relationships
        frappe.db.set_value(
            "Party Relationship Type",
            "Parent Company",
            "reverse_relationship_type",
            "Subsidiary",
        )
        frappe.db.set_value(
            "Party Relationship Type",
            "Subsidiary",
            "reverse_relationship_type",
            "Parent Company",
        )
        frappe.db.set_value(
            "Party Relationship Type", "Partner", "reverse_relationship_type", "Partner"
        )
        frappe.db.commit()

    @classmethod
    def _create_test_party_masters(cls):
        """Create test party masters."""
        for name in ["_Test Company A", "_Test Company B", "_Test Company C"]:
            if not frappe.db.exists("Party Master", {"party_name": name}):
                try:
                    frappe.get_doc(
                        {
                            "doctype": "Party Master",
                            "party_name": name,
                            "party_type": "Customer",
                        }
                    ).insert(ignore_permissions=True)
                except frappe.ValidationError:
                    pass  # May already exist
        frappe.db.commit()

    def tearDown(self):
        """Clean up test relationships after each test."""
        frappe.db.delete("Party Relationship", {"subject_party": ["like", "_Test%"]})
        frappe.db.commit()

    def test_create_relationship(self):
        """Test basic relationship creation."""
        # Get existing parties
        parties = frappe.get_all("Party Master", limit=2, pluck="name")
        if len(parties) < 2:
            self.skipTest("Need at least 2 Party Masters")

        rel = frappe.get_doc(
            {
                "doctype": "Party Relationship",
                "subject_party": parties[0],
                "relationship_type": "Partner",
                "object_party": parties[1],
            }
        )
        rel.insert(ignore_permissions=True)

        self.assertTrue(frappe.db.exists("Party Relationship", rel.name))
        self.assertEqual(rel.status, "Active")

        # Cleanup
        rel.delete()

    def test_self_referential_blocked(self):
        """Test that self-referential relationships are blocked."""
        parties = frappe.get_all("Party Master", limit=1, pluck="name")
        if not parties:
            self.skipTest("Need at least 1 Party Master")

        rel = frappe.get_doc(
            {
                "doctype": "Party Relationship",
                "subject_party": parties[0],
                "relationship_type": "Partner",
                "object_party": parties[0],
            }
        )

        self.assertRaises(frappe.ValidationError, rel.insert)

    def test_date_range_validation(self):
        """Test that end_date must be after start_date."""
        parties = frappe.get_all("Party Master", limit=2, pluck="name")
        if len(parties) < 2:
            self.skipTest("Need at least 2 Party Masters")

        rel = frappe.get_doc(
            {
                "doctype": "Party Relationship",
                "subject_party": parties[0],
                "relationship_type": "Partner",
                "object_party": parties[1],
                "start_date": "2025-12-31",
                "end_date": "2025-01-01",  # Before start_date
            }
        )

        self.assertRaises(frappe.ValidationError, rel.insert)

    def test_ownership_percentage_validation(self):
        """Test ownership percentage must be 0-100."""
        parties = frappe.get_all("Party Master", limit=2, pluck="name")
        if len(parties) < 2:
            self.skipTest("Need at least 2 Party Masters")

        rel = frappe.get_doc(
            {
                "doctype": "Party Relationship",
                "subject_party": parties[0],
                "relationship_type": "Parent Company",
                "object_party": parties[1],
                "ownership_percentage": 150,  # Invalid
            }
        )

        self.assertRaises(frappe.ValidationError, rel.insert)

    def test_get_party_relationships_api(self):
        """Test get_party_relationships API function."""
        from uph.party.doctype.party_relationship.party_relationship import (
            get_party_relationships,
        )

        parties = frappe.get_all("Party Master", limit=2, pluck="name")
        if len(parties) < 2:
            self.skipTest("Need at least 2 Party Masters")

        # Create test relationship
        rel = frappe.get_doc(
            {
                "doctype": "Party Relationship",
                "subject_party": parties[0],
                "relationship_type": "Partner",
                "object_party": parties[1],
            }
        )
        rel.insert(ignore_permissions=True)

        # Test outgoing
        outgoing = get_party_relationships(parties[0], "outgoing")
        self.assertGreaterEqual(len(outgoing), 1)

        # Cleanup
        rel.delete()
