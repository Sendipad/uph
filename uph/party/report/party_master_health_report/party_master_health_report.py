# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

import frappe

from frappe import _

# from uph.party.doctype.party_master.party_master import fetch_parties_list
# from frappe.query_builder.functions import Count

# from frappe.query_builder.custom import ConstantColumn

# from frappe.query_builder import DocType
from uph.party.controllers.queries import get_unlinked_party


def execute(filters=None):
    filters = frappe._dict(filters or {})
    # Default party types when user did not filter and settings are empty
    if not filters.get("party_type"):
        try:
            settings = frappe.get_cached_doc("Party Master Settings")
            if settings and settings.party_types:
                filters.party_type = [p.party_type for p in settings.party_types]
        except Exception:
            filters.party_type = []
        if not filters.get("party_type"):
            filters.party_type = ["Customer", "Supplier", "Employee"]
    data = get_data(filters)
    columns = get_columns()
    summary_data = get_party_type_summary(filters)

    chart = {
        "data": summary_data["chart_data"],
        "type": "axis-mixed",
        "colors": ["#5cb85c", "#d9534f", "#0275d8"],  # green, red, blue
        "title": _("Linked vs Unlinked Party Stats"),
        "subtitle": "Compared to total records per party type",
        "height": 300,
    }

    return (
        columns,
        data,
        _("This is Old Report Build query Again to get fresh Stats"),
        chart,
    )


def get_data(filters):
    # settings = frappe.get_cached_doc("party Master Settings")
    data = []

    unlinked_parties = get_unlinked_party(filters)
    if unlinked_parties:
        data.extend(unlinked_parties)
    data.extend(get_voucher_stats(filters))
    return data


def get_voucher_stats(filters):
    # voucher = frappe.get_cached_doc("Party Master Settings").document_types
    # parties = get_party_master_parties_db()
    result = []
    return result


@frappe.whitelist()
def get_party_type_summary(filters=None):
    if not filters:
        filters = {}

    result = []
    party_types = filters.get("party_type", None)
    if not party_types:
        party_types = frappe.get_cached_doc("Party Master Settings").party_types
        party_types = [p.party_type for p in party_types] if party_types else []
    if not party_types:
        party_types = ["Customer", "Supplier", "Employee"]
    chart_data = {
        "labels": [],
        "datasets": [
            {"name": "Linked", "values": [], "chartType": "bar"},
            {"name": "Unlinked", "values": [], "chartType": "bar"},
            {"name": "Total", "values": [], "chartType": "line"},
        ],
    }

    total_linked = 0
    total_unlinked = 0
    total_overall = 0

    for pt in party_types:
        party_stats = frappe.db.sql(
            f"""
            SELECT 
                COUNT(*) as total_count,
                COUNT(CASE WHEN party_master IS NOT NULL THEN 1 END) as linked_count,
                COUNT(CASE WHEN party_master IS NULL THEN 1 END) as unlinked_count
            FROM `tab{pt}`
            """,
            as_dict=True,
        )

        if party_stats:
            stats = party_stats[0]
            linked_count = stats.get("linked_count", 0)
            unlinked_count = stats.get("unlinked_count", 0)
            total_count = stats.get("total_count", 0)

            linked_pct = (linked_count / total_count * 100) if total_count else 0
            unlinked_pct = (unlinked_count / total_count * 100) if total_count else 0

            result.append(
                {
                    "party_type": pt,
                    "linked_count": linked_count,
                    "unlinked_count": unlinked_count,
                    "total_count": total_count,
                    "linked_percentage": round(linked_pct, 2),
                    "unlinked_percentage": round(unlinked_pct, 2),
                }
            )

            chart_data["labels"].append(pt)
            chart_data["datasets"][0]["values"].append(linked_count)
            chart_data["datasets"][1]["values"].append(unlinked_count)
            chart_data["datasets"][2]["values"].append(total_count)

            total_linked += linked_count
            total_unlinked += unlinked_count
            total_overall += total_count

    overall_summary = {
        "total_linked": total_linked,
        "total_unlinked": total_unlinked,
        "total": total_overall,
        "linked_percentage": round(
            (total_linked / total_overall * 100) if total_overall else 0, 2
        ),
        "unlinked_percentage": round(
            (total_unlinked / total_overall * 100) if total_overall else 0, 2
        ),
    }

    return {
        "data": result,
        "chart_data": chart_data,
        "summary": overall_summary,
    }


def get_columns():
    return [
        {
            "label": "Party",
            "fieldname": "party",
            "fieldtype": "Dynamic Link",
            "options": "party_type",  # Replace with actual linked DocType
            "width": 180,
        },
        {
            "label": "Voucher",
            "fieldname": "voucher",
            "fieldtype": "Dynamic Link",
            "options": "voucher_type",  # Replace with actual linked DocType
            "width": 180,
        },
        {
            "label": "Voucher Name",
            "fieldname": "voucher_name",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": "Party Master",
            "fieldname": "party_master",
            "fieldtype": "Link",
            "options": "Party Master",
            "width": 200,
        },
        {
            "label": "Voucher Type",
            "fieldname": "voucher_type",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": "Currency",
            "fieldname": "currency",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Party Type",
            "fieldname": "party_type",
            "fieldtype": "Data",
            "width": 130,
        },
    ]
