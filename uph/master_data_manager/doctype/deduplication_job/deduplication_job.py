# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from uph.master_data_manager.run_jobs import run_job


class DeduplicationJob(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from uph.master_data_manager.doctype.deduplication_job_field.deduplication_job_field import DeduplicationJobField

        active: DF.Check
        deduplication_mode: DF.Literal["Fuzzy", "Exact"]
        document_type: DF.Link
        fields: DF.Table[DeduplicationJobField]
        match_threshold: DF.Float
        schedule: DF.Literal["Hourly", "Daily", "Monthly", "Manual"]
        validate_on_form_save: DF.Check
    # end: auto-generated types
    @frappe.whitelist()
    def run_job(self):
        return run_job(self.name)
