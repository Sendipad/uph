import json
import frappe
from frappe.utils import now_datetime


OPEN_STATUSES = ("Open", "Under Review")
TERMINAL_STATUSES = ("Resolved", "Ignored")


def normalize_party_pair(party_1, party_2):
    if party_1 and party_2 and party_1 > party_2:
        return party_2, party_1
    return party_1, party_2


def get_issue_status(
    *,
    party,
    issue_type,
    party_secondary=None,
    reference_doctype=None,
    reference_name=None,
):
    filters = {
        "party": party,
        "issue_type": issue_type,
    }
    if party_secondary:
        filters["party_secondary"] = party_secondary
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
    party,
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
    filters = {
        "party": party,
        "issue_type": issue_type,
        "status": ["in", list(OPEN_STATUSES)],
    }

    if party_secondary:
        filters["party_secondary"] = party_secondary
    if reference_doctype and reference_name:
        filters["reference_doctype"] = reference_doctype
        filters["reference_name"] = reference_name

    existing = frappe.db.get_value("Party Issue", filters, "name")
    if existing:
        return existing, False

    doc = frappe.get_doc(
        {
            "doctype": "Party Issue",
            "party": party,
            "party_secondary": party_secondary,
            "issue_type": issue_type,
            "severity": severity,
            "status": status,
            "score": score,
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "details_json": json.dumps(details) if isinstance(details, (dict, list)) else details,
            "source_engine": source_engine,
            "detected_on": now_datetime(),
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name, True
