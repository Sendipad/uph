# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PartyIssue(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        details_json: DF.LongText | None
        detected_on: DF.Datetime | None
        dismiss_reason: DF.SmallText | None
        issue_type: DF.Literal["Duplicate", "Unlinked", "Health", "Transaction Policy"]
        party_master: DF.Link
        reference_doctype: DF.Link | None
        reference_name: DF.DynamicLink | None
        resolved_by: DF.Link | None
        resolved_on: DF.Datetime | None
        score: DF.Float
        severity: DF.Literal["Low", "Medium", "High", "Critical"]
        source_engine: DF.Data | None
        status: DF.Literal["Open", "Under Review", "Resolved", "Ignored"]
    # end: auto-generated types
    def before_insert(self):
        if not self.detected_on:
            self.detected_on = frappe.utils.now_datetime()

    def validate(self):
        self._set_resolution_metadata()

    def _set_resolution_metadata(self):
        if self.status in ("Resolved", "Ignored"):
            if not self.resolved_on:
                self.resolved_on = frappe.utils.now_datetime()
            if not self.resolved_by:
                self.resolved_by = frappe.session.user
        else:
            # Keep resolved fields intact for audit; do not clear automatically
            pass


def on_doctype_update():
    """Add composite indexes for better query performance"""
    # 1. Performance index for party-specific issue lookup
    frappe.db.add_index(
        "Party Issue", ["party_master", "status", "issue_type"], "idx_party_status_type"
    )

    # 2. Performance index for reference-based lookup
    frappe.db.add_index(
        "Party Issue", ["reference_doctype", "reference_name"], "idx_ref_doc"
    )

    # 3. Dashboard/Priority index
    frappe.db.add_index(
        "Party Issue", ["status", "severity", "detected_on"], "idx_dashboard_order"
    )
