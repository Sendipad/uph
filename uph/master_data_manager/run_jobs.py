import frappe
from uph.master_data_manager.deduper import BaseDeduplicationManager


def run_all_active_dedupe_jobs():
    jobs = frappe.get_all("Deduplication Job", filters={"active": 1}, pluck="name")
    for job_name in jobs:
        run_job(job_name)


@frappe.whitelist()
def run_job(job_name):
    """Run deduplication for a single job record by name."""
    job = frappe.get_doc("Deduplication Job", job_name)

    doctype = job.document_type
    fields = [f.fieldname for f in job.fields]
    weights = {f.fieldname: f.weight or 1 for f in job.fields}
    threshold = job.match_threshold or 85
    mode = job.deduplication_mode or "fuzzy"  # Add this field to the job doctype

    manager = BaseDeduplicationManager(
        doctype=doctype, fields=fields, weights=weights, threshold=threshold, mode=mode
    )

    manager.configure_conditions(filters={})  # Or custom filters if needed
    duplicates = manager.find_duplicates()

    for dup in duplicates:
        if not _result_exists(job.name, dup["original"], dup["duplicate"]):
            frappe.get_doc(
                {
                    "doctype": "Deduplication Result",
                    "deduplication_job": job.name,
                    "doctype_name": doctype,
                    "docname_a": dup["original"],
                    "docname_b": dup["duplicate"],
                    "score": dup.get("score", 100),
                    "resolved": 0,
                    "notes": f'{dup["original"]} vs {dup["duplicate"]}',
                }
            ).insert(ignore_permissions=True)


def _result_exists(job_name, a, b):
    return frappe.db.exists(
        "Deduplication Result",
        {"deduplication_job": job_name, "docname_a": a, "docname_b": b, "resolved": 0},
    )


@frappe.whitelist()
def run_deduplication_job(job_name, filters=None):
    job = frappe.get_doc("Deduplication Job", job_name)

    doctype = job.document_type
    fields = [f.fieldname for f in job.fields]
    weights = {f.fieldname: f.weight or 1 for f in job.fields}
    threshold = job.match_threshold or 85
    mode = job.deduplication_mode or "fuzzy"

    manager = BaseDeduplicationManager(
        doctype=doctype, fields=fields, weights=weights, threshold=threshold, mode=mode
    )

    if filters:
        manager.configure_conditions(filters)

    return manager.find_duplicates()
