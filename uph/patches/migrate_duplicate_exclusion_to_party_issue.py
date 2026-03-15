import frappe
from frappe.utils import now_datetime

from uph.party.controllers.party_issue_utils import normalize_party_pair

STATUS_MAP = {
	"Detected": "Open",
	"Dismissed": "Ignored",
	"Merged": "Resolved",
}


def _severity_from_score(score):
	if score is None:
		return "Low"
	try:
		score = float(score)
	except Exception:
		return "Low"
	if score >= 95:
		return "Critical"
	if score >= 90:
		return "High"
	if score >= 80:
		return "Medium"
	return "Low"


def execute():
	if not frappe.db.exists("DocType", "Duplicate Exclusion"):
		return
	if not frappe.db.exists("DocType", "Party Issue"):
		return

	# Check available columns to avoid OperationalError: (1054, "Unknown column '...' in 'SELECT'")
	# Some older sites or specific environments might have a truncated/different schema for Duplicate Exclusion
	available_columns = set(frappe.db.get_table_columns("Duplicate Exclusion"))
	desired_fields = [
		"name",
		"party_1",
		"party_2",
		"status",
		"similarity_score",
		"normalized_name_1",
		"normalized_name_2",
		"detected_on",
		"dismissed_on",
		"dismissed_by",
		"dismissed_reason",
		"creation",
	]
	fields_to_fetch = [f for f in desired_fields if f in available_columns]

	rows = frappe.get_all(
		"Duplicate Exclusion",
		fields=fields_to_fetch,
		limit_page_length=0,
	)

	for row in rows:
		party_1, party_2 = normalize_party_pair(row.get("party_1"), row.get("party_2"))
		status = STATUS_MAP.get(row.get("status"), "Open")

		exists = frappe.db.get_value(
			"Party Issue",
			{
				"party": party_1,
				"party_secondary": party_2,
				"issue_type": "Duplicate",
			},
			"name",
		)
		if exists:
			continue

		details = {
			"source": "Duplicate Exclusion",
			"normalized_name_1": row.get("normalized_name_1"),
			"normalized_name_2": row.get("normalized_name_2"),
			"dismissed_reason": row.get("dismissed_reason"),
			"legacy_name": row.get("name"),
		}

		doc = frappe.get_doc(
			{
				"doctype": "Party Issue",
				"party": party_1,
				"party_secondary": party_2,
				"issue_type": "Duplicate",
				"severity": _severity_from_score(row.get("similarity_score")),
				"status": status,
				"score": row.get("similarity_score"),
				"source_engine": "duplicate_exclusion_migration",
				"details_json": frappe.as_json(details),
				"detected_on": row.get("detected_on") or row.get("creation") or now_datetime(),
			}
		)

		if status in ("Resolved", "Ignored"):
			doc.resolved_on = row.get("dismissed_on") or now_datetime()
			doc.resolved_by = row.get("dismissed_by")

		doc.insert(ignore_permissions=True)
