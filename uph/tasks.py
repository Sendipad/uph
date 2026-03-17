import json

import frappe

from uph.party.controllers.duplicate_scanner import run_duplicate_scan
from uph.party.controllers.party_issue_utils import OPEN_STATUSES


def refresh_dashboard_stats():
	"""
	Calculates dashboard stats and caches them in Redis.
	Runs hourly.
	"""
	open_status = ["in", list(OPEN_STATUSES)]

	duplicate_open = frappe.db.count("Party Issue", {"issue_type": "Duplicate", "status": open_status})
	duplicate_ignored = frappe.db.count("Party Issue", {"issue_type": "Duplicate", "status": "Ignored"})
	duplicate_resolved = frappe.db.count("Party Issue", {"issue_type": "Duplicate", "status": "Resolved"})

	unlinked_open = frappe.db.count("Party Issue", {"issue_type": "Unlinked", "status": open_status})

	# Transaction policy issue breakdown (draft_overdue / cancelled_referenced)
	policy_issues = frappe.get_all(
		"Party Issue",
		filters={"issue_type": "Transaction Policy", "status": open_status},
		fields=["details_json"],
	)
	policy_draft = 0
	policy_cancelled = 0
	policy_mismatch = 0
	for row in policy_issues:
		if not row.details_json:
			continue
		try:
			details = json.loads(row.details_json)
		except Exception:
			continue
		issue_code = details.get("issue")
		if issue_code == "draft_overdue":
			policy_draft += 1
		elif issue_code == "cancelled_referenced":
			policy_cancelled += 1
		elif issue_code == "party_master_mismatch":
			policy_mismatch += 1

	total_parties = frappe.db.count("Party Master", {"is_group": 0})
	total_groups = frappe.db.count("Party Master", {"is_group": 1})
	incomplete_count = frappe.db.count("Party Master", {"is_group": 0, "party_type": ["is", "not set"]})

	frappe.cache.set_value("uph:stats:duplicate_open", duplicate_open)
	frappe.cache.set_value("uph:stats:duplicate_ignored", duplicate_ignored)
	frappe.cache.set_value("uph:stats:duplicate_resolved", duplicate_resolved)
	frappe.cache.set_value("uph:stats:unlinked_open", unlinked_open)
	frappe.cache.set_value("uph:stats:policy_draft", policy_draft)
	frappe.cache.set_value("uph:stats:policy_cancelled", policy_cancelled)
	frappe.cache.set_value("uph:stats:policy_mismatch", policy_mismatch)
	frappe.cache.set_value("uph:stats:total_parties", total_parties)
	frappe.cache.set_value("uph:stats:total_groups", total_groups)
	frappe.cache.set_value("uph:stats:incomplete_count", incomplete_count)
	frappe.cache.set_value("uph:stats:last_updated", frappe.utils.now())


def run_full_duplicate_scan():
	"""
	Scans for duplicates and creates Party Issue (Duplicate) records.
	Runs daily.
	"""
	run_duplicate_scan()


def run_all_quality_scans():
	"""
	Runs all data quality scanners and refreshes dashboard stats.
	"""
	from uph.party.controllers.duplicate_scanner import run_duplicate_scan
	from uph.party.controllers.transaction_health import run_transaction_policy_scan
	from uph.party.controllers.unlinked_resolver import run_unlinked_issue_scan

	run_duplicate_scan()
	run_unlinked_issue_scan()
	run_transaction_policy_scan()
	refresh_dashboard_stats()
