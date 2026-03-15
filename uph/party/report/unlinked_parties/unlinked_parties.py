# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from uph.party.controllers.cache_utils import get_configured_party_types


def execute(filters=None):
	columns = [
		{
			"label": _("Role DocType"),
			"fieldname": "role_doctype",
			"fieldtype": "Link",
			"options": "DocType",
			"width": 140,
		},
		{
			"label": _("Role Name"),
			"fieldname": "role_name",
			"fieldtype": "Dynamic Link",
			"options": "role_doctype",
			"width": 180,
		},
		{
			"label": _("Party Name"),
			"fieldname": "party_name",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Currency"),
			"fieldname": "currency",
			"fieldtype": "Data",
			"width": 100,
		},
	]

	data = []

	# Get configured types or defaults
	party_types = get_configured_party_types() or ["Customer", "Supplier", "Employee"]

	# Filter by specific DocType if requested
	if filters and filters.get("role_doctype"):
		if filters.get("role_doctype") in party_types:
			party_types = [filters.get("role_doctype")]
		else:
			party_types = []

	for dt in party_types:
		if not frappe.db.exists("DocType", dt):
			continue

		meta = frappe.get_meta(dt)
		if not meta.has_field("party_master"):
			continue

		# Build fields list
		fields = ["name"]
		name_field = None
		for candidate in [
			f"{dt.lower().replace(' ', '_')}_name",
			"employee_name",
			"customer_name",
			"supplier_name",
		]:
			if meta.has_field(candidate):
				name_field = candidate
				break

		if name_field:
			fields.append(name_field)

		if meta.has_field("default_currency"):
			fields.append("default_currency")

		# Get unlinked records
		unlinked = frappe.get_all(
			dt,
			filters={"party_master": ["in", [None, ""]]},
			fields=fields,
			order_by="creation desc",
			limit=500,  # Cap for performance safety in report view
		)

		for row in unlinked:
			data.append(
				{
					"role_doctype": dt,
					"role_name": row.name,
					"party_name": row.get(name_field) if name_field else row.name,
					"currency": row.get("default_currency"),
				}
			)

	return columns, data
