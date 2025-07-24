# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class RuleScope(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		apply_filter_json: DF.Code | None
		apply_for_user_role: DF.Link | None
		apply_when_docstatus_is: DF.Literal["Any", "Draft (0)", "Submitted (1)", "Cancelled (2)"]
		apply_when_workflow_state_is: DF.Link | None
		custom_event_name: DF.Data | None
		document_type: DF.Link
		evaluation_event: DF.Literal["Before Insert", "Before Save", "After Save", "Before Submit", "After Submit", "Before Cancel", "After Cancel", "Before Trash", "After Trash", "Custom Event", "On Load", "On Change"]
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
	# end: auto-generated types
	pass
