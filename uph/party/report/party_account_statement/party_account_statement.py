# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt
from collections import defaultdict
from datetime import datetime

import frappe
from uph.party.controllers.queries import (
    get_party_master_parties_db,
    get_leaf_party_master_list_from_any_node,
)
from frappe import _
from frappe.query_builder import DocType, functions as fn

import uph
from frappe.query_builder.custom import ConstantColumn
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)
from uph.party.controllers.queries import get_counts_of_unposted_or_cancelled_vouchers


def execute(filters=None):
    filters = frappe._dict(filters or {})
    validate_set_filters(filters)
    party_master = get_leaf_party_master_list_from_any_node(filters)
    columns = get_columns(filters)
    data = get_data(filters, party_master)
    chart = get_timeline_chart_by_currency(data, from_date=filters.get("from_date"))

    return columns, data, None, chart


def validate_set_filters(filters):
    if not filters.get("company"):
        frappe.throw(_("{0} is mandatory").format(_("Company")))
    if not filters.get("from_date") and not filters.get("to_date"):
        frappe.throw(
            _("{0} and {1} are mandatory").format(
                frappe.bold(_("From Date")), frappe.bold(_("To Date"))
            )
        )
    if filters.from_date > filters.to_date:
        frappe.throw(_("From Date must be before To Date"))
    filters["company_currency"] = frappe.get_cached_value(
        "Company", filters.company, "default_currency"
    )

    display_options = set(filters.get("display_options", []))

    if "show_err" not in display_options:
        err_journals = frappe.db.get_all(
            "Journal Entry",
            filters={
                "company": filters.get("company"),
                "docstatus": 1,
                "voucher_type": (
                    "in",
                    ["Exchange Rate Revaluation", "Exchange Gain Or Loss"],
                ),
            },
            as_list=True,
        )
        if err_journals:
            filters.update({"voucher_no_not_in": [x[0] for x in err_journals]})

    if "show_cr_dr_notes" not in display_options:
        system_generated_cr_dr_journals = frappe.db.get_all(
            "Journal Entry",
            filters={
                "company": filters.get("company"),
                "docstatus": 1,
                "voucher_type": ("in", ["Credit Note", "Debit Note"]),
                "is_system_generated": 1,
            },
            as_list=True,
        )
        if system_generated_cr_dr_journals:
            vouchers_to_ignore = (filters.get("voucher_no_not_in") or []) + [
                x[0] for x in system_generated_cr_dr_journals
            ]
            filters.update({"voucher_no_not_in": vouchers_to_ignore})


def get_timeline_chart_by_currency(data, from_date=None):

    # Structure: currency -> month -> net change
    currency_month_map = defaultdict(lambda: defaultdict(float))
    all_months = set()

    if isinstance(from_date, str):
        from_date = datetime.strptime(from_date, "%Y-%m-%d").date()

    for entry in data:
        currency = entry.get("currency")
        if not currency:
            continue

        raw_date = entry.get("posting_date")
        if not raw_date and entry.get("rowtype") == "Opening Balance":
            raw_date = from_date
        if not raw_date:
            continue

        if isinstance(raw_date, str):
            date_obj = datetime.strptime(raw_date, "%Y-%m-%d").date()
        else:
            date_obj = raw_date

        month = date_obj.strftime("%Y-%m")
        all_months.add(month)

        change = entry.get("debit", 0) - entry.get("credit", 0)
        currency_month_map[currency][month] += change

    sorted_months = sorted(all_months)
    labels = sorted_months

    datasets = []

    for currency, month_map in currency_month_map.items():
        cumulative_balance = 0
        line_values = []
        debit_values = []
        credit_values = []

        for month in sorted_months:
            # Add balance before applying this month's change
            line_values.append(round(cumulative_balance, 2))

            change = month_map.get(month, 0)
            if change >= 0:
                debit_values.append(round(change, 2))
                credit_values.append(0)
            else:
                debit_values.append(0)
                credit_values.append(round(abs(change), 2))

            cumulative_balance += change

        datasets.extend(
            [
                {
                    "name": _("{0} - {1}").format(_(currency), _("Debit")),
                    "values": debit_values,
                    "chartType": "bar",
                },
                {
                    "name": _("{0} - {1}").format(_(currency), _("Credit")),
                    "values": credit_values,
                    "chartType": "bar",
                },
                {
                    "name": _("{0} - {1}").format(_(currency), _("Balance")),
                    "values": line_values,
                    "chartType": "line",
                },
            ]
        )

    return {
        "data": {"labels": labels, "datasets": datasets},
        "type": "axis-mixed",
        "colors": ["#F582E8", "#A64AC9", "#00BFFF"] * len(currency_month_map),
    }


