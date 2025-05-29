# -----------------------------------------------------------------------------
# Project Name: UPH - Unified Party Hub
# File: validator.py
# Description: Contains the DeduplicationValidator class for validating documents against deduplication jobs and handling duplicate detection in the UPH system.
#
# Author: Abdo Ruzaqi(Sendipad)
# Created: 2025-04-10
# License: GNU General Public License v3.0 (GPL-3.0)
# Repository: https://github.com/Sendipad/uph
#
# Copyright (c) 2025 Abdo  Ruzaqi(Sendipad)
# This file is part of the UPH project and is released under the GPL-3.0 license.
# See LICENSE file or https://www.gnu.org/licenses/gpl-3.0.en.html for full terms.
# -----------------------------------------------------------------------------

import frappe
from frappe.utils import add_days
from uph.unified_data_tools.mdm.deduplication_engine import DeduplicationEngine
from uph.unified_data_tools.doctype.deduplication_job.deduplication_job import (
    get_document_type_run_validate_events,
)


class DeduplicationValidator:
    def __init__(self, doc, jobs=None):
        self.doc = doc
        self.active_jobs = jobs or self._get_active_jobs()

    def validate(self):
        if self._should_skip():
            return {"status": "skipped"}

        if not self.active_jobs:
            return {"status": "no_jobs"}

        for job_name in self.active_jobs:
            engine = DeduplicationEngine(job_name)
            job = engine.job

            candidates = self._get_existing_docs(job)
            if not candidates:
                continue

            for existing_doc in candidates:
                score = engine.compare(self.doc, existing_doc)
                if score >= job.match_threshold:
                    return self._handle_duplicate(job, existing_doc, score)

        return {"status": "pass"}  # ✅ Final return if no matches found

    def _get_existing_docs(self, job):
        filters = {
            "name": ["!=", self.doc.name],
            "docstatus": ["<", 2],
        }

        for rule in job.rules:
            if rule.use_in_filter and hasattr(self.doc, rule.field_path):
                value = self.doc.get(rule.field_path)
                if not value:
                    continue

                if (
                    rule.operator == "Within Days"
                    and rule.field_type == "Date"
                    and rule.tolerance
                ):
                    filters[rule.field_path] = [
                        "between",
                        [
                            add_days(value, -rule.tolerance),
                            add_days(value, rule.tolerance),
                        ],
                    ]
                else:
                    filters[rule.field_path] = value

        return [
            frappe.get_doc(job.document_type, d.name)
            for d in frappe.get_all(
                job.document_type,
                filters=filters,
                fields=["name"],
                limit_page_length=job.batch_size or 100,
            )
        ]

    def _get_active_jobs(self):
        return get_document_type_run_validate_events(self.doc.doctype)

    def _should_skip(self):
        return frappe.flags.in_patch or frappe.flags.in_install or not self.active_jobs

    def _handle_duplicate(self, job, match_doc, score):
        action = job.validate_threshold_action or "Warn"
        msg = f"Duplicate of <b>{match_doc.name}</b> (Score: {score:.1f}%) detected by job <b>{job.name}</b>"

        if action == "Stop":
            frappe.throw(msg, title="Duplicate Not Allowed")

        frappe.msgprint(msg, indicator="orange", alert=True)
        return {
            "status": "duplicate",
            "match_doc": match_doc.name,
            "score": score,
            "job": job.name,
            "action": action,
        }
