# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

"""
Tests for Data Quality Dashboard API.
"""

import frappe
from frappe.tests.utils import FrappeTestCase


class TestDataQualityDashboard(FrappeTestCase):
	"""Test suite for Data Quality Dashboard functionality."""

	def test_get_duplicate_issues(self):
		"""Test get_duplicate_issues API."""
		from uph.party.page.data_quality_dashboard.data_quality_dashboard import (
			get_duplicate_issues,
		)

		result = get_duplicate_issues(limit=50, min_score=50)

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
		self.assertIn("duplicate_issues", stats)
		self.assertIn("unlinked_count", stats)
		self.assertIn("draft_voucher_count", stats)
		self.assertIn("cancelled_unamended_count", stats)
		self.assertIn("unlinked_transaction_count", stats)

		# Should have some parties
		self.assertGreaterEqual(stats["total_parties"], 0)


class TestDuplicateIssues(FrappeTestCase):
	"""Tests for Duplicate Party Issue flow."""

	def test_dismiss_duplicate_issue(self):
		"""Test dismissing a duplicate issue."""
		from uph.party.page.data_quality_dashboard.data_quality_dashboard import (
			dismiss_duplicate,
		)

		parties = frappe.get_all("Party Master", limit=2, pluck="name")
		if len(parties) < 2:
			self.skipTest("Need at least 2 Party Masters for this test")

		from uph.party.controllers.party_issue_utils import normalize_party_pair

		party_1, party_2 = normalize_party_pair(parties[0], parties[1])
		issue = frappe.get_doc(
			{
				"doctype": "Party Issue",
				"party_master": party_1,
				"reference_doctype": "Party Master",
				"reference_name": party_2,
				"issue_type": "Duplicate",
				"severity": "Medium",
				"status": "Open",
				"source_engine": "test",
			}
		).insert(ignore_permissions=True)

		result = dismiss_duplicate(party_1, party_2, reason="Test ignore")
		self.assertTrue(result.get("success"))

		issue.reload()
		self.assertEqual(issue.status, "Ignored")
