# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

import frappe

# from uph.party.doctype.party_master.party_master import fetch_parties_list
# from frappe.query_builder.functions import Locate, Coalesce, Count
from frappe.query_builder.custom import ConstantColumn
from frappe.query_builder import DocType


def execute(filters=None):
    filters = frappe._dict(filters or {})
    data = get_data(filters)
    columns = get_columns()
    return columns, data


def get_data(filters):
    # settings = frappe.get_cached_doc("party Master Settings")
    data = []
    data.extend(
        get_parties_unlinked_to_party_master(
            party_master=filters.get("party_master", None)
        )
    )
    return data


def get_parties_unlinked_to_party_master(
    party_master=None,
    party_name=None,
    fieldmap={"name": "voucher", "party_type": "voucher_type"},
):
    party_types = frappe.get_cached_doc("Party Master Settings").party_types

    if party_master and not party_name:
        party_name = frappe.get_doc("Party Master", party_master).party_name

    words = list(set(filter(None, party_name.lower().split()))) if party_name else []
    queries = []

    for p in party_types:
        Doctype = DocType(p.party_type)
        meta = frappe.get_meta(p.party_type)

        fields = [
            Doctype.name.as_("voucher"),
            Doctype.party_master,
            ConstantColumn(p.party_type).as_("voucher_type"),
        ]

        # Determine field for party_name
        voucher_name_fieldname = f"{p.party_type.lower()}_name"
        party_name_field = None

        if meta.has_field(voucher_name_fieldname):
            party_name_field = getattr(Doctype, voucher_name_fieldname)
        elif meta.has_field("title"):
            party_name_field = Doctype.title

        # Add party name field and placeholder for match_flag
        if party_name_field:
            fields.append(party_name_field.as_("party_name"))
            fields.append(
                ConstantColumn("__MATCH_FLAG__").as_("match_flag")
            )  # placeholder
        else:
            fields.append(ConstantColumn("").as_("party_name"))
            fields.append(ConstantColumn("__MATCH_FLAG__").as_("match_flag"))

        # Currency fields
        if meta.has_field("default_currency"):
            fields.append(Doctype.default_currency.as_("currency"))
        elif meta.has_field("salary_currency"):
            fields.append(Doctype.salary_currency.as_("currency"))
        else:
            fields.append(ConstantColumn("").as_("currency"))

        query = (
            frappe.qb.from_(Doctype)
            .select(*fields)
            .where((Doctype.party_master.isnull()) | (Doctype.party_master == ""))
        )
        queries.append(query)

    if not queries:
        return []

    # Combine all queries using UNION ALL
    combined_query = queries[0]
    for q in queries[1:]:
        combined_query = combined_query.union_all(q)

    query_sql = combined_query.get_sql()

    # If party_name is given, replace placeholder with computed match_flag
    if words:
        escaped_words = [word.replace("'", "''") for word in words]
        conditions = [f"LOWER(party_name) LIKE '%{word}%'" for word in escaped_words]
        combined_condition = " OR ".join(conditions)
        match_flag_sql = f"CASE WHEN {combined_condition} THEN 9999 ELSE 0 END"
        query_sql = query_sql.replace(
            "'__MATCH_FLAG__' AS match_flag", f"{match_flag_sql} AS match_flag"
        )
    else:
        query_sql = query_sql.replace(
            "'__MATCH_FLAG__' AS match_flag", "0 AS match_flag"
        )

    outer_sql = f"SELECT * FROM ({query_sql}) AS X"

    if party_name:
        outer_sql += " ORDER BY match_flag DESC, party_name ASC"
    else:
        outer_sql += " ORDER BY party_name ASC"

    return frappe.db.sql(outer_sql, as_dict=True, debug=True)


"""
    if queries:
        final_query = queries[0]
        for q in queries[1:]:
            final_query = final_query.union_all(q)

        if party_name:
            words = list(set(filter(None, party_name.split())))
            case = Case()
            for word in words:
                case = case.when(
                    frappe.qb.functions.Lower(frappe.qb.Column("voucher_name")).like(
                        f"%{word.lower()}%"
                    ),
                    1,
                )
            final_query = final_query.orderby(case.else_(0), order="desc")
        else:
            final_query = final_query.orderby("voucher_name")

        return final_query.run(as_dict=True)
"""


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
