"""`(Party Master )`
This is a controller functions to Validate Party Master,Validate Or fetch Party Master on Transactional Docs,
As well it will validate Party Analytic Accounting which is a Dimension Accounting
Meanwhile it will Create the required Custom Field on Some ERPNext Doctype
Beside It Will reflect the Change of set Party Master on Party Type Doctype

"""

from collections import defaultdict

import frappe
import redis
from frappe.utils import cstr

import json
from uph.party.utils import get_mapped_fieldnames
from frappe.utils.caching import redis_cache
from pypika.functions import Coalesce, Sum

from frappe import _, scrub
from frappe.utils.nestedset import NestedSet
from frappe.contacts.address_and_contact import (
    delete_contact_and_address,
    load_address_and_contact,
)
from erpnext.accounts.party import (
    get_dashboard_info,
    validate_party_accounts,
    add_party_account,
    get_party_gle_account,
    get_party_gle_currency,
    get_party_account,
)  # noqa
from frappe import qb, scrub
from frappe.query_builder import Criterion, DocType, Case
from frappe.query_builder.functions import Concat, Locate, Sum
from pypika import Order, CustomFunction
from functools import reduce
from frappe.query_builder.custom import ConstantColumn
from frappe.query_builder.functions import Count, Sum
from frappe.utils.caching import redis_cache
from uph.party.boot import get_pm_doctypes
import uph
from frappe import _

# from uph.party.doctype.party_master_settings.party_master_settings import get_doctypes_functional_fields_mapping_as_dict,get_document_type_mapping_with_party_master,get_party_type_validation_rule
from uph.party.controllers.queries import get_party_master_parties


###################### Caching##############################################
def on_update_document_types_clear_cache():
    get_pm_doctypes.clear_cache()
    get_doctypes_functional_fields_mapping_as_dict.clear_cache()


@redis_cache()
def get_doctypes_functional_fields_mapping_as_dict():
    doctypes = frappe.db.get_all(
        "Party Master Settings DocType",
        filters={"parenttype": "Party Master Settings"},
        fields=[
            "document_type",
            "parent_doctype",
            "is_dynamic_party_type",
            "reqd",
            "party_fieldname",
            "party_type_fieldname",
            "party_type",
            "party_type_fieldname",
        ],
    )
    docs = {}
    for d in doctypes:
        doctype = d.get("parent_doctype")
        document_type = d.get("document_type")
        meta = frappe.get_meta(doctype)
        if not meta.issingle:
            docs.update({doctype: d})
            if doctype != document_type:
                docs.update({document_type: d})
    return docs


def get_document_type_mapping_with_party_master(document_type):
    def generator():
        docs = get_doctypes_functional_fields_mapping_as_dict()
        if document_type in docs:
            return docs[document_type]
        for v in docs.values():
            if v.get("document_type") == document_type:
                return v
        frappe.db.get_value(
            "Party Master Settings DocType",
            {"parenttype": "Party Master Settings", "document_type": document_type},
            fields=[
                "document_type",
                "parent_doctype",
                "is_dynamic_party_type",
                "reqd",
                "party_fieldname",
                "party_type_fieldname",
                "party_type",
                "party_type_fieldname",
            ],
            as_dict=1,
        )

    return frappe.local_cache("_pm_document_type_maps", document_type, generator)


def get_party_type_validation_rule(party_type):
    def generator():
        return frappe.db.get_value(
            "Party Master Settings Party Type",
            {"party_type": party_type},
            ["party_type", "reqd", "allowed", "rule_fieldname"],
            as_dict=1,
        )

    return frappe.local_cache("party_type_validation_rule", party_type, generator)


################End Cache #################
""" 
Here is the Master validation function
    
    
"""


