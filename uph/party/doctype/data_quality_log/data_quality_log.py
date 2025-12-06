# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class DataQualityLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		action_taken: DF.Literal["", "Blocked", "Warned", "Logged"]
		candidates_checked: DF.Int
		document_name: DF.DynamicLink | None
		document_type: DF.Link
		error_message: DF.Text | None
		execution_mode: DF.Literal["", "Single", "Bulk"]
		execution_time_ms: DF.Float
		execution_timestamp: DF.Datetime
		highest_score: DF.Float
		matches_found: DF.JSON | None
		policy: DF.Link
		query_time_ms: DF.Float
		scoring_time_ms: DF.Float
		status: DF.Literal["Completed", "Failed", "Skipped"]
		total_matches: DF.Int
		trigger_type: DF.Literal["", "On Save", "On Submit", "Scheduled", "Manual", "Bulk Scan"]
	# end: auto-generated types

	pass
