import unittest

import frappe

from uph.party.controllers.party_issue_utils import create_party_issue_if_missing


class TestPartyIssue(unittest.TestCase):
	def setUp(self):
		self.parent = frappe.get_all(
			"Party Master",
			filters={"is_group": 1},
			order_by="lft asc",
			pluck="name",
			limit=1,
		)[0]
		self.party = frappe.get_doc(
			{
				"doctype": "Party Master",
				"party_name": f"Test Party Issue {frappe.generate_hash(length=8)}",
				"parent_party_master": self.parent,
				"party_type": "Customer",
				"is_group": 0,
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.db.rollback()

	def test_create_party_issue_idempotent(self):
		issue_1, created_1 = create_party_issue_if_missing(
			party_master=self.party.name,
			issue_type="Duplicate",
			severity="High",
			source_engine="test",
			party_secondary=self.party.name,
		)
		issue_2, created_2 = create_party_issue_if_missing(
			party_master=self.party.name,
			issue_type="Duplicate",
			severity="High",
			source_engine="test",
			party_secondary=self.party.name,
		)
		self.assertTrue(created_1)
		self.assertFalse(created_2)
		self.assertEqual(issue_1, issue_2)

	def test_resolved_metadata(self):
		doc = frappe.get_doc(
			{
				"doctype": "Party Issue",
				"party_master": self.party.name,
				"issue_type": "Health",
				"severity": "Low",
				"status": "Open",
				"source_engine": "test",
			}
		).insert(ignore_permissions=True)
		doc.status = "Under Review"
		doc.save(ignore_permissions=True)
		doc.status = "Resolved"
		doc.save(ignore_permissions=True)
		self.assertTrue(doc.resolved_on)
		self.assertEqual(doc.resolved_by, frappe.session.user)
