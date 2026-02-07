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
        # Ensure a root group exists
        if not frappe.db.exists("Party Master", {"party_name": "Root Group"}):
            frappe.get_doc(
                {
                    "doctype": "Party Master",
                    "party_name": "Root Group",
                    "is_group": 1,
                    "party_type": "Customer",
                }
            ).insert(ignore_permissions=True)

        root_group = frappe.db.get_value(
            "Party Master", {"party_name": "Root Group"}, "name"
        )

        for name in ["_Test Company A", "_Test Company B", "_Test Company C"]:
            if not frappe.db.exists("Party Master", {"party_name": name}):
                try:
                    frappe.get_doc(
                        {
                            "doctype": "Party Master",
                            "party_name": name,
                            "party_type": "Customer",
                            "parent_party_master": root_group,
                        }
                    ).insert(ignore_permissions=True)
                except frappe.ValidationError:
                    pass  # May already exist
        frappe.db.commit()

    def tearDown(self):
        """Clean up test relationships after each test."""
        # Find all test parties
        test_parties = frappe.get_all(
            "Party Master", filters={"party_name": ["like", "_Test%"]}, pluck="name"
        )
        if test_parties:
            frappe.db.delete(
                "Party Relationship",
                {"subject_party": ["in", test_parties]},
            )
            frappe.db.delete(
                "Party Relationship",
                {"object_party": ["in", test_parties]},
            )
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
        frappe.db.delete("Party Relationship", {"subject_party": parties[0]})
        frappe.db.delete("Party Relationship", {"subject_party": parties[1]})

    def test_circular_dependency(self):
        """Test circular dependency prevention."""
        # Ensure Relationship Type has prevent_circular = 1
        if not frappe.db.exists("Party Relationship Type", "Hierarchy Check"):
            frappe.get_doc(
                {
                    "doctype": "Party Relationship Type",
                    "relationship_type_name": "Hierarchy Check",
                    "prevent_circular": 1,
                    "is_enabled": 1,
                }
            ).insert(ignore_permissions=True)

        p1 = self._create_party("P1")
        p2 = self._create_party("P2")
        p3 = self._create_party("P3")

        # Cleanup potential existing relationships from previous runs
        frappe.db.delete("Party Relationship", {"subject_party": ["in", [p1, p2, p3]]})
        frappe.db.delete("Party Relationship", {"object_party": ["in", [p1, p2, p3]]})
        frappe.db.commit()

        # P1 -> P2
        frappe.get_doc(
            {
                "doctype": "Party Relationship",
                "subject_party": p1,
                "relationship_type": "Hierarchy Check",
                "object_party": p2,
            }
        ).insert()

        # P2 -> P3
        frappe.get_doc(
            {
                "doctype": "Party Relationship",
                "subject_party": p2,
                "relationship_type": "Hierarchy Check",
                "object_party": p3,
            }
        ).insert()

        # Try P3 -> P1 (Circular)
        rel = frappe.get_doc(
            {
                "doctype": "Party Relationship",
                "subject_party": p3,
                "relationship_type": "Hierarchy Check",
                "object_party": p1,
            }
        )
        self.assertRaises(frappe.ValidationError, rel.insert)

    def test_symmetric_relationship(self):
        """Test symmetric relationship creation."""
        if not frappe.db.exists("Party Relationship Type", "Peer"):
            frappe.get_doc(
                {
                    "doctype": "Party Relationship Type",
                    "relationship_type_name": "Peer",
                    "is_symmetric": 1,
                    "is_enabled": 1,
                }
            ).insert(ignore_permissions=True)

        p1 = self._create_party("S1")
        p2 = self._create_party("S2")

        # Create P1 -> P2
        rel = frappe.get_doc(
            {
                "doctype": "Party Relationship",
                "subject_party": p1,
                "relationship_type": "Peer",
                "object_party": p2,
                "is_guarantor": 1,
            }
        ).insert()

        # Check if P2 -> P1 exists
        reverse = frappe.db.get_value(
            "Party Relationship",
            {"subject_party": p2, "relationship_type": "Peer", "object_party": p1},
            ["name", "is_guarantor"],
            as_dict=1,
        )

        self.assertTrue(reverse)
        self.assertEqual(reverse.is_guarantor, 1)

    def _create_party(self, name):
        # Ensure a root group exists
        if not frappe.db.exists("Party Master", {"party_name": "Root Group"}):
            frappe.get_doc(
                {
                    "doctype": "Party Master",
                    "party_name": "Root Group",
                    "is_group": 1,
                    "party_type": "Customer",
                }
            ).insert(ignore_permissions=True)

        root_group = frappe.db.get_value(
            "Party Master", {"party_name": "Root Group"}, "name"
        )

        pname = f"_Test_Party_{name}"
        if not frappe.db.exists("Party Master", {"party_name": pname}):
            return (
                frappe.get_doc(
                    {
                        "doctype": "Party Master",
                        "party_name": pname,
                        "party_type": "Customer",
                        "parent_party_master": root_group,
                    }
                )
                .insert(ignore_permissions=True)
                .name
            )
        return frappe.get_value("Party Master", {"party_name": pname}, "name")
