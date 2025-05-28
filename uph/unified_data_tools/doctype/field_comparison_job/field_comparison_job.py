# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class FieldComparisonJob(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from uph.unified_data_tools.doctype.field_comparison_job_link.field_comparison_job_link import FieldComparisonJobLink

		completed_at: DF.Datetime | None
		document_type: DF.Link
		enabled: DF.Check
		filters_json: DF.Code | None
		ignore_cancelled_doc: DF.Check
		rules: DF.TableMultiSelect[FieldComparisonJobLink]
		run_mode: DF.Literal["Manual", "Daily", "Weekly", "Monthly", "Real-Time Triggered"]
		started_at: DF.Datetime | None
		status: DF.Literal["Pending", "Queued", "Running", "Completed", "Failed"]
		title: DF.Data | None
		trigger_on_event: DF.Literal["", "Before Insert", "Before Save", "Validate", "On Submit", "On Cancel", "On Update After Submit"]
	# end: auto-generated types
	pass
