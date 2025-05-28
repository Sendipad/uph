import frappe
from uph.unified_data_tools.mdm.deduplication_engine import DeduplicationEngine
from uph.unified_data_tools.mdm.remark_engine import RemarkEngine
from uph.unified_data_tools.mdm.validator import DeduplicationValidator


def run_all_active_dedupe_jobs():
    jobs = frappe.get_all("Deduplication Job", filters={"active": 1}, pluck="name")
    for job_name in jobs:
        enqueue_job(job_name)


@frappe.whitelist()
def enqueue_job(job_name):
    DeduplicationEngine.enqueue(job_name)


@frappe.whitelist()
def run_job(job_name, docname=None):
    job = frappe.get_doc("Deduplication Job", job_name)

    if docname:
        doc = frappe.get_doc(job.document_type, docname)
        validator = DeduplicationValidator(doc, jobs=[job.name])
        result = validator.validate() or {"status": "error"}

        if result.get("status") == "duplicate" and result.get("action") == "Stop":
            # Already thrown in validator
            return result

        return result

    engine = DeduplicationEngine(job)
    return engine.execute()


def _result_exists(job_name, a, b):
    return frappe.db.exists(
        "Data Quality Task",
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

    manager = DeduplicationEngine(
        doctype=doctype, fields=fields, weights=weights, threshold=threshold, mode=mode
    )

    if filters:
        manager.configure_conditions(filters)

    return manager.find_duplicates()


@frappe.whitelist()
def generate_custom_remark(doctype, docname):
    try:
        doc = frappe.get_doc(doctype, docname)
        engine = RemarkEngine(doc=doc)
        remark = engine.generate()

        if not remark:
            frappe.msgprint("No applicable remark found for this document.")
        else:
            frappe.msgprint(f"Remarks: {remark}")
    except Exception as e:
        frappe.log_error(f"Failed to generate remark: {e}", "Custom Remark API")
        frappe.throw("Could not generate remark. Check logs for more info.")
