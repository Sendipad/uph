import frappe
from frappe.utils import add_days
from uph.unified_data_tools.mdm.deduplication_engine import DeduplicationEngine
from uph.unified_data_tools.doctype.deduplication_job.deduplication_job import (
    get_doctype_with_validation_deduplication_jobs,
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
        return get_doctype_with_validation_deduplication_jobs().get(self.doc.doctype)

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


"""class DeduplicationValidator:
    def validate(self, doc):
        if self._should_skip(doc):
            return

        for job in self.active_jobs:
            if self._is_duplicate(doc, job):
                self._handle_duplicate(doc, job)

    def _is_duplicate(self, doc, job):
        existing_docs = self._get_existing_docs(job)
        engine = DeduplicationEngine(job.name)

        for existing in existing_docs:
            if engine.compare(doc, existing) >= job.threshold:
                return True
        return False

    def _get_existing_docs(self, job):
        return frappe.get_all(
            job.document_type,
            filters={"name": ("!=", self.name)},
            limit=job.batch_size or 100,
        )

    def _handle_duplicate(self, doc, job):
        action = job.threshold_action or "Warn"

        if action == "Stop":
            self._block_save(doc, job)
        else:
            self._show_warning(doc, job)

    def _block_save(self, doc, job):
        original = self._find_original_duplicate(doc, job)
        frappe.throw(
            f"Duplicate of {original} detected (Score: {score})",
            title="Duplicate Not Allowed",
        )

    def _show_warning(self, doc, job):
        original = self._find_original_duplicate(doc, job)
        frappe.msgprint(
            f"Possible duplicate of {original}", indicator="orange", alert=True
        )


 class DeduplicationValidator:
    def __init__(self, doctype):
        self.doctype = doctype
        self.cache = RedisCache(doctype)
        self.active_jobs = self._get_active_jobs()

    def validate(self, doc):
        if self._should_skip(doc):
            return

        for job in self.active_jobs:
            engine = self._get_engine(job)
            if engine.is_duplicate(doc):
                self.handle_duplicate(doc, job)

    def _get_active_jobs(self):
        return frappe.get_all(
            "Deduplication Job",
            filters={"document_type": self.doctype, "is_active": 1},
            pluck="name",
        )

    def _should_skip(self, doc):
        return doc.is_new() or frappe.flags.in_import or not self.active_jobs

    def _get_engine(self, job_name):
        job = frappe.get_cached_doc("Deduplication Job", job_name)
        return DeduplicationEngine(job.name)

    def handle_duplicate(self, doc, job):
        if job.threshold_action == "Stop":
            frappe.throw(
                f"Duplicate detected by job: {job.name}", title="Duplicate Record"
            )
        else:
            frappe.msgprint(
                f"Possible duplicate detected by job: {job.name}", indicator="orange"
            ) """
