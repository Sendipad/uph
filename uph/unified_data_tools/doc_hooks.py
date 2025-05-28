import frappe
from uph.unified_data_tools.mdm import BaseDeduplicationManager
from uph.unified_data_tools.doctype.deduplication_job.deduplication_job import (
    get_doctype_with_validation_deduplication_jobs,
)


def validate_deduplication_on_save(doc, method):
    doctype = doc.doctype
    jobs = get_doctype_with_validation_deduplication_jobs()
    if doctype not in jobs:
        return

    for job_name in jobs.get(doctype):
        job = frappe.get_doc("Deduplication Job", job_name)

        # Check bypass roles
        bypass_roles = [r.role for r in job.get("bypass_roles")]
        if any(frappe.has_role(role) for role in bypass_roles):
            continue

        manager = BaseDeduplicationManager(job)
        manager.configure_conditions({"name": ["!=", doc.name]})
        duplicates = manager.find_duplicates()

        for dup in duplicates:
            if dup["original"] == doc.name or dup["duplicate"] == doc.name:
                frappe.throw(
                    f"Duplicate detected (Score: {dup['score']}%): {dup['original']} vs {dup['duplicate']}"
                )
