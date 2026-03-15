# Copyright (c) 2026, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.dashboard import cache_source


@frappe.whitelist()
@cache_source
def get_data(
	chart_name=None,
	chart=None,
	no_cache=None,
	filters=None,
	from_date=None,
	to_date=None,
	timespan=None,
	time_interval=None,
	heatmap_year=None,
):
	if chart_name:
		chart = frappe.get_doc("Dashboard Chart", chart_name)
	else:
		chart = frappe._dict(frappe.parse_json(chart))

	filters = frappe.parse_json(filters or "{}")

	# Get configured party types from settings
	settings = frappe.get_cached_doc("Party Master Settings")
	party_types = [p.party_type for p in settings.party_types]

	labels = []
	linked_values = []
	unlinked_values = []
	quality_scores = []

	for pt in party_types:
		labels.append(_(pt))

		# Calculate Linked vs Unlinked
		# Check if tax_id field exists
		has_tax_id = frappe.get_meta(pt).has_field("tax_id")
		tax_id_query = (
			"COUNT(CASE WHEN tax_id IS NOT NULL AND tax_id != '' THEN 1 END)" if has_tax_id else "0"
		)

		# Calculate Linked vs Unlinked
		stats = frappe.db.sql(
			f"""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN party_master IS NOT NULL THEN 1 END) as linked,
                COUNT(CASE WHEN party_master IS NULL THEN 1 END) as unlinked,
                {tax_id_query} as with_tax_id
            FROM `tab{pt}`
            WHERE docstatus < 2
            """,
			as_dict=True,
		)[0]

		linked_values.append(stats.linked)
		unlinked_values.append(stats.unlinked)

		# Calculate a simple Quality Score % (Linked and having Tax ID)
		total = stats.total or 1
		score = ((stats.linked + stats.with_tax_id) / (2 * total)) * 100
		quality_scores.append(round(score, 1))

	return {
		"labels": labels,
		"datasets": [
			{"name": _("Linked"), "chartType": "bar", "values": linked_values},
			{"name": _("Unlinked"), "chartType": "bar", "values": unlinked_values},
			{
				"name": _("Quality Score (%)"),
				"chartType": "line",
				"values": quality_scores,
			},
		],
	}
