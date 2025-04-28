# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class PartyMasterSettingsPartyType(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		allowed: DF.Check
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		party_type: DF.Link | None
		reqd: DF.Check
		rule_fieldname: DF.Literal[None]
	# end: auto-generated types
	pass
