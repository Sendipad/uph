# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PartyIssue(Document):
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
