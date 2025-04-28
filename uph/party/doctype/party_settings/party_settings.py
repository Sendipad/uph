# Copyright (c) 2025, Abdo Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.custom.doctype.custom_field.custom_field import create_custom_field
#from uph.party.utils import 
from frappe import _
class PartySettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from uph.party.doctype.party_master_settings_doctype.party_master_settings_doctype import PartyMasterSettingsDocType

		customer_naming_rule: DF.Literal["Auto Name", "Customer Name", "Naming Series", "Party Master", "Party Master-Default Currency"]
		document_type: DF.Table[PartyMasterSettingsDocType]
		is_numbering_mandatory: DF.Check
		is_party_master_mandatory: DF.Check
		party_master_name: DF.Literal["Party Name", "Auto Name", "Naming Series Prefixed By Parent", "Party Name and Party Type", "Naming Series"]
		supplier_naming_rule: DF.Literal["Auto Name", "Supplier Name", "Naming Series", "Party Master", "Party Master-Default Currency"]
	# end: auto-generated types
	
	def validate_document_type(self):
		if not self.document_type:
			setup_initial_document_type(self, force_reset=True)

		doctypes = set()

		for d in self.document_type:
			# Validate required fields
			if not d.document_type and not d.parent_doctype:
				frappe.throw(_('Document Type and Parent Doctype are Required'))

			dt_meta = frappe.get_meta(d.document_type)
			meta = None  # Meta of the Parent Doctype

			# Handle cases where parent doctype is not provided
			if not d.parent_doctype:
				if dt_meta.istable:
					frappe.throw(_('Parent Doctype is Required at row {0}').format(d.idx))
				d.parent_doctype = d.document_type  # Self-parented

			# If parent and child are different, validate the linkage
			if d.parent_doctype and d.document_type:
				meta = frappe.get_meta(d.parent_doctype)
				has_child = any(
					df.fieldtype == "Table" and df.options == d.document_type
					for df in meta.fields
				)
				if not has_child:
					frappe.throw(_('The Parent Doctype at row {0} has no Child Table pointing to {1}').format(d.idx, _(d.document_type)))

			# Validate party field
			if not d.party_fieldname:
				frappe.throw(_('Party Fieldname is required at the target Document Type at row {0}').format(d.idx))

			field = dt_meta.get_field(d.party_fieldname)
			if not field:
				frappe.throw(_('Party Fieldname "{0}" does not exist in {1} (row {2})').format(d.party_fieldname, d.document_type, d.idx))

			fieldtype = field.fieldtype
			if fieldtype not in ("Link", "Dynamic Link"):
				frappe.throw(_('Party Fieldname at the target Document Type at row {0} must be either a Link or Dynamic Link').format(d.idx))

			# Assign dynamic/static party type fields
			option = field.options
			if fieldtype == "Link":
				d.party_type = option
				d.is_dynamic_party_type = 0
				d.party_type_fieldname = ''
			elif fieldtype == "Dynamic Link":
				d.party_type = None
				d.is_dynamic_party_type = 1
				d.party_type_fieldname = option

			# Check for duplicates
			key = (d.document_type, d.parent_doctype)
			if key in doctypes:
				frappe.throw(_('Duplicate Document Type mapping found at row {0}').format(d.idx))

			doctypes.add(key)

			# Create custom field if not already created


		
	