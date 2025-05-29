# -----------------------------------------------------------------------------
# Project Name: UPH - Unified Party Hub
# File: validate_pm.py
# Description:
#
# Author: Abdo (Sendipad)
# Created: 2025-04-10
# License: GNU General Public License v3.0 (GPL-3.0)
# Repository: https://github.com/Sendipad/uph
#
# Copyright (c) 2025 Abdo (Sendipad)
# This file is part of the UPH project and is released under the GPL-3.0 license.
# See LICENSE file or https://www.gnu.org/licenses/gpl-3.0.en.html for full terms.
# -----------------------------------------------------------------------------


import frappe
from uph.party.utils import (
    get_party_type_party_field_from_doc,
    get_party_field_in_doctype,
    get_transactional_doctype_list_to_add_pm,
    get_party_type_currency_field,
)
from frappe import _


def validate_party_master_journal_entry_account(doc, method):
    if not frappe.get_meta("Journal Entry Account").has_field("party_master"):
        return
    for d in doc.accounts:
        if (
            method == "before_insert"
            and doc.doctype == "Journal Entry"
            and doc.is_system_generated
        ):
            if d.party_type != "" and d.party != "" and d.party_master == "":
                if pm := frappe.db.get_value(d.party_type, d.party, "party_master"):
                    d.party_master = pm
                else:
                    frappe.throw(_("Party Master of {0} is not set").format(d.party))
            continue
        elif d.party != "" and d.party_type != "" and d.party_master != "":
            if d.party_master != frappe.db.get_value(
                d.party_type, d.party, "party_master"
            ):
                frappe.throw(
                    _("Party Master of {0} is not {1}").format(d.party, d.party_master)
                )


def validate_party_master_tx_doctype(doc, method):
    if doc.doctype in get_transactional_doctype_list_to_add_pm:
        return
    if frappe.flags.ignore_party_master_match:
        return
    if doc.doctype == "Journal Entry":
        return validate_party_master_journal_entry_account(doc, method)
    party_type_party_field = get_party_type_party_field_from_doc(doc, value=True)
    if doc.party_master == "":
        frappe.throw(_("Party Master is Mandatory"))
    elif doc.party_master != frappe.db.get_value(
        party_type_party_field.get("party_type"),
        party_type_party_field.get("party"),
        "party_master",
    ):
        frappe.throw(
            _("Party Master of {0} is not {1}").format(
                party_type_party_field.get("party"), doc.party_master
            )
        )


# This is Called from Hooks on Customer,Supplier,Employee,Shareholder
# def append_party_to_party_master(doc):
def assign_party_to_party_master(doc, method=None):
    mandatory_pm = frappe.get_doc("Party Settings").is_party_master_mandatory
    if mandatory_pm == 1:
        if method == "before_insert" and doc.party_master == "":
            frappe.throw(_("Party Master is Mandatory"))
        elif method in ("before_save", "on_change") and doc.party_master == "":
            frappe.throw(_("Party Master is Mandatory"))
        elif (
            not doc.is_new()
            and method in ("before_save", "on_change")
            and doc.party_master
            != frappe.db.get_value(doc.doctype, doc.name, "party_master")
        ):
            if doc.party_master == "":
                frappe.throw(_("Party Master is Mandatory"))
            previouse_pm = frappe.db.get_value(doc.doctype, doc.name, "party_master")
            if previouse_pm is not None and previouse_pm != doc.party_master:
                if frappe.flags.on_party_master_rename:
                    return
                try:
                    change_party_master_on_change_linked_party(
                        doc.doctype, doc, doc.party_master, previouse_pm
                    )
                except Exception as e:
                    doc.log_error(f"Error while updating Party Master for {doc.name}")
    old_pm = frappe.db.get_value(doc.doctype, doc.name, "party_master") or ""
    new_pm = doc.get("party_master", "")
    currency_field = get_party_type_currency_field(doc.doctype)
    fullname = frappe.utils.get_fullname(frappe.session.user)
    if new_pm != old_pm:
        if new_pm != "" and frappe.db.exists(
            doc.doctype,
            {"party_master": new_pm, currency_field: doc.get(currency_field)},
        ):
            frappe.throw(
                _("Party Master {0} has Linked {1} with Currency{2}").format(
                    new_pm, _(doc.doctype), doc.get(currency_field)
                )
            )
        if new_pm != "":
            doc.add_comment(
                "Comment",
                _("{0} Has {1} This {2} To Party Master :{3}").format(
                    frappe.bold(fullname),
                    frappe.bold(_("Assign")),
                    _(doc.doctype),
                    frappe.bold(new_pm),
                ),
            )
            pm = frappe.get_cached_doc("Party Master", new_pm)
            pm.add_comment(
                "Comment",
                _("{0} {1} Has {2} a {3} named {4}").format(
                    frappe.bold(frappe.session.user),
                    frappe.bold(fullname),
                    frappe.bold(_("Assign")),
                    frappe.bold(_(doc.doctype)),
                    frappe.bold(_(doc.name)),
                ),
            )
            pm.save()
            # frappe.db.commit()
        if old_pm != "":
            opm = frappe.get_cached_doc("Party Master", old_pm)
            opm.add_comment(
                "Comment",
                _("{0} {1} Has {2} a {3} named {4}").format(
                    frappe.bold(frappe.session.user),
                    frappe.bold(fullname),
                    frappe.bold(_("Unlinked")),
                    frappe.bold(_(doc.doctype)),
                    frappe.bold(_(doc.name)),
                ),
            )
            opm.save()
    # previouse_pm = frappe.db.get_value(doc.doctype, doc.name, "party_master")
    # set_comments_on_party_master(doc.doctype,doc.name,doc.party_master,previouse_pm)


