# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class RuleCondition(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		comparison_strategy: DF.Literal["", "Auto Detect", "String", "Numeric", "Date", "Boolean"]
		condition_id: DF.Data
		custom_scorer: DF.Link | None
		final_left_field_path: DF.Data | None
		final_right_field_path: DF.Data | None
		fuzzy_threshold: DF.Int
		group_operator: DF.Literal["", "AND", "OR"]
		indent: DF.Int
		is_critical: DF.Check
		is_group: DF.Check
		left_field_path: DF.Autocomplete | None
		left_method_parameters: DF.Code | None
		left_specific_doctype: DF.Link | None
		left_value_context_key: DF.Data | None
		left_value_literal: DF.Data | None
		left_value_method: DF.Link | None
		left_value_source: DF.Literal["", "Document Field", "Specific DocType Field", "Literal Value", "Registered Method Result", "Context Variable"]
		logical_operator: DF.Literal["", "AND", "OR"]
		negate_condition: DF.Check
		normalization_profile: DF.Link | None
		normalized_record: DF.Check
		operator: DF.Literal["", "==", "!=", ">", "<", ">=", "<=", "contains", "not contains", "in", "not in", "is set", "is not set", "fuzzy_match", "regex_match", "between", "normalize_field"]
		parent: DF.Data
		parent_condition_id: DF.Data | None
		parentfield: DF.Data
		parenttype: DF.Data
		regex_pattern: DF.Data | None
		right_field_path: DF.Autocomplete | None
		right_method_parameters: DF.Code | None
		right_value_context_key: DF.Data | None
		right_value_literal: DF.Data | None
		right_value_method: DF.Link | None
		right_value_source: DF.Literal["", "Document Field", "Literal Value", "Registered Method Result", "Context Variable"]
		scorer: DF.Literal["", "Levenshtein Distance", "Jaro-Winkler", "Cosine Similarity", "Jaccard Index", "Token Set Ratio", "Partial Ratio", "Soundex", "Metaphone", "Double Metaphone", "Custom Scorer"]
		use_in_filter: DF.Check
		weight: DF.Float
	# end: auto-generated types
	pass
