# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from uph.party.controllers.queries import (
    get_party_master_parties,
    get_party_master_parties_db,
)
from frappe import _
from frappe.query_builder import Criterion, CustomFunction, DocType, functions as fn
from frappe import qb, scrub
from frappe.query_builder.functions import Concat, Locate, Sum, Coalesce, Count
from frappe.utils import nowdate, today, unique, add_months
import uph
from frappe.query_builder.custom import ConstantColumn
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
    get_dimension_with_children,
)


def execute(filters=None):
    filters = frappe._dict(filters or {})
    company_currency=frappe.get_cached_value(
        "Company", filters.company, "default_currency"
    ) or None        
    fields, data = get_data(filters)
    columns = get_columns(fields, company_currency)
    return columns, data

def get_data(filters):
    GL=DocType('GL Entry')

def get_columns(fields, company_currency):
    columns = [
        {"fieldname": "party_type", "label": _("Party Type"), "fieldtytpe": "Data"},
        {
            "fieldname": "party_master",
            "fieldtype": "Link",
            "options": "Party Master",
            "label": _("Party Master"),
        },
        {"fieldname": "party_name", "fieldtype": "Data", "label": _("Party Name")},
    ]
    
    for df in fields:
        columns.append(
            {
                "fieldname": df,
                "label": _("Balance ({0})").format(_(df)),
                "fieldtype": "Currency",
                "options": df,
            }
        )
        
    if company_currency:
            columns.append(   {
                "fieldname": "balance_in_cc",
                "label": _("Balance ({0})").format(_(company_currency)),
                "fieldtype": "Link",
                "options": "Currency",
            })
