# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class DeduplicationResult(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		deduplication_job: DF.Link
		docname_a: DF.DynamicLink | None
		docname_b: DF.DynamicLink | None
		document_type: DF.Link
		note: DF.LongText | None
		priority: DF.Literal["High", "Medium", "Low"]
		resolved: DF.Check
		score: DF.Float
	# end: auto-generated types
	pass