def get_data(filters, party_master):
    data = []

    # Handle party type selection
    party_type = filters.get("party_type", [])
    if not party_type or "All" in party_type:
        filters["party_type"] = uph.get_party_type_list()

    partylist = get_party_master_parties_db(
        party_master, all_roles=False, roles=filters.party_type
    )
    filters.party = [x.party for x in partylist]

    dimension = ["cost_center", "project"] + get_accounting_dimensions(as_list=True)

    opening, entries = query_gl(filters, dimension)

    opening_map = {
        (row.get("party"), row.get("party_type")): row
        for row in opening
        if row.get("type") == "Opening"
    }

    current_totals = {
        (row.get("party"), row.get("party_type")): row
        for row in opening
        if row.get("type") == "Current"
    }

    # Group entries by party

    party_entries = defaultdict(list)
    for entry in entries:
        party_entries[(entry.get("party"), entry.get("party_type"))].append(entry)

    group_by_vn = filters.get("group_by") == "Group by Voucher (Consolidated)"
    display_options = filters.get("display_options") or []
    hide_equal = "Hide Equals Voucher" in display_options
    hide_warning = "Hide Warnings Message" in display_options

    def prepare_entries(key, party_master, balance, balance_in_cc, party_name):
        entries = party_entries.get(key, [])
        if not entries:
            return balance, balance_in_cc

        last_vn = None
        last_index = -1

        for entry in entries:
            debit = entry.get("debit") or 0
            credit = entry.get("credit") or 0
            debit_in_cc = entry.get("debit_in_cc") or 0
            credit_in_cc = entry.get("credit_in_cc") or 0

            if group_by_vn:
                current_vn = entry.get("voucher_no")

                if current_vn == last_vn:
                    row = data[last_index]
                    row["debit"] += debit
                    row["credit"] += credit
                    row["balance"] += debit - credit
                    balance = row["balance"]

                    if filters.get("in_company_currency"):
                        row["debit_in_cc"] += debit_in_cc
                        row["credit_in_cc"] += credit_in_cc
                        row["balance_in_cc"] += debit_in_cc - credit_in_cc
                        balance_in_cc = row["balance_in_cc"]

                    if hide_equal and row["debit"] == row["credit"]:
                        data.pop(last_index)
                        last_index -= 1
                        last_vn = None
                    continue
                else:
                    balance += debit - credit
                    balance_in_cc += debit_in_cc - credit_in_cc
                    new_row = {
                        **entry,
                        "balance": balance,
                        # "voucher_subtype":_(entry.get('voucher_subtype'),context="Voucher Type"),
                        "balance_in_cc": balance_in_cc,
                        "party_master": party_master,
                        "party_name": party_name,
                    }
                    data.append(new_row)
                    last_vn = current_vn
                    last_index = len(data) - 1
            else:
                balance += debit - credit
                balance_in_cc += debit_in_cc - credit_in_cc

                new_row = {
                    **entry,
                    "balance": balance,
                    "balance_in_cc": balance_in_cc,
                    "party_master": party_master,
                    "party_name": party_name,
                }

                if hide_equal and new_row["debit"] == new_row["credit"]:
                    continue

                data.append(new_row)

        return balance, balance_in_cc

    # Collect unposted/cancelled voucher info
    gl_voucher_counts = get_counts_of_unposted_or_cancelled_vouchers(
        filters.get("company"), party_master=None, is_party_gl_effected=1
    )
    unposted_voucher = {}
    for vc in gl_voucher_counts:
        unposted_voucher.setdefault(vc.get("party_master"), []).append(vc)

    last_pm = None
    cached_warning_row = None

    for party in partylist:
        current_pm = party.get("party_master")

        # Flush warning if party_master has changed
        if last_pm and current_pm != last_pm and cached_warning_row:
            data.append(cached_warning_row)
            cached_warning_row = None

        key = (party.get("party"), party.get("party_type"))
        open_row = opening_map.get(key, {})
        open_balance = open_row.get("balance", 0) or 0
        balance_in_cc = open_row.get("balance_in_cc", 0) or 0

        if open_balance != 0 or (
            filters.get("in_company_currency") and balance_in_cc != 0
        ):
            row = {**open_row}
            row.update(
                {
                    "debit" if open_balance > 0 else "credit": abs(open_balance),
                    **party,
                    "remarks": _("Opening Balance"),
                    "rowtype": "Opening Balance",
                    "status": _("Dr") if open_balance > 0 else _("Cr"),
                }
            )
            data.append(row)

        total_balance, total_balance_in_cc = prepare_entries(
            key,
            current_pm,
            balance=open_balance,
            balance_in_cc=balance_in_cc,
            party_name=party.get("party_name"),
        )

        totals = current_totals.get(key)
        if totals:
            data.append(
                {
                    "debit": totals.get("total_debit", 0),
                    "credit": totals.get("total_credit", 0),
                    **party,
                    "remarks": _("Current Period Total"),
                    "current_balance": totals.get("debit", 0) - totals.get("credit", 0),
                    "balance": total_balance,
                    "opening": open_balance,
                    "rowtype": "Current Period Total",
                }
            )

        if total_balance:
            closing_row = {
                **party,
                "credit" if total_balance < 0 else "debit": abs(total_balance),
                "remarks": _("Closing (Opening + Total)"),
                "bold": 1,
                "rowtype": "Closing Balance",
                "status": _("Dr") if total_balance > 0 else _("Cr"),
                "balance": total_balance,
            }
            if filters.get("in_company_currency"):
                closing_row[
                    "credit_in_cc" if total_balance_in_cc < 0 else "debit_in_cc"
                ] = abs(total_balance_in_cc)
            data.append(closing_row)

        # Cache warning for this party_master if it changed
        if current_pm != last_pm and not hide_warning:
            warnings = unposted_voucher.get(current_pm, [])
            if warnings:
                msg = _("On Hold Vouchers:")
                for d in warnings:
                    if d.get("draft_count"):
                        msg += f'{_(d.get("doctype"))}: {d.get("draft_count")} {_("Draft")} '
                    if d.get("cancelled_count"):
                        msg += f'{d.get("cancelled_count")} {_("Cancelled")} '
                cached_warning_row = {
                    "party_name": party.get("party_name"),
                    "party_master": current_pm,
                    "remarks": msg.strip(),
                    "warning": 1,
                }

        last_pm = current_pm

    # Final flush of last warning
    if cached_warning_row:
        data.append(cached_warning_row)

    return data


