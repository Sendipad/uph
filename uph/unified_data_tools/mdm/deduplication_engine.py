# -----------------------------------------------------------------------------
# Project Name: UPH - Unified Party Hub
# File: deduplication_engine.py
# Description: Implements the DeduplicationEngine for detecting and managing duplicate records using configurable matching rules in the UPH system.
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
from frappe.utils.background_jobs import enqueue

# from frappe.model.document import Document
from uph.unified_data_tools.services.cache import RedisCache
from uph.unified_data_tools.services.matchers import (
    ExactMatcher,
    FuzzyMatcher,
    ChildTableMatcher,
)


class DeduplicationEngine:
    def __init__(self, job):
        if isinstance(job, str):
            job = frappe.get_cached_doc("Deduplication Job", job)
        self.job = job
        self.cache = RedisCache(self.job.document_type)
        self.matchers = self._init_matchers()

    def _init_matchers(self):
        matchers = []
        for rule in self.job.rules:
            matcher_class = self._get_matcher_class(rule)
            matchers.append(matcher_class(rule, self.cache))
        return matchers

    def _get_matcher_class(self, rule):
        if "." in rule.field_path:  # Child table
            return ChildTableMatcher
        elif self.job.deduplication_mode == "Exact":
            return ExactMatcher
        else:
            return FuzzyMatcher

    def compare(self, doc1, doc2):
        """Score between two specific docs using job rules"""
        score = 0
        total_weight = sum(rule.weight for rule in self.job.rules if rule.weight)

        if total_weight <= 0:
            return 0

        for matcher in self.matchers:
            try:
                score += matcher.compare(doc1, doc2) * (
                    matcher.rule.weight / total_weight
                )
            except Exception as e:
                frappe.log_error(
                    f"Matcher error: {e}", f"Rule: {matcher.rule.field_path}"
                )

        return score

    def execute(self):
        """Main execution method"""
        duplicates = []
        processed = set()

        records = self._get_records()
        for i, doc1 in enumerate(records):
            for doc2 in records[i + 1 :]:
                pair_key = self._get_pair_key(doc1, doc2)
                if pair_key not in processed:
                    score = self._compare_docs(doc1, doc2)
                    if score >= self.job.match_threshold:
                        duplicates.append(
                            {
                                "original": doc1.name,
                                "duplicate": doc2.name,
                                "score": score,
                            }
                        )
                    processed.add(pair_key)

        self._store_results(duplicates)
        return duplicates

    def _store_results(self, duplicates):
        document_type = self.job.document_type
        if not document_type:
            frappe.throw("Document Type is not set on Deduplication Job.")

        for dup in duplicates:
            if not self._result_exists(
                self.job.name, dup["original"], dup["duplicate"]
            ):
                frappe.get_doc(
                    {
                        "doctype": "Data Quality Task",
                        "reference_type": "Deduplication Job",
                        "reference_name": self.job.name,
                        "document_type": document_type,  # ✅ important for dynamic link
                        "docname_a": dup["original"],
                        "docname_b": dup["duplicate"],
                        "score": dup["score"],
                        "resolved": 0,
                        "priority": "High",
                        "note": f"{dup['original']} vs {dup['duplicate']}",
                    }
                ).insert(ignore_permissions=True)

    def _get_records(self):
        """Fetch records with selected fields"""
        fields = list(
            set(
                rule.field_path.split(".")[0]
                for rule in self.job.rules
                if not rule.field_path.startswith("items.")
            )
        )

        return frappe.get_all(
            self.job.document_type,
            fields=["name"] + fields,
            limit_page_length=self.job.batch_size or 1000,
        )

    def _compare_docs(self, doc1, doc2):
        """Calculate weighted similarity score"""
        total_weight = sum(rule.weight for rule in self.job.rules)
        if total_weight <= 0:
            return 0

        score = 0
        for matcher in self.matchers:
            try:
                score += matcher.compare(doc1, doc2) * (
                    matcher.rule.weight / total_weight
                )
            except Exception:
                frappe.log_error(f"Failed to compare {matcher.rule.field_path}")

        return score

    def _get_pair_key(self, doc1, doc2):
        return frozenset([doc1.name, doc2.name])

    def _create_duplicate_logs(self, duplicates):
        for dup in duplicates:
            frappe.get_doc(
                {
                    "doctype": "Duplicate Log",
                    "deduplication_job": self.job.name,
                    "original_record": dup["original"],
                    "duplicate_record": dup["duplicate"],
                    "similarity_score": dup["score"],
                }
            ).insert(ignore_permissions=True)

    @classmethod
    def enqueue(cls, job_name):
        enqueue(
            "uph.unified_data_tools.mdm.deduplication_engine.DeduplicationEngine.execute_async",
            job_name=job_name,
            queue="long",
        )

    @classmethod
    def execute_async(cls, job_name):
        cls(job_name).execute()

    def _result_exists(self, job_name, a, b):
        return frappe.db.exists(
            "Data Quality Task",
            {
                "deduplication_job": job_name,
                "docname_a": a,
                "docname_b": b,
                "resolved": 0,
            },
        )
