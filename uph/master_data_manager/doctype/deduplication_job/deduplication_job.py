# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from uph.master_data_manager.run_jobs import run_job
from collections import defaultdict
from frappe.utils.caching import redis_cache

from uph.master_data_manager.mdm import RedisNormalizerCache
from rapidfuzz import fuzz


class DeduplicationJob(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from uph.master_data_manager.doctype.deduplication_job_field.deduplication_job_field import DeduplicationJobField

        deduplication_mode: DF.Literal["Fuzzy", "Exact"]
        document_type: DF.Link
        enabled: DF.Check
        fields: DF.Table[DeduplicationJobField]
        match_threshold: DF.Float
        schedule: DF.Literal["Monthly", "Daily", "Hourly", "Manual"]
        validate_on_save: DF.Check
    # end: auto-generated types
    @frappe.whitelist()
    def run_job(self):
        return run_job(self.name)

    def clear_cache(self):
        get_doctype_with_validation_deduplication_jobs.clear_cache()
        super().clear_cache()

    def get_validation_threshold(self):
        return self.validation_threshold or self.match_threshold or 85

    def find_duplicates_for_doc(self, doc):
        filters = self._build_dynamic_filters(doc)

        self._filters = filters  # used in get_records()

        records = self.get_records()
        doc_record = doc.as_dict()

        if self.deduplication_mode == "Fuzzy":
            normalizer = RedisNormalizerCache(self.document_type)
            records = [self._normalize_record(r, normalizer) for r in records]
            doc_record = self._normalize_record(doc_record, normalizer)

        for rec in records:
            if rec["name"] == doc.name:
                continue

            if self.deduplication_mode == "Exact":
                if all(rec.get(f) == doc.get(f) for f in self.get_fieldnames()):
                    return {"duplicate": rec["name"], "score": 100}
            else:
                score = self.score_similarity(doc_record, rec)
                if score >= (self.validation_threshold or self.match_threshold or 85):
                    return {"duplicate": rec["name"], "score": round(score, 2)}

        return None

    def _build_dynamic_filters(self, doc):
        filters = {}
        for f in self.fields:
            if not f.filter:
                continue
            val = doc.get(f.fieldname)
            if not val:
                continue

            op = (f.operator or "=").lower()
            if op == "=":
                filters[f.fieldname] = val
            elif op == "startswith":
                filters[f.fieldname] = ["like", f"{val}%"]
            elif op == "contains":
                filters[f.fieldname] = ["like", f"%{val}%"]
            elif op == "endswith":
                filters[f.fieldname] = ["like", f"%{val}"]
            elif op == "!=":
                filters[f.fieldname] = ["!=", val]
            elif op == "in":
                filters[f.fieldname] = ["in", val.split(",")]
            elif op == "not in":
                filters[f.fieldname] = ["not in", val.split(",")]
            elif op == "date ±1 day":
                from frappe.utils import getdate, add_days

                date_val = getdate(val)
                filters[f.fieldname] = [
                    "between",
                    [add_days(date_val, -1), add_days(date_val, 1)],
                ]

        return filters

    def get_fieldnames(self):
        return [f.fieldname for f in self.fields]

    def get_weights(self):
        return {f.fieldname: f.weight or 1 for f in self.fields}

    def get_records(self):
        fields = ["name"] + self.get_fieldnames()
        return frappe.get_all(self.document_type, fields=fields, filters=self._filters)

    def _normalize_record(self, record, normalizer):
        return {
            f: normalizer.normalize(f, record.get(f)) for f in self.get_fieldnames()
        } | {"name": record["name"]}

    def score_similarity(self, a, b):
        weights = self.get_weights()
        total = sum(weights.values())
        score = sum(
            weights[f] * fuzz.ratio(a.get(f, ""), b.get(f, ""))
            for f in self.get_fieldnames()
        )
        return score / total if total else 0


@frappe.whitelist()
@redis_cache()
def get_doctype_with_validation_deduplication_jobs():
    jobs = frappe.get_all(
        "Deduplication Job",
        filters={"active": 1, "validate_on_form_save": 1},
        fields=["name", "document_type"],
    )

    result = defaultdict(list)
    for job in jobs:
        result[job.document_type].append(job.name)

    return dict(result)