def validate_party_master_on_document_types(doc, method=None):
    doctype = doc.doctype
    mapping = get_doctypes_functional_fields_mapping_as_dict()
    if (
        frappe.flags.in_patch
        or frappe.flags.in_install
        or frappe.flags.in_migrate
        or frappe.flags.in_import
        or frappe.flags.in_setup_wizard
        or doc.doctype not in mapping
    ):
        return
    parent_meta = frappe.get_meta(doc.doctype)
    if parent_meta.issingle:
        return
    mapping = mapping.get(doc.doctype)
    reqd = mapping.get("reqd")
    party_fieldname = mapping.get("party_fieldname")
    party_type_fieldname = mapping.get("party_type_fieldname")
    meta = frappe.get_meta(mapping.get("document_type"))
    field = meta.get_field(party_fieldname)
    fetch_if_not_exist = True if not field.get("reqd") else False

    ischild = mapping.get("document_type") != doc.doctype
    alert_msg = []

    def validate(d):
        party_type = mapping.get("party_type") or d.get(party_type_fieldname)
        party = d.get(party_fieldname)
        party_master = d.get("party_master")
        new_party_master = frappe.db.get_value(party_type, party, "party_master")
        if ischild or fetch_if_not_exist and (not party_type and not party):
            return
        if party and party_type:
            if (
                not party_master or party_master != new_party_master
            ) and fetch_if_not_exist:
                d.party_master = new_party_master
                alert_msg.append(
                    _("Party Master {0} has been set to {1} automatically").format(
                        new_party_master if not None else _("Un Set"), d.doctype
                    )
                )
                return
            if not party_master or party_master != new_party_master:
                frappe.throw(
                    _(
                        "Party Master is Mandatory Or Maybe this is Not the corrected Party Master for {0}"
                    ).format(party)
                )

    if ischild:
        docs = doc.get_all_children()
        docs = [d for d in docs if d.get("doctype") == mapping.get("document_type")]
        for d in docs:
            validate(d)
        return
    validate(doc)
    if alert_msg:
        for msg in alert_msg:
            frappe.msgprint(title=_("Party Master Reset"), msg=msg, alert=1)
    return



def validate_party_master_on_target_party_type(doc, method):
    if (
        frappe.flags.in_patch
        or frappe.flags.in_install
        or frappe.flags.in_migrate
        #or frappe.flags.in_import
        or frappe.flags.in_setup_wizard
        or doc.doctype not in uph.get_party_type_list()
    ):
        return
    party_type_rule = get_party_type_validation_rule(doc.doctype)
    old_doc = doc.get_doc_before_save()
    old_party_master = old_doc.get("party_master") if old_doc else None
    is_default_for_party_master=doc.is_default_for_party_master
    old_is_default_for_party_master=old_doc.get('is_default_for_party_master') if old_doc else None
    if  doc.party_master and is_default_for_party_master!=old_is_default_for_party_master:
        if is_default_for_party_master:
            reset_default_on_party_master(doc.name,doc.doctype,doc.party_master)

        frappe.cache.hdel(uph.make_key("Party Master.parties"), doc.party_master)

    if doc.party_master and old_party_master == doc.party_master:
        return
    if (
        doc.party_master
        and not frappe.db.exists("Party Master", doc.party_master)
        or not is_valide_party_master_to_party(doc.party_master, doc.doctype)
    ):
        frappe.throw(
            _(
                "Party Master {0} Could be not Exists or is group or has not Role of {1} or not enabled"
            ).format(doc.party_master, doc.doctype)
        )
    if not doc.party_master and party_type_rule.get("reqd"):
        frappe.throw(
            _(
                "Party Master is Mandatory for {0} <br> You can Check Mandatory at Party Master Settings"
            ).format(_(doc.doctype))
        )
    party_master = doc.party_master
    filters = {"party_master": ["=",party_master],
               "name":["!=",doc.name]
               }
    rule_fieldname = get_party_type_validation_rule(doc.doctype).get("rule_fieldname")
    if rule_fieldname:
        filters.update({rule_fieldname: ["=",doc.get(rule_fieldname)]})
    if frappe.db.exists(doc.doctype, filters):
        frappe.throw(
            title=_("Duplicate Exists"),
            msg=_("Party Master {0} has a Party {1} with {2}").format(
                party_master,
                frappe.get_doc(doc.doctype,filters).name,
                doc.get(rule_fieldname) if rule_fieldname else "",
            ),
        )

    if method == "before_save":
        if party_master:
            frappe.cache.hdel(uph.make_key("Party Master.parties"), doc.party_master)

        

        if doc.get("party_master") != old_party_master:
            if old_party_master is not None:
                frappe.cache.hdel(uph.make_key("Party Master.parties"), old_party_master)

            frappe.enqueue(
                on_change_party_master_update_transactional_document_types,
                party=doc,
                queue="short",
                enqueue_after_commit=True,
            )

    if method=="on_trash" and doc.party_master:
        pm=frappe.get_doc('Party Master',doc.party_master)
        pm.add_comment("Comment",_("Party : {0} Has been deleted").format(doc.name))
        frappe.cache.hdel(uph.make_key("Party Master.parties"), doc.party_master)

