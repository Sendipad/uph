# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt
from datetime import datetime
from collections import defaultdict

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.utils import today

"""
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
    get_dimension_with_children,
)
"""
from uph.party.controllers.queries import (
    get_party_master_parties_db,
)


def execute(filters=None):
    if not filters:
        frappe.throw(_("Party Master and Company are Mandatory"))
    filters = frappe._dict(filters)
    if not filters.party_master:
        frappe.throw(_("Party Master is Mandatory"))
    parties = get_party_master_parties_db(filters.party_master)
    if not parties:
        return (
            get_columns(filters),
            [],
            _("No Parties linked to this Party Master"),
            None,
        )
    filters["party"] = [p.party for p in parties]
    filters["parties"] = parties
    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_timeline_chart_by_currency(data)
    hide_equal = (
        True
        if filters.get("display_options")
        and "Hide Equals Voucher" in filters.get("display_options")
        else False
    )
    message = _(
        "This report is based on Transaction date (Timeline) If you want to see the transactions in the Party Master, please check the Party Master Transactions Report"
    )
    return columns, data, message, chart


def get_data(filters):
    parties = filters.parties
    party_by_currency = {}
    data = []

    for p in parties:
        currency = p.get("currency")
        p["color"] = string_to_hsl(currency)
        p["balance"] = 0
        party_by_currency[currency] = p
    to_date = filters.get("to_date") or today
    GL = DocType("GL Entry")
    entries = (
        frappe.qb.from_(GL)
        .select(
            GL.name,
            GL.posting_date,
            GL.voucher_no,
            GL.voucher_type,
            GL.remarks,
            GL.party_type,
            GL.party,
            GL.voucher_subtype,
            GL.debit_in_account_currency.as_("debit"),
            GL.credit_in_account_currency.as_("credit"),
            GL.account_currency.as_("currency"),
            GL.transaction_exchange_rate,
            GL.debit.as_("debit_in_cc"),
            GL.credit.as_("credit_in_cc"),
        )
        .where(
            (GL.party.isin(filters.party))
            & (GL.posting_date <= to_date)
            & (GL.company == filters.company)
            & (GL.is_cancelled == 0)
        )
        .orderby(GL.posting_date, GL.creation)
    ).run(as_dict=True)
    from_date = filters.get("from_date")
    if isinstance(from_date, str):
        from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
    balance_in_cc = 0
    opening_balances = {}
    for e in entries:
        currency = e.get("currency")
        party = party_by_currency.get(currency)
        if not party:
            continue
        balance_in_cc += e.get("debit_in_cc", 0) - e.get("credit_in_cc", 0)
        party["balance"] += e.get("debit", 0) - e.get("credit", 0)
        if from_date and e.get("posting_date") < from_date:
            opening_balances[currency] = party["balance"]
            continue
        e["balance"] = party["balance"]
        e["balance_in_cc"] = balance_in_cc
        e["status"] = _("Dr") if e["balance"] > 0 else _("Cr")
        e["color"] = party["color"]
        e["transaction_exchange_rate"] = e.get("transaction_exchange_rate") or 1
        data.append(e)
    for currency, balance in opening_balances.items():
        data.insert(
            0,
            {
                "posting_date": from_date,
                "voucher_no": "Opening",
                "voucher_type": "",
                "remarks": _("Opening Balance"),
                "party_type": "",
                "party": "",
                "voucher_subtype": "",
                "debit": 0,
                "credit": 0,
                "currency": currency,
                "debit_in_cc": 0,
                "credit_in_cc": 0,
                "balance": balance,
                "balance_in_cc": balance_in_cc,
                "status": _("Dr") if balance > 0 else _("Cr"),
                "color": party_by_currency[currency]["color"],
                "transaction_exchange_rate": 1,
            },
        )

    return data


def get_timeline_chart_by_currency(data):
    # Nested dict: {currency: {date: balance_change}}
    currency_date_map = defaultdict(lambda: defaultdict(float))
    all_dates = set()

    for entry in data:
        currency = entry["currency"]
        date = entry["posting_date"]
        all_dates.add(date)
        balance_change = entry.get("balance", 0)
        currency_date_map[currency][date] += balance_change

    sorted_dates = sorted(all_dates)
    labels = [d.strftime("%Y-%m-%d") for d in sorted_dates]

    datasets = []
    for i, (currency, date_map) in enumerate(currency_date_map.items()):
        values = [round(date_map.get(d, 0), 2) for d in sorted_dates]
        datasets.append(
            {
                "name": _(currency),
                "values": values,
                "chartType": (
                    "line" if i % 2 == 0 else "bar"
                ),  # alternate or customize as needed
            }
        )

    return {
        "data": {"labels": labels, "datasets": datasets},
        "type": "axis-mixed",
        "colors": [string_to_hsl(c) for c in currency_date_map.keys()],
    }


def string_to_hsl(s):
    if not s:
        return ""
    s = str(s)
    hash = 0
    for c in s:
        hash = ord(c) + ((hash << 5) - hash)
    hue = hash % 360
    return f"hsl({hue}, 60%, 85%)"  # 85% lightness keeps it readable


def get_columns(filters):
    company_currency = filters.get("company_currency", "YER")

    return [
        {
            "label": "GL Entry",
            "fieldname": "gl_entry",
            "hidden": 1,
        },
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": _("Voucher No"),
            "fieldname": "voucher_no",
            "fieldtype": "Dynamic Link",
            "options": "voucher_type",
            "width": 150,
        },
        {
            "label": _("Currency"),
            "fieldname": "currency",
            "fieldtype": "Data",
            "width": 50,
            "hidden": 0,
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
        },
        {
            "label": _("Debit"),
            "fieldname": "debit",
            "fieldtype": "Currency",
            "width": 130,
            "options": "currency",
        },
        {
            "label": _("Credit"),
            "fieldname": "credit",
            "fieldtype": "Currency",
            "width": 130,
            "options": "currency",
        },
        {
            "label": _("Balance"),
            "fieldname": "balance",
            "fieldtype": "Currency",
            "width": 130,
            "options": "currency",
        },
        {
            "label": _("Exchange Rate"),
            "fieldname": "transaction_exchange_rate",
            "fieldtype": "Float",
            "width": 110,
            "precision": 2,
        },
        {
            "label": _("Debit ({0})").format(company_currency),
            "fieldname": "debit_in_cc",
            "fieldtype": "Float",
            "width": 110,
            "precision": 2,
        },
        {
            "label": _("Credit ({0})").format(company_currency),
            "fieldname": "credit_in_cc",
            "fieldtype": "Float",
            "width": 110,
            "precision": 2,
        },
        {
            "label": _("Balance ({0})").format(company_currency),
            "fieldname": "balance_in_cc",
            "fieldtype": "Currency",
            "width": 130,
            "options": "company_currency",
        },
        {
            "label": _("Voucher Subtype"),
            "fieldname": "voucher_subtype",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": _("Remarks"),
            "fieldname": "remarks",
            "fieldtype": "Data",
            "align": "right",
            "width": 200,
        },
        {
            "label": _("Voucher Type"),
            "fieldname": "voucher_type",
            "fieldtype": "Data",
            "width": 100,
        },
    ]
