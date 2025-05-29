# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt
from frappe import _
import frappe
from frappe.model.document import Document
from collections import defaultdict
from frappe.utils.caching import redis_cache
from frappe.utils import (
    cint,
    cstr,
)


class DeduplicationJob(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from uph.unified_data_tools.doctype.deduplication_job_doc_validation_rule.deduplication_job_doc_validation_rule import (
            DeduplicationJobDocValidationRule,
        )
        from uph.unified_data_tools.doctype.deduplication_job_rule.deduplication_job_rule import (
            DeduplicationJobRule,
        )

        batch_size: DF.Int
        deduplication_mode: DF.Literal["Fuzzy", "Exact"]
        document_type: DF.Link
        enable_pass_validation: DF.Check
        enabled: DF.Check
        last_execution: DF.Datetime | None
        match_threshold: DF.Float
        on_doc_rules: DF.Table[DeduplicationJobDocValidationRule]
        rules: DF.Table[DeduplicationJobRule]
        schedule: DF.Literal["Monthly", "Daily", "Hourly", "Manual"]
        similarity_calculation_method: DF.Literal[
            "Ratio", "Partial Ratio", "Token Sort Ratio", "Token Set Ratio"
        ]
        validate_on_save: DF.Check
        validate_threshold_action: DF.Literal["Stop", "Warn"]
    # end: auto-generated types

    def autoname(self):
        name = frappe.scrub(f"de_dup {self.document_type}")
        if (
            frappe.db.get_value("Deduplication Job", name)
            and not frappe.flags.in_import
        ):
            count = frappe.db.sql(
                """select ifnull(MAX(CAST(SUBSTRING_INDEX(name, ' ', -1) AS UNSIGNED)), 0) from tabDeduplication Job
				 where name like %s""",
                f"%{name} - %",
                as_list=1,
            )[0][0]
            count = cint(count) + 1
            name = f"{name}_{cstr(count)}"
        self.name = name

    def validate(self):
        self.validate_on_doc_rule()
        self.validate_doctype_fields()

    def validate_on_doc_rule(self):
        if self.on_doc_rules:

            for rule in self.on_doc_rules:
                if rule.rule == "Not Equal" and not rule.with_fieldname:
                    frappe.throw(
                        _("With Fieldname is Mandatory on {0}").format(rule.idx)
                    )
                if (
                    rule.fieldname
                    and rule.with_fieldname
                    and rule.fieldname == rule.with_fieldname
                ):
                    frappe.throw(
                        _("Fieldname and With Fieldname Can not Be same on {0}").format(
                            rule.idx
                        )
                    )

    def validate_doctype_fields(self):
        meta = frappe.get_meta(self.document_type)
        rowfields = self.get_all_children() or []

        fields = (
            [r.field_path for r in rowfields if r.get("field_path")]
            + [r.fieldname for r in rowfields if r.get("fieldname")]
            + [r.with_fieldname for r in rowfields if r.get("with_fieldname")]
        )
        fields = set(fields)
        not_exist = None
        meta_fields = [f.fieldname for f in meta.fields]
        childs = meta.get_table_fields()
        child_fields = []

        for c in childs:
            child = c.options
            c_meta = frappe.get_meta(child)
            child_fields.extend([f.fieldname for f in c_meta.fields])
        for f in fields:

            if "." in f:
                table_field, child_field = f.split(".", 1)
                if table_field not in meta_fields or child_field not in child_fields:
                    not_exist = f"{table_field} {child_field}"
                    break

            else:
                if f not in meta_fields:
                    not_exist = f"{f}"
                    break

        if not_exist is not None:
            frappe.throw(_("Field {0} Not Exist in DocType").format(not_exist))

    def clear_cache(self):
        get_document_type_run_validate_events().clear_cache()
        return super().clear_cache()

    def get_validation_threshold(self):
        return self.validation_threshold or self.match_threshold or 85

    """
    @frappe.whitelist()
    def run_job(self, docname=None):
        return run_job(self.name, docname)
    """


@frappe.whitelist()
@redis_cache()
def get_document_type_run_validate_events(document_type=None):
    filters = {"enabled": 1, "validate_on_event": ["!=", ""]}
    if document_type:
        filters["document_type"] = document_type

    jobs = frappe.get_all(
        "Deduplication Job",
        filters=filters,
        fields=["name", "document_type", "validate_on_event"],
    )

    result = defaultdict(lambda: defaultdict(list))

    for job in jobs:
        result[job.document_type][job.validate_on_event].append(job.name)

    # Convert nested defaultdicts to normal dicts before returning
    return {doctype: dict(events) for doctype, events in result.items()}

    """
    def find_duplicates_for_doc(self, doc):
        filters = self._build_dynamic_filters(doc)

        self._filters = filters  # used in get_records()

        records = self.get_records()
        doc_record = doc.as_dict()

        if self.deduplication_mode == "Fuzzy":
            normalizer = RedisCache(self.document_type)
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


    """
