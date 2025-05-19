import frappe
from uph.master_data_manager.deduper import BaseDeduplicationManager


def validate_deduplication_on_save(doc, method):
    jobs = frappe.get_all(
        "Deduplication Job",
        filters={"document_type": doc.doctype, "validate_on_form_save": 1, "active": 1},
    )

    for job_data in jobs:
        job = frappe.get_doc("Deduplication Job", job_data.name)

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
