import frappe
from frappe.tests.utils import FrappeTestCase


class TestPartyNumbering(FrappeTestCase):
    def setUp(self):
        frappe.db.delete("Party Master")

    def test_numbering_hierarchy(self):
        # 1. Root Group (should be 1000)
        root = frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": "Root Group",
                "is_group": 1,
                "party_type": "Customer",
            }
        ).insert(ignore_permissions=True)

        self.assertEqual(root.party_number, "1000")

        # 2. Subgroup (should be 1100)
        subgroup = frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": "Sub Group",
                "parent_party_master": root.name,
                "is_group": 1,
                "party_type": "Customer",
            }
        ).insert(ignore_permissions=True)

        self.assertEqual(subgroup.party_number, "1100")

        # 3. Leaf under Subgroup (should be 1100000001)
        leaf = frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": "Edge Leaf",
                "parent_party_master": subgroup.name,
                "is_group": 0,
                "party_type": "Customer",
            }
        ).insert(ignore_permissions=True)

        self.assertEqual(leaf.party_number, "1100000001")

        # 4. Another Leaf (should be 1100000002)
        leaf2 = frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": "Edge Leaf 2",
                "parent_party_master": subgroup.name,
                "is_group": 0,
                "party_type": "Customer",
            }
        ).insert(ignore_permissions=True)

        self.assertEqual(leaf2.party_number, "1100000002")

    def test_root_leaf_prevention(self):
        # Should throw if trying to create leaf without parent
        leaf = frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": "Lone Leaf",
                "is_group": 0,
                "party_type": "Customer",
            }
        )
        self.assertRaises(frappe.ValidationError, leaf.insert)
