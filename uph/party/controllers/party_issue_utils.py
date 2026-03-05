import json
import frappe
from frappe.utils import now_datetime


OPEN_STATUSES = ("Open", "Under Review")
TERMINAL_STATUSES = ("Resolved", "Ignored")
SEVERITY_RANK = {
    "High": 4,
    "Critical": 3,
    "Medium": 2,
    "Low": 1,
}


def get_severity_rank(severity: str | None) -> int:
    if not severity:
        return 0
    return SEVERITY_RANK.get(severity, 0)


def normalize_party_pair(party_1, party_2):
    if party_1 and party_2 and party_1 > party_2:
        return party_2, party_1
    return party_1, party_2


def get_issue_status(
    *,
    party_master,
    issue_type,
    reference_doctype=None,
    reference_name=None,
):
    filters = {
        "party_master": party_master,
        "issue_type": issue_type,
    }
    if reference_doctype and reference_name:
        filters["reference_doctype"] = reference_doctype
        filters["reference_name"] = reference_name

    return frappe.db.get_value(
        "Party Issue",
        filters,
        ["name", "status"],
        as_dict=True,
    )


def create_party_issue_if_missing(
    *,
    party_master,
    issue_type,
    severity,
    source_engine,
    status="Open",
    party_secondary=None,
    score=None,
    reference_doctype=None,
    reference_name=None,
    details=None,
):
    """Create a Party Issue if one doesn't already exist for the given filters.

    For Duplicate issues, pass the second party via
    ``reference_doctype="Party Master"`` and ``reference_name=<party_2>``.
    The legacy ``party_secondary`` kwarg is accepted for backwards
    compatibility and is transparently mapped to reference fields.
    """
    # Legacy compat: map party_secondary → reference fields
    if party_secondary and not reference_name:
        reference_doctype = "Party Master"
        reference_name = party_secondary

    filters = {
        "party_master": party_master,
        "issue_type": issue_type,
        "status": ["in", list(OPEN_STATUSES)],
    }

    if reference_doctype and reference_name:
        filters["reference_doctype"] = reference_doctype
        filters["reference_name"] = reference_name

    existing_doc = frappe.db.get_value(
        "Party Issue",
        filters,
        ["name", "severity", "score", "details_json"],
        as_dict=True,
    )

    new_details_json = (
        json.dumps(details) if isinstance(details, (dict, list)) else details
    )
    new_severity_rank = get_severity_rank(severity)

    if existing_doc:
        updates = {}
        if existing_doc.severity != severity:
            updates["severity"] = severity
            updates["severity_rank"] = new_severity_rank
        elif getattr(existing_doc, "severity_rank", None) != new_severity_rank:
            updates["severity_rank"] = new_severity_rank
        if score is not None and getattr(existing_doc, "score", None) != score:
            updates["score"] = score
        if existing_doc.details_json != new_details_json:
            updates["details_json"] = new_details_json

        if updates:
            frappe.db.set_value("Party Issue", existing_doc.name, updates)

        return existing_doc.name, False

    doc = frappe.get_doc(
        {
            "doctype": "Party Issue",
            "party_master": party_master,
            "issue_type": issue_type,
            "severity": severity,
            "severity_rank": new_severity_rank,
            "status": status,
            "score": score,
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "details_json": new_details_json,
            "source_engine": source_engine,
            "detected_on": now_datetime(),
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name, True
