import frappe
from uph.unified_data_tools.mdm.field_comparison_engine import RecordIntegrityEngine
from frappe.utils import now_datetime
from frappe import _


@frappe.whitelist()
def run_job(job_name):
    _run_job(job_name)


def _run_job(job_name):
    # Skip if already queued

    job = frappe.get_doc("Field Comparison Rule", job_name)
    if not frappe.has_permission("Field Comparison Rule", "write", doc=job):
        frappe.throw(_("You have not Permission to run this Job"))

    if job.status in ["Queued", "Runing"]:
        return

    # Mark job as Running
    job.status = "Running"
    job.started_at = now_datetime()
    job.save(ignore_permissions=True)
    frappe.db.commit()

    try:
        # ---- Actual job logic ----
        engine = RecordIntegrityEngine(job)
        engine.run_batch()

        # Mark as Completed
        job.status = "Completed"

    except Exception as e:
        job.status = "Failed"
        frappe.log_error(
            title=f"FieldComparison Job Failed: {job.name}",
            message=frappe.get_traceback(e),
        )

    finally:
        job.completed_at = now_datetime()
        job.save(ignore_permissions=True)
        frappe.db.commit()