def change_party_master_on_change_linked_party(
    party_type, party, new_party_master, previouse_party_master, commit=False
):
    frappe.flags.ignore_party_master_match = True
    for d in get_tx_doctype_for_party_type(party_type):
        meta = frappe.get_meta(d)
        if not meta.has_field("party_master"):
            continue
        cancelled_exist = frappe.db.exists(
            d,
            {
                party_field: party,
                party_master: ["!=", new_party_master],
                "docstatus": 2,
            },
        )
        if cancelled_exist:
            doctype = d
            doclist = frappe.get_all(
                d,
                filters={
                    party_field: party,
                    "party_master": ["!=", new_party_master],
                    "docstatus": 2,
                },
                pluck="name",
            )
            query = (
                "UPDATE `tab{0}` SET party_master = {1} WHERE docstatus = '2'"
                and name in {2}.format(doctype, new_party_master, doclist)
            )
            frappe.db.sql(query)
        party_field = get_party_field_in_doctype(d)
        if frappe.db.exists(
            d,
            {
                party_field: party,
                party_master: ["!=", new_party_master],
                "docstatus": ["<", 2],
            },
        ):
            frappe.db.set_value(
                d,
                {
                    party_field: party,
                    party_master: ["!=", new_party_master],
                    docstatus: ["<", 2],
                },
                "party_master",
                new_party_master,
                update_modified=False,
            )
            # dt_list=frappe.get_all(d,filters={party_field:party,'party_master':['!=',new_party_master]},pluck="name")
    if commit:
        frappe.db.commit()
    frappe.flags.ignore_party_master_match = False


def get_tx_doctype_for_party_type(party_type):
    tx_dt = ["Payment Entry", "Journal Entry Account"]
    if party_type == "Customer":
        tx_dt.extend(["Sales Invoice", "Sales Order", "Delivery Note"])
    elif party_type == "Supplier":
        tx_dt.extend(["Purchase Order", "Purchase Receipt", "Purchase Invoice"])
    elif party_type == "Employee":
        if frappe.db.exists("DocType", "Expense Claim"):
            tx_dt.append("Expense Claim")
    return tx_dt


def set_comments_on_party_master(
    party_master, party_type, party, action, previouse_party_master=None
):
    frappe.get_doc(
        {
            "doctype": "Comment",
            "comment_type": "comment",
            "reference_doctype": party_type,
            "referenc_name": party,
            "content": _("Party Master {0} {1} is {2}").format(
                frappe.get_value("Party Master", party_master, "party_name"),
                party_master,
                _(action),
            ),
        }
    ).insert()
    frappe.get_doc(
        {
            "doctype": "Comment",
            "comment_type": "comment",
            "reference_doctype": "Party Master",
            "referenc_name": party_master,
            "content": _("{0} named {1} has been {2}").format(
                _(party_type), party, _("added")
            ),
        }
    ).insert()
    if previouse_party_master:
        frappe.get_doc(
            {
                "doctype": "Comment",
                "comment_type": "comment",
                "reference_doctype": "Party Master",
                "referenc_name": party_master,
                "content": _("{0} named {1} has been {2}").format(
                    _(party_type), party, _("removed")
                ),
            }
        ).insert()


def validate_party_master_in_doc_event(doc, method=None):
    meta = frappe.get_meta(doc.doctype).has_field("party_master")
    is_mandatory = frappe.get_doc("Party Settings").is_party_master_mandatory

    if doc.doctype == "Journal Entry":
        return validate_party_master_journal_entry_account(doc, method)
    if doc.doctype in (frappe.get_all("Party Type", pluck="name")):
        return assign_party_to_party_master(doc, method)
    if meta:
        if not is_mandatory and doc.party_master == "" or method == "before_insert":
            # This will assign Party master based on Party That in doc
            return assign_party_master_based_on_doctype_and_exist(doc, method)

        elif is_mandatory and doc.party_master == "":
            frappe.throw(_("Party Master is Mandatory"))
        if doc.party_master != "":
            return validate_party_match_to_party_master(doc)


# If the Party in doc is Linked To Party Master then assign it
def assign_party_master_based_on_doctype_and_exist(doc, method):
    pt_p = get_party_type_party_field_from_doc(doc, value=True, party_type=None)
    pm = frappe.get_value(pt_p.get("party_type"), pt_p.get("party"), "party_master")
    if pm and doc.party_master == "":
        doc.party_master = pm
        return
    else:
        frappe.msgprint(
            msg=_("{0} - {1} is not Linked to any Party Master").format(
                _(pt_p.get("party_type")), pt_p.get("party")
            ),
            alert=1,
        )


def validate_party_match_to_party_master(doc):
    find_by_fields = [
        "customer",
        "supplier",
        "employee",
        "party",
        "default_customer",
        "default_supplier",
    ]
    party_type = ""
    party_field = ""
    party = ""
    try:
        pt_p = get_party_type_party_field_from_doc(doc, value=True, party_type=None)
        if pt_p:
            party_type = pt_p.get("party_type")
            party = pt_p.get("party")
    except Exception as e:
        for f in find_by_fields:
            if doc.get(f):
                party_field = f
                party = doc.get(f)

                if f == "party":
                    party_type = doc.get("party_type")
                else:
                    party_type = doc.get("party_type")
                break

    if not get_party_type_party_field_from_doc(doc, value=True, party_type=None):

        pt_p = get_party_type_party_field_from_doc(doc, value=True, party_type=None)
    p_doc = frappe.get_cached_doc(pt_p.get("party_type"), pt_p.get("party"))
    if doc.party_master != p_doc.party_master:
        frappe.throw(
            _("Party Master {0} is not the Party Master for {1} - {2}").format(
                doc.get("party_master"), _(pt_p.get("party_type")), pt_p.get("party")
            )
        )
