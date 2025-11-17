# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class PartyMasterSettingsDocType(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		client_script: DF.Link | None
		document_categories: DF.Literal["", "Selling DocType", "Purchasing DocType", "Dynamic type As Parent", "Dynamic Type As Child", "Employee DocType"]
		document_type: DF.Link
		enabled: DF.Check
		is_dynamic_party_type: DF.Check
		is_system_generated: DF.Check
		parent: DF.Data
		parent_doctype: DF.Link | None
		parentfield: DF.Data
		parenttype: DF.Data
		party_fieldname: DF.Literal[None]
		party_master_custom_field: DF.Link | None
		party_type: DF.Link | None
		party_type_fieldname: DF.Literal[None]
		reqd: DF.Check
		warn_not_submitted_document: DF.Check
	# end: auto-generated types
	pass