def query_gl(filters, dimension):

    dimension = ["cost_center", "project"] + get_accounting_dimensions(as_list=True)
    GL = DocType("GL Entry")
    display_options = set(filters.get("display_options") or [])
    conditions = GL.company == filters.get("company")

    from_date = filters.get("from_date")
    period_condition = GL.posting_date.between(from_date, filters.get("to_date"))

    def get_totals_opening_and_current(base_conditions):
        """
        Optimized function to fetch opening and current totals with improved SQL query performance.
        """
        total_fields = [
            GL.party_type,
            GL.party,
            fn.Sum(GL.debit_in_account_currency).as_("total_debit"),
            fn.Sum(GL.credit_in_account_currency).as_("total_credit"),
            (
                fn.Sum(GL.debit_in_account_currency)
                - fn.Sum(GL.credit_in_account_currency)
            ).as_("balance"),
            GL.account_currency.as_("currency"),
        ]

        if filters.get("in_company_currency"):
            total_fields.extend(
                [
                    fn.Sum(GL.debit).as_("debit_in_cc"),
                    fn.Sum(GL.credit).as_("credit_in_cc"),
                    (fn.Sum(GL.debit) - fn.Sum(GL.credit)).as_("balance_in_cc"),
                ]
            )

        # Opening totals query
        opening_query = (
            frappe.qb.from_(GL)
            .select(*total_fields, ConstantColumn("Opening").as_("type"))
            .where(base_conditions & (GL.posting_date < from_date))
            .groupby(GL.party, GL.party_type)
            .having(
                fn.Sum(GL.debit_in_account_currency)
                - fn.Sum(GL.credit_in_account_currency)
                != 0
            )
        )

        # Current totals query
        current_query = (
            frappe.qb.from_(GL)
            .select(*total_fields, ConstantColumn("Current").as_("type"))
            .where(
                base_conditions
                & (GL.posting_date.between(from_date, filters.get("to_date")))
            )
            .groupby(GL.party, GL.party_type)
            .having(
                fn.Sum(GL.debit_in_account_currency)
                - fn.Sum(GL.credit_in_account_currency)
                != 0
            )
        )

        # Combine queries using UNION ALL for better performance
        final_query = opening_query.union_all(current_query)

        return final_query.run(as_dict=True)

    if filters.party:
        conditions &= GL.party.isin(filters.get("party"))
    conditions &= GL.party_type.isin(filters.get("party_type"))

    if "show_cancelled_entries" not in display_options:
        conditions &= GL.is_cancelled == 0

    if filters.get("account"):
        conditions &= GL.account.isin(filters.get("account"))
    for df in dimension:
        if filters.get(df):
            conditions &= GL[df].isin(filters.get(df))

    total_query = get_totals_opening_and_current(conditions)
    entry_condition = conditions
    if filters.get("voucher_no_not_in"):
        entry_condition &= ~GL.voucher_no.isin(filters.get("voucher_no_not_in"))

    fields = [
        GL.name.as_("entry"),
        GL.debit_in_account_currency.as_("debit"),
        GL.credit_in_account_currency.as_("credit"),
        GL.posting_date,
        GL.account,
        GL.remarks,
        GL.account_currency.as_("currency"),
        GL.party_type,
        GL.party,
        GL.voucher_type,
        GL.voucher_subtype,
        GL.voucher_no,
        GL.against_voucher_type,
        GL.against_voucher,
        GL.against,
        GL.is_opening,
    ] + dimension
    if filters.get("in_company_currency"):
        fields.extend([GL.debit.as_("debit_in_cc"), GL.credit.as_("credit_in_cc")])
    if "add_values_in_transaction_currency" in display_options:
        fields.extend(
            [
                GL.debit_in_transaction_currency,
                GL.credit_in_transaction_currency,
                GL.transaction_currency,
            ]
        )

    gl_query = (
        frappe.qb.from_(GL)
        .select(*fields)
        .where((entry_condition) & (period_condition))
    )
    if filters.get("group_by") == "Group by Voucher (Consolidated)":
        gl_query.groupby(GL.party_type, GL.party, GL.voucher_type, GL.voucher_no)
    gl_query = gl_query.orderby(
        "party_type", "party", "posting_date", "voucher_no", "creation"
    )

    return total_query, gl_query.run(as_dict=True)


