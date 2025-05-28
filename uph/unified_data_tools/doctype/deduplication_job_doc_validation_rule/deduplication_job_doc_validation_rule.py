# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class DeduplicationJobDocValidationRule(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		fieldname: DF.Autocomplete
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		rule: DF.Literal["", "Not Equal", "Disallow Duplicate in Line"]
		with_fieldname: DF.Autocomplete | None
	# end: auto-generated types
	pass
