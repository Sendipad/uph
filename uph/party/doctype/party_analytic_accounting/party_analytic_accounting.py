# Copyright (c) 2024, Abdo Ruzaqi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class PartyAnalyticAccounting(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		analytic_name: DF.Data
		enabled: DF.Check
		is_default: DF.Check
		party: DF.DynamicLink
		party_acount: DF.Link | None
		party_master: DF.Link
		party_type: DF.Link
	# end: auto-generated types
	pass