def is_valide_party_master_to_party(party_master, role):
    if isinstance(party_master, str):
        party_master = frappe.get_cached_doc("Party Master", party_master)
    if party_master.is_group or party_master.disabled:
        return False
    roles = [x.get("party_type_role") for x in party_master.get("roles")]
    if party_master.party_type != role and role not in roles:
        return False
    return True


def reset_default_on_party_master(party,party_type,party_master):
    defaults = frappe.get_list(
        party_type,
        filters={"party_master": party_master, "is_default_for_party_master": 1},
        fields=["name", "is_default_for_party_master"],
    )
    if defaults:
        for d in defaults:
            if d.is_default_for_party_master and d.name != party:
                doc = frappe.get_doc(party_type, d.name)
                doc.db_set("is_default_for_party_master", 0)


def run_sync_party_master_change_queue():
    if not getattr(frappe.local, "_party_to_pm_queue", None):
        return
    local = frappe.local.get("_party_to_pm_queue")
    pm = []
    old = local.get("old_party_master")
    new = local.get("new_party_master")
    if old:
        pm.append(old)
    if new:
        pm.append(new)
        pm.append(old)
    if new:
        pm.append(new)
    if pm:
        uph.update_cached_party_master_parties(pm)
    party_type = local.get("party_type")
    if local.get("is_new"):
        return
    party_name = local.get("party")
    doc = frappe.get_doc(party_type, party_name)

    """ 
    party_names=[local.get('party')]
    if not party_name and party_type:
        party_name=frappe.db.get_all(party_type,filters={'party_master':new},pluck='name')
    for p in party_name:
        doc=frappe.get_doc(party_type,p)
        frappe.enqueue(update_transactional_docs, party_doc=doc, queue="short")
    """


def on_change_party_master_update_transactional_document_types(party, commit=True):
    changes = []
    party_master = party.get("party_master")
    doctypes = get_doctypes_functional_fields_mapping_as_dict()
    docsets = set(d.get("document_type") for d in doctypes.values())

    for doctype in docsets:
        mapping = get_document_type_mapping_with_party_master(doctype)
        if not mapping:
            continue
        party_fieldname = mapping.get("party_fieldname")
        party_type = mapping.get("party_type", None)
        party_type_fieldname = mapping.get("party_type_fieldname", None)
        if not party_fieldname:
            continue
        count = _update_party_master_field_on_exists_transactional_document_types(
            doctype=doctype,
            party_fieldname=party_fieldname,
            party=party.name,
            party_master=party_master,
            party_type=party_type,
            party_type_fieldname=party_type_fieldname,
        )
        if count:
            changes.append(frappe._("{0} Count: {1}").format(frappe._(doctype), count))
    if changes:
        content = ", ".join(changes)

        party.add_comment(
            "Comment", f"🎯 {content} Assigned to → {party_master or 'NULL'}"
        )
        party.save()

        if party_master:
            doc = frappe.get_doc("Party Master", party_master)
            doc.add_comment("Comment", f"{party.name} Assigned and Updated: {content}")
            doc.save()
    if commit:
        frappe.db.commit()

