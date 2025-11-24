# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt
from collections import defaultdict, Counter
from copy import copy

import frappe
from uph.controllers.queries import (
    get_party_master_parties_db,
    get_leaf_party_master_list_from_any_node,
)
from frappe import _
from frappe.query_builder import DocType, functions as fn

"""
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
    get_dimension_with_children,
)
"""


def execute(filters=None):
    filters = frappe._dict(filters or {})
    filters["company_currency"] = (
        frappe.get_cached_value("Company", filters.company, "default_currency") or None
    )
    build_filters(filters)
    data, fields = get_data(filters)
    columns = get_columns(fields, filters)
    return columns, data


def build_filters(filters):
    if filters.party_master:
        filters["party_master"] = get_leaf_party_master_list_from_any_node(filters)
    filters["parties"] = get_party_master_parties_db(filters.party_master)


def get_data(filters):
    data = []

    arrange_balances = filters.arrange_balances
    columns = None if arrange_balances != "Horizontal" else []
    parties = filters.parties or None
    GL = DocType("GL Entry")
    where_conditions = (GL.company == filters.get("company")) & (GL.is_cancelled == 0)

    if parties:
        in_parties = [p.get("party") for p in parties]
        where_conditions &= GL.party.isin(in_parties)
    elif not parties:
        where_conditions &= GL.party.isnotnull()
    fields = [
        GL.party,
        GL.party_type,
        GL.account_currency.as_("currency"),
        (
            (
                fn.Sum(GL.debit_in_account_currency)
                - fn.Sum(GL.credit_in_account_currency)
            ).as_("balance")
        ),
        fn.Max(GL.posting_date).as_("posting_date"),
    ]
    if filters.in_company_currency:
        fields.append(((fn.Sum(GL.debit) - fn.Sum(GL.credit)).as_("balance_in_cc")))
    balances = (
        frappe.qb.from_(GL)
        .select(
            *fields,
        )
        .where(where_conditions)
        .groupby(GL.party, GL.party_type)
    ).run(as_dict=True)
    if balances and not filters.show_zero_balance:
        balances = [b for b in balances if b.get("balance", 0) != 0]
    if arrange_balances == "Horizontal" and balances:
        currency_list = [b.get("currency") for b in balances if b.get("currency")]
        currency_freq = Counter(currency_list)
        columns = [currency for currency, _ in currency_freq.most_common()]
    party_entries = {
        (entry.get("party_type"), entry.get("party")): entry for entry in balances
    }
    pm_entries = defaultdict(list)
    for p in parties:
        key = (p.get("party_type"), p.get("party"))

        if key in party_entries:
            pm_entries[(p.get("party_master"), p.get("party_type"))].append(
                party_entries.get(key)
            )

    party_master_details = get_party_master_informations_as_dict(filters)

    for (pm, party_type), entries in pm_entries.items():
        pm_detail = party_master_details.get(pm)
        if arrange_balances != "Horizontal":
            for e in entries:
                e.update(pm_detail)
                data.append(e)
        elif arrange_balances == "Horizontal":
            pm_dict = copy(pm_detail)
            pm_dict["party_type"] = party_type
            posting_date = []
            balance_in_cc = 0
            for e in entries:
                currency = e.get("currency")
                pm_dict[currency] = e.get("balance")
                if filters.in_company_currency:
                    balance_in_cc += e.get("balance_in_cc")
                if e.get("posting_date"):
                    posting_date.append(
                        "{0} : {1}".format(_(currency), e.get("posting_date"))
                    )
            pm_dict["posting_date"] = ", ".join(posting_date)
            if filters.in_company_currency:
                pm_dict["balance_in_cc"] = balance_in_cc
            data.append(pm_dict)

    return data, columns


def get_party_master_informations_as_dict(filters):
    PM = DocType("Party Master")
    where_cond = PM.is_group == 0
    if filters.get("party_master"):
        where_cond &= PM.name.isin(filters.get("party_master"))

    party_master = (
        frappe.qb.from_(PM)
        .select(
            PM.name.as_("party_master"),
            PM.party_name,
            PM.status,
            PM.mobile_no,
            PM.territory,
            PM.party_type_group,
            PM.party_details,
        )
        .where(where_cond)
    ).run(as_dict=True)
    return {pm.get("party_master"): pm for pm in party_master}


def get_columns(fields, filters):
    columns = [
        {"fieldname": "party_type", "label": _("Party Type"), "fieldtytpe": "Data"},
        {
            "fieldname": "party_master",
            "fieldtype": "Link",
            "options": "Party Master",
            "label": _("Party Master"),
        },
        {
            "fieldname": "party_name",
            "fieldtype": "Data",
            "label": _("Party Name"),
            "width": 200,
        },
    ]
    if fields:

        for df in fields:
            columns.append(
                {
                    "fieldname": df,
                    "label": _("Balance ({0})").format(_(df)),
                    "fieldtype": "Currency",
                    "options": df,
                }
            )
    elif not fields:
        columns.extend(
            [
                {
                    "fieldname": "balance",
                    "label": _("Balance"),
                    "fieldtype": "Currency",
                    "options": "currency",
                },
                {
                    "fieldname": "currency",
                    "label": _("Currency"),
                    "fieldtype": "Link",
                    "options": "Currency",
                },
            ]
        )

    if filters.in_company_currency:
        company_currency = filters.company_currency
        columns.append(
            {
                "fieldname": "balance_in_cc",
                "label": _("Balance ({0})").format(_(company_currency)),
                "fieldtype": "Currency",
                "options": company_currency,
            }
        )
    return columns + [
        {"fieldname": "mobile_no", "fieldtype": "Data", "label": _("Mobile No")},
        {
            "fieldname": "posting_date",
            "fieldtype": "Data",
            "label": _("Latest Posting Date"),
        },
        {"fieldname": "status", "fieldtype": "Data", "label": _("Status")},
        {"fieldname": "territory", "fieldtype": "Data", "label": _("Territory")},
        {
            "fieldname": "party_type_group",
            "fieldtype": "Data",
            "label": _("Party Type Group"),
        },
        {
            "fieldname": "party_details",
            "fieldtype": "Text Editor",
            "label": _("Party Details"),
        },
    ]
