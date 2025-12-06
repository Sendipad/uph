# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DataQualityPolicy(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.core.doctype.has_role.has_role import HasRole
		from frappe.types import DF

		action: DF.Literal["Block", "Warn", "Log Only"]
		apply_to_new_only: DF.Check
		bypass_roles: DF.Table[HasRole]
		custom_message: DF.Text | None
		data_quality_rule: DF.Link
		document_type: DF.Link | None
		enable_blocking: DF.Check
		enabled: DF.Check
		filter_condition: DF.Code | None
		max_candidates: DF.Int
		policy_name: DF.Data
		priority: DF.Int
		schedule: DF.Literal["", "Daily", "Weekly", "Monthly"]
		schedule_time: DF.Time | None
		threshold_score: DF.Float
		trigger: DF.Literal["On Save", "On Submit", "Scheduled"]
	# end: auto-generated types

	def validate(self):
		"""Validation logic for Data Quality Policy."""
		# Auto-fetch document_type from linked rule
		if self.data_quality_rule:
			rule = frappe.get_cached_doc("Data Quality Rule", self.data_quality_rule)
			self.document_type = rule.document_type
	
	def should_execute(self, doc, method):
		"""Check if this policy applies to this document/event."""
		if not self.enabled:
			return False
		
		# Check trigger
		trigger_map = {"validate": "On Save", "on_submit": "On Submit"}
		if trigger_map.get(method) != self.trigger:
			return False
		
		# Check bypass roles
		if self.bypass_roles:
			user_roles = frappe.get_roles()
			bypass_role_list = [r.role for r in self.bypass_roles]
			if any(role in bypass_role_list for role in user_roles):
				return False
		
		# Check filter condition
		if self.filter_condition:
			try:
				if not frappe.safe_eval(self.filter_condition, None, {"doc": doc}):
					return False
			except Exception as e:
				frappe.log_error(f"Filter condition error: {e}", "Data Quality Policy")
				return False
		
		return True
	
	def execute(self, doc):
		"""Execute the policy and return results."""
		rule = frappe.get_cached_doc("Data Quality Rule", self.data_quality_rule)
		
		from uph.controllers.mdm.engine import QualityCheckEngine
		engine = QualityCheckEngine(doc, self, rule)
		
		return engine.find_matches()
