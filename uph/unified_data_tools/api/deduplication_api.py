import frappe
from uph.unified_data_tools.mdm.validator import DeduplicationValidator
from uph.unified_data_tools.mdm.deduplication_engine import DeduplicationEngine


@frappe.whitelist()
def get_potential_duplicates(job_name, docname):
    job = frappe.get_doc("Deduplication Job", job_name)
    doc = frappe.get_doc(job.document_type, docname)
    validator = DeduplicationValidator(doc, jobs=[job.name])
    candidates = validator._get_existing_docs(job)
    return [d.name for d in candidates]


@frappe.whitelist()
def run_job(job_name, docname=None):
    job = frappe.get_doc("Deduplication Job", job_name)

    if docname:
        from uph.unified_data_tools.mdm.validator import DeduplicationValidator

        doc = frappe.get_doc(job.document_type, docname)
        validator = DeduplicationValidator(doc, jobs=[job.name])
        return validator.validate()
    else:
        engine = DeduplicationEngine(job)
        result = engine.execute()
        return {"status": "success", "duplicates_found": len(result)}
