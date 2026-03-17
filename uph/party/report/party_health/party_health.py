# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from uph.party.controllers.cache_utils import get_pm_doctypes


def execute(filters=None):
	columns = [
		{
			"label": _("Party Master"),
			"fieldname": "party_master",
			"fieldtype": "Link",
			"options": "Party Master",
			"width": 200,
		},
		{
			"label": _("Party Name"),
			"fieldname": "party_name",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("DocType"),
			"fieldname": "doctype",
			"fieldtype": "Link",
			"options": "DocType",
			"width": 140,
		},
		{
			"label": _("Voucher No"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "doctype",
			"width": 180,
		},
		{
			"label": _("Issue Type"),
			"fieldname": "issue_type",
			"fieldtype": "Data",
			"width": 150,
		},  # Draft / Cancelled Unamended
		{"label": _("Owner"), "fieldname": "owner", "fieldtype": "Data", "width": 140},
		{
			"label": _("Creation"),
			"fieldname": "creation",
			"fieldtype": "Date",
			"width": 100,
		},
	]

	data = []

	# Get configured transaction types
	tx_doctypes = get_pm_doctypes() or []
	processed_types = set()

	target_party = filters.get("party_master") if filters else None

	for row in tx_doctypes:
		# cache_utils returns list of lists: [parent_doctype, document_type, party_fieldname]
		doctype = row[0]

		if doctype in processed_types:
			continue
		processed_types.add(doctype)

		if not frappe.db.exists("DocType", doctype):
			continue

		meta = frappe.get_meta(doctype)
		if not meta.has_field("docstatus") or not meta.has_field("party_master"):
			continue

		# Filters
		query_filters = {"party_master": ["is", "set"]}
		if target_party:
			query_filters["party_master"] = target_party

		# Drafts
		draft_filters = query_filters.copy()
		draft_filters["docstatus"] = 0

		drafts = frappe.get_all(
			doctype,
			filters=draft_filters,
			fields=["name", "party_master", "owner", "creation"],
			limit=100,
		)
		for d in drafts:
			data.append(
				{
					"party_master": d.party_master,
					"party_name": frappe.db.get_value("Party Master", d.party_master, "party_name")
					or d.party_master,
					"doctype": doctype,
					"voucher_no": d.name,
					"issue_type": "Draft",
					"owner": d.owner,
					"creation": d.creation,
				}
			)

		# Cancelled Unamended
		if meta.has_field("amended_from"):
			cancelled_filters = query_filters.copy()
			cancelled_filters["docstatus"] = 2
			cancelled_filters["amended_from"] = ["in", [None, ""]]

			cancelled = frappe.get_all(
				doctype,
				filters=cancelled_filters,
				fields=["name", "party_master", "owner", "creation"],
				limit=100,
			)
			for c in cancelled:
				data.append(
					{
						"party_master": c.party_master,
						"party_name": frappe.db.get_value("Party Master", c.party_master, "party_name")
						or c.party_master,
						"doctype": doctype,
						"voucher_no": c.name,
						"issue_type": "Cancelled (Unamended)",
						"owner": c.owner,
						"creation": c.creation,
					}
				)

	return columns, data
