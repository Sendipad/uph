# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

from collections import defaultdict
import frappe
from frappe.model.document import Document
from frappe.utils.caching import redis_cache


class RecordIntegrityRule(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from uph.unified_data_tools.doctype.field_comparison_job_link.field_comparison_job_link import FieldComparisonJobLink

        completed_at: DF.Datetime | None
        document_type: DF.Link
        enabled: DF.Check
        field_comparison_rules: DF.TableMultiSelect[FieldComparisonJobLink]
        filters_json: DF.Code | None
        ignore_cancelled_doc: DF.Check
        reference_doctype: DF.Link | None
        run_mode: DF.Literal["Manual", "Daily", "Weekly", "Monthly", "Real-Time Triggered"]
        started_at: DF.Datetime | None
        status: DF.Literal["Pending", "Queued", "Running", "Completed", "Failed"]
        title: DF.Data | None
        validate_on_event: DF.Literal["", "Before Insert", "Before Save", "Validate", "On Submit", "On Cancel", "On Update After Submit"]
    # end: auto-generated types

    def clear_cache(self):
        get_document_type_run_validate_events.clear_cache()
        return super().clear_cache()


@frappe.whitelist()
@redis_cache()
def get_document_type_run_validate_events():

    jobs = frappe.get_all(
        "Record Integrity Rule",
        filters={"enabled": 1, "validate_on_event": ["!=", ""]},
        fields=["name", "document_type", "validate_on_event"],
    )

    result = defaultdict(lambda: defaultdict(list))

    for job in jobs:
        result[job.document_type][job.validate_on_event].append(job.name)

    # Convert nested defaultdicts to normal dicts before returning
    return {doctype: dict(events) for doctype, events in result.items()}
