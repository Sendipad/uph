# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class RegisteredMethodParameter(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		default_value: DF.Data | None
		description: DF.SmallText | None
		is_context_var: DF.Check
		parameter_name: DF.Data
		parameter_type: DF.Literal["String", "Integer", "Float", "Boolean", "Dict", "List", "DocType", "Any"]
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		required: DF.Check
		target_doctype: DF.Link | None
	# end: auto-generated types
	pass
