import frappe
from frappe.utils import now_datetime

from uph.party.controllers.party_issue_utils import normalize_party_pair


STATUS_MAP = {
    "Detected": "Open",
    "Dismissed": "Ignored",
    "Merged": "Resolved",
}


def _severity_from_score(score):
    if score is None:
        return "Low"
    try:
        score = float(score)
    except Exception:
        return "Low"
    if score >= 95:
        return "Critical"
    if score >= 90:
        return "High"
    if score >= 80:
        return "Medium"
    return "Low"


def execute():
    if not frappe.db.exists("DocType", "Duplicate Exclusion"):
        return
    if not frappe.db.exists("DocType", "Party Issue"):
        return

    rows = frappe.get_all(
        "Duplicate Exclusion",
        fields=[
            "name",
            "party_1",
            "party_2",
            "status",
            "similarity_score",
            "normalized_name_1",
            "normalized_name_2",
            "detected_on",
            "dismissed_on",
            "dismissed_by",
            "dismissed_reason",
            "creation",
        ],
        limit_page_length=0,
    )

    for row in rows:
        party_1, party_2 = normalize_party_pair(row.party_1, row.party_2)
        status = STATUS_MAP.get(row.status, "Open")

        exists = frappe.db.get_value(
            "Party Issue",
            {
                "party": party_1,
                "party_secondary": party_2,
                "issue_type": "Duplicate",
            },
            "name",
        )
        if exists:
            continue

        details = {
            "source": "Duplicate Exclusion",
            "normalized_name_1": row.normalized_name_1,
            "normalized_name_2": row.normalized_name_2,
            "dismissed_reason": row.dismissed_reason,
            "legacy_name": row.name,
        }

        doc = frappe.get_doc(
            {
                "doctype": "Party Issue",
                "party": party_1,
                "party_secondary": party_2,
                "issue_type": "Duplicate",
                "severity": _severity_from_score(row.similarity_score),
                "status": status,
                "score": row.similarity_score,
                "source_engine": "duplicate_exclusion_migration",
                "details_json": frappe.as_json(details),
                "detected_on": row.detected_on or row.creation or now_datetime(),
            }
        )

        if status in ("Resolved", "Ignored"):
            doc.resolved_on = row.dismissed_on or now_datetime()
            doc.resolved_by = row.dismissed_by

        doc.insert(ignore_permissions=True)
