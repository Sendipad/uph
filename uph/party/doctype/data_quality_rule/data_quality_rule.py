# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DataQualityRule(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from uph.party.doctype.data_quality_rule_condition.data_quality_rule_condition import DataQualityRuleCondition

		category: DF.Literal["", "Deduplication", "Validation", "Data Enrichment"]
		conditions: DF.Table[DataQualityRuleCondition]
		description: DF.TextEditor | None
		document_type: DF.Link
		enabled: DF.Check
		rule_name: DF.Data
	# end: auto-generated types

	def validate(self):
		"""Validation logic for Data Quality Rule."""
		if not self.document_type:
			frappe.throw("Document Type is required")
		
		meta = frappe.get_meta(self.document_type)
		
		# Validate that all condition fields exist in document_type
		for condition in self.conditions:
			field_parts = condition.field.split(".")
			
			if len(field_parts) == 1:
				# Parent field
				if not meta.has_field(condition.field):
					frappe.throw(
						f"Field '{condition.field}' not found in {self.document_type}"
					)
			else:
				# Child table field
				child_table, child_field = field_parts
				if not meta.has_field(child_table):
					frappe.throw(f"Child table '{child_table}' not found in {self.document_type}")
				
				child_meta = frappe.get_meta(meta.get_field(child_table).options)
				if not child_meta.has_field(child_field):
					frappe.throw(
						f"Field '{child_field}' not found in child table '{child_table}'"
					)
			
			# If is_normalized, check normalized field exists
			if condition.is_normalized and condition.check_type == "Fuzzy Match":
				norm_field = f"normalized_{condition.field}"
				if "." not in condition.field and not meta.has_field(norm_field):
					frappe.msgprint(
						f"Warning: {norm_field} not found. Normalization will happen on-the-fly.",
						indicator="orange"
					)
	
	def get_required_fields(self):
		"""Returns list of fields needed for matching."""
		fields = []
		for c in self.conditions:
			fields.append(c.field)
			
			# Add normalized field if using pre-normalized values
			if c.is_normalized and c.check_type == "Fuzzy Match":
				if "." not in c.field:  # Parent field only
					fields.append(f"normalized_{c.field}")
		
		return list(set(fields))
	
	def evaluate(self, doc, candidate):
		"""
		Pure function: Score match between two docs.
		Returns: Float score
		"""
		from uph.controllers.mdm.strategies import calculate_score
		return calculate_score(doc, candidate, self.conditions)