def get_columns(filters):
    company_currency = filters.get("company_currency", "YER")
    columns = [
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
            "label": _("Currency"),
            "fieldname": "currency",
            "fieldtype": "Data",
            "width": 50,
            "hidden": 0,
        },
        {
            "label": _("Debit"),
            "fieldname": "debit",
            "fieldtype": "Float",
            "width": 110,
            "precision": 2,
        },
        {
            "label": _("Credit"),
            "fieldname": "credit",
            "fieldtype": "Float",
            "width": 110,
            "precision": 2,
        },
        {
            "label": _("The Balance"),
            "fieldname": "balance",
            "fieldtype": "Currency",
            "width": 130,
            "options": "currency",
        },
        {
            "label": _("Party Name"),
            "fieldname": "party_name",
            "fieldtype": "Data",
        },
        {
            "label": _("Party Master"),
            "fieldname": "party_master",
            "fieldtype": "Link",
            "options": "Party Master",
            # "Party Profile" is used in the column definition for the "Account No"
            # field. This indicates that the "Account No" field is linked to the "Party
            # Profile" document in the system.
            "align": "left",
            "width": 100,
        },
        {
            "label": _("Party Type"),
            "fieldname": "party_type",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": _("Party"),
            "fieldname": "party",
            "fieldtype": "Dynamic Link",
            "options": "party_type",
            # "Party Profile" is used in the column definition for the "Account No"
            # field. This indicates that the "Account No" field is linked to the "Party
            # Profile" document in the system.
            "align": "left",
            "width": 100,
        },
        {
            "label": _("Voucher Type"),
            "fieldname": "voucher_type",
            "fieldtype": "Data",
            "width": 100,
        },
    ]
    if filters.get("include_dimensions"):
        columns.append(
            {
                "label": _("Cost Center"),
                "options": "Cost Center",
                "fieldname": "cost_center",
                "width": 100,
            }
        )
        for dim in get_accounting_dimensions(as_list=False):
            columns.append(
                {
                    "label": _(dim.label),
                    "options": dim.label,
                    "fieldname": dim.fieldname,
                    "width": 100,
                }
            )
        columns.append(
            {
                "label": _("Project"),
                "options": "Project",
                "fieldname": "project",
                "width": 100,
            }
        )
    if filters.get("in_company_currency"):
        columns[9:9] = [
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
        ]

    return columns


def string_to_hsl(s):
    # FNV-1a Hash (lightweight, consistent)
    hash_val = 2166136261
    for c in s:
        hash_val ^= ord(c)
        hash_val *= 16777619
        hash_val &= 0xFFFFFFFF  # keep it 32-bit
    hue = hash_val % 360
    return f"hsl({hue}, 60%, 85%)"  # 85% lightness keeps it readable
