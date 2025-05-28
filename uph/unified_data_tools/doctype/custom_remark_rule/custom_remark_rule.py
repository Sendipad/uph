# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CustomRemarkRule(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from uph.unified_data_tools.doctype.custom_remark_rule_condition.custom_remark_rule_condition import CustomRemarkRuleCondition

		conditions: DF.Table[CustomRemarkRuleCondition]
		document_type: DF.Link
		enabled: DF.Check
		priority: DF.Int
		remark_fieldname: DF.Data
		template: DF.HTMLEditor | None
	# end: auto-generated types
	pass
