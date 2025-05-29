import frappe
from frappe import _
from uph.unified_data_tools.mdm import (
    DeduplicationEngine,
    FieldComparisonEngine,
    # RemarkEngine
)


def run_deduplication_job_on_doc(doc, method):
    """
    Runs deduplication validation for a given document based on configured jobs and the triggered method.

    - Skips validation if the document type has no jobs or the current method is not listed.
    - Skips validation if the current user has a matching bypass role.
    - Raises a validation error if duplicates are found.

    Args:
        doc: The Frappe document object being validated.
        method: The event (e.g. 'before_save', 'on_submit').
    """
    from uph.unified_data_tools.doctype.deduplication_job.deduplication_job import (
        get_document_type_run_validate_events,
    )

    doctype = doc.doctype
    jobs = get_document_type_run_validate_events() or {}
    if doctype not in jobs or method not in jobs[doctype]:
        return

    for job_name in jobs[doctype][method]:
        job = frappe.get_doc("Deduplication Job", job_name)

        # Skip if current user has a bypass role
        bypass_roles = [r.role for r in job.get("bypass_roles")]
        if any(frappe.has_role(role) for role in bypass_roles):
            continue

        manager = DeduplicationEngine(job)
        manager.configure_conditions({"name": ["!=", doc.name]})
        duplicates = manager.find_duplicates()

        for dup in duplicates:
            if dup["original"] == doc.name or dup["duplicate"] == doc.name:
                frappe.throw(
                    _("Duplicate detected (Score: {0}%): {1} vs {2}").format(
                        dup["score"], dup["original"], dup["duplicate"]
                    ),
                    title=_("Deduplication Error"),
                )


def run_field_comparison_job_on_doc(doc, method):
    """
    Runs field comparison validation for a given document using preconfigured jobs.

    - Skips if no job is found for the document type and method.
    - Raises a validation error listing the violated field rules.

    Args:
        doc: The Frappe document object being validated.
        method: The event (e.g. 'before_save', 'on_submit').
    """
    from uph.unified_data_tools.doctype.field_comparison_job.field_comparison_job import (
        get_document_type_run_validate_events,
    )

    doctype = doc.doctype  # ✅ fixed typo here
    jobs = get_document_type_run_validate_events() or {}
    if doctype not in jobs or method not in jobs[doctype]:
        return

    for job_name in jobs[doctype][method]:
        job = frappe.get_doc("Field Comparison Job", job_name)
        manager = FieldComparisonEngine(job)
        result = manager.validate_document(doc)
        if result:
            frappe.throw(
                _("Field Comparison Rule Violations: {0}").format(" ,".join(result)),
                title=_("Field Violation Error"),
            )


def generate_custom_remarks_on_doc(doc, method):
    return
