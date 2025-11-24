# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class DataQualityRule(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.core.doctype.has_role.has_role import HasRole
		from frappe.types import DF
		from uph.party.doctype.data_quality_rule_condition.data_quality_rule_condition import DataQualityRuleCondition

		action: DF.Literal["Warn", "Block"]
		bypass_roles: DF.Table[HasRole]
		conditions: DF.Table[DataQualityRuleCondition]
		document_type: DF.Link
		enabled: DF.Check
		filter_condition: DF.Code | None
		rule_name: DF.Data
		threshold_score: DF.Float
		trigger: DF.Literal["On Save", "On Submit"]
	# end: auto-generated types
	pass