def _update_party_master_field_on_exists_transactional_document_types(
    doctype,
    party_fieldname,
    party,
    party_master,
    party_type=None,
    party_type_fieldname=None,
):
    """
    This FunctionReceived Args as Str without commiting Change
    Return Count of Effected Docs
    """
    doc = frappe.qb.DocType(doctype)

    # Define conditions
    conditions = (doc[party_fieldname] == party) & (
        Coalesce(doc.party_master, "") != party_master
    )
    if party_type_fieldname:
        conditions &= doc[party_type_fieldname] == party_type

    # Get count of affected records
    affected_count = (
        frappe.qb.from_(doc)
        .select(Count("*").as_("count"))
        .where(conditions)
        .run(as_dict=True)
    )
    count = affected_count[0]["count"] if affected_count else 0

    if count > 0:

        # Step 2: Perform bulk update separately
        frappe.qb.update(doc).set(doc.party_master, party_master).where(
            conditions
        ).run()

    return count

# This will be called on insert new Document type in Party Master Setting and it has Exist documents
def update_exists_docs_on_new_document_type_insert(document_type):
    mapping_all = get_doctypes_functional_fields_mapping_as_dict()
    mapping = mapping_all.get(document_type, {})
    meta = frappe.get_meta(document_type, cache=False)
    if not meta.has_field("party_master"):
        frappe.log_error(
            _("Uph:Party Master Field does not Exist on {0}").format(document_type),
        )
    if isinstance(document_type, str):
        mapping = get_doctypes_functional_fields_mapping_as_dict().get(
            document_type, {}
        )
    if not mapping:
        frappe.log_error(
            _("Could not update documents {0}").format(
                document_type,
                f"Error exist as no mapping Could be this function run before update cache ",
            )
        )
        return
    doctype = mapping.get("document_type")
    meta = frappe.get_meta(doctype)
    if meta.issingle or not frappe.db.count(doctype):
        return
    fieldname = mapping.get("party_fieldname")




@frappe.whitelist()
def set_party_as_default_for_party_master(
    party, party_type, party_master, value, commit=True
):
    # check if there is another default to the same party master:
    defaults = frappe.get_list(
        party_type,
        filters={"party_master": party_master, "is_default_for_party_master": 1},
        fields=["name", "is_default_for_party_master"],
    )
    if defaults:
        for d in defaults:
            if d.is_default_for_party_master and d.name != party:
                doc = frappe.get_doc(party_type, d.name)
                doc.set("is_default_for_party_master", 0)
                doc.save()
    doc = frappe.get_doc(party_type, party)
    doc.set("is_default_for_party_master", value)
    doc.save()




@frappe.whitelist()
def check_duplicate_voucher_party_master(
    party_master, doctype, posting_date, current_name=None, doc=None
):
    pfn = get_mapped_fieldnames(doctype, "party_fieldname")
    total_fn = get_mapped_fieldnames(doctype, "total_fieldname")
    filters = {
        "party_master": party_master,
        "posting_date": posting_date,
        "docstatus": ["!=", 2],
    }

    if current_name:
        filters["name"] = ["!=", current_name]
    fields = ["name", "owner"]
    if pfn:
        fields.append(pfn)
    if total_fn:

        fields.append(total_fn)

    duplicates = frappe.get_all(
        doctype,
        fields=fields,
        filters=filters,
        limit=5,  # Limit to 5 results for performance
    )

    if duplicates and not doc:
        for d in duplicates or []:
            if d.get(pfn):
                d["party"] = d.get(pfn, "")
            if d.get(total_fn):

                d["total"] = d.get(total_fn, 0)

    return {"duplicates": duplicates}

