# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder import Interval
from frappe.query_builder.functions import Now


class DataQualityTask(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        deduplication_job: DF.Link | None
        docname_a: DF.DynamicLink | None
        docname_b: DF.DynamicLink | None
        document_type: DF.Link
        note: DF.LongText | None
        priority: DF.Literal["High", "Medium", "Low"]
        reference_name: DF.DynamicLink | None
        reference_type: DF.Link | None
        resolved: DF.Check
        score: DF.Float
    # end: auto-generated types

    @staticmethod
    def clear_old_logs(days=30):
        table = frappe.qb.DocType("Data Quality Task")
        frappe.db.delete(
            table,
            filters=(
                (table.modified < (Now() - Interval(days=days))) & (table.resolved == 1)
            ),
        )


@frappe.whitelist()
def clear_all_data_quality_tasks():
    frappe.only_for("System Manager")
    frappe.db.truncate("Data Quality Task")
