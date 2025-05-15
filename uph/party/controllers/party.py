"""`(Party Master )`
This is a controller functions to Validate Party Master,Validate Or fetch Party Master
on Transactional Docs,
As well it will validate Party Analytic Accounting which is a Dimension Accounting
Meanwhile it will Create the required Custom Field on Some ERPNext Doctype
Beside It Will reflect the Change of set Party Master on Party Type Doctype

"""

import frappe

from uph.party.utils import get_mapped_fieldnames
from frappe.utils.caching import redis_cache
from pypika.functions import Coalesce

from frappe import _
from frappe.query_builder.functions import Count
from uph.party.boot import get_pm_doctypes
import uph


# Caching
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
    mapping = get_doctypes_functional_fields_mapping_as_dict()
    doctype = doc.doctype

    if (
        frappe.flags.in_patch
        or frappe.flags.in_install
        or frappe.flags.in_migrate
        or frappe.flags.in_import
        or frappe.flags.in_setup_wizard
        or doctype not in mapping
    ):
        return

    map_conf = mapping.get(doctype)
    if not map_conf:
        return

    document_type = map_conf.get("document_type")
    is_child = document_type != doctype
    party_field = map_conf.get("party_fieldname")
    party_type_field = map_conf.get("party_type_fieldname")
    meta = frappe.get_meta(document_type)
    fetch_if_not_exist = not meta.get_field(party_field).reqd
    alert_msg = []

    def set_or_validate_party_master(d):
        party = d.get(party_field)
        party_type = map_conf.get("party_type") or d.get(party_type_field)
        party_master = d.get("party_master")

        if not (party and party_type):
            return

        new_party_master = frappe.db.get_value(party_type, party, "party_master")
        should_autoset = (
            not party_master
            and new_party_master
            and (
                fetch_if_not_exist
                or getattr(doc.flags, "ignore_validate", False)
                or frappe.flags.in_test
            )
        )

        if should_autoset:
            d.party_master = new_party_master
            alert_msg.append(
                _("Party Master for {0} set to {1} automatically").format(
                    d.doctype, new_party_master
                )
            )
        elif not party_master or party_master != new_party_master:
            frappe.throw(
                _("Party Master mismatch or missing for Party {0} ({1})").format(
                    party, party_type
                )
            )

    if is_child:
        for d in doc.get_all_children():
            if d.doctype == document_type:
                set_or_validate_party_master(d)
    else:
        set_or_validate_party_master(doc)

    for msg in alert_msg:
        frappe.msgprint(title=_("Party Master Auto-set"), msg=msg, alert=1)


def validate_party_master_on_target_party_type(doc, method):
    if (
        frappe.flags.in_patch
        or frappe.flags.in_install
        or frappe.flags.in_migrate
        # or frappe.flags.in_import
        or frappe.flags.in_setup_wizard
        or doc.doctype not in uph.get_party_type_list()
    ):
        return
    party_type_rule = get_party_type_validation_rule(party_type=doc.doctype)

    if method == "validate":
        if party_type_rule.get("reqd") and not doc.party_master:
            frappe.throw(
                _(
                    "Party Master is mandatory for {0},<br> You can unset Mandatory in Party Master Settings"
                ).format(_(doc.doctype))
            )
        if doc.party_master and not is_valide_party_master_to_party(
            doc.party_master, doc.doctype
        ):
            frappe.throw(
                _(
                    "Party Master {0} Could be not Exists or is group or has not Role of {1} or not enabled"
                ).format(doc.party_master, doc.doctype)
            )
        if doc.party_master:
            filters = {
                "party_master": ["=", doc.party_master],
                "name": ["!=", doc.name],
            }
            rule_fieldname = get_party_type_validation_rule(doc.doctype).get(
                "rule_fieldname"
            )
            if rule_fieldname:
                filters.update({rule_fieldname: ["=", doc.get(rule_fieldname)]})
            existing = frappe.get_value(doc.doctype, filters, "name")
            if existing:
                frappe.throw(
                    title=_("Duplicate Exists"),
                    msg=_("Party Master {0} has a Party {1} with {2}").format(
                        doc.party_master,
                        existing,
                        doc.get(rule_fieldname) if rule_fieldname else "",
                    ),
                )

    if method == "on_update":
        old_doc = doc.get_doc_before_save()
        old_party_master = old_doc.get("party_master") if old_doc else None
        is_default_for_party_master = doc.is_default_for_party_master
        old_is_default_for_party_master = (
            old_doc.get("is_default_for_party_master") if old_doc else 0
        )
        if (
            doc.party_master != old_party_master
            or is_default_for_party_master != old_is_default_for_party_master
        ):
            if doc.party_master:
                update_linked_party_to_party_master_count(doc.party_master)
                frappe.cache.hdel(
                    uph.make_key("Party Master.parties"), doc.party_master
                )
            if old_party_master:
                update_linked_party_to_party_master_count(old_party_master)
                frappe.cache.hdel(
                    uph.make_key("Party Master.parties"), old_party_master
                )
        if doc.party_master != old_party_master:
            if frappe.flags.in_test:
                return on_change_party_master_update_transactional_document_types(
                    party=doc, old_party_master=old_party_master
                )
            return frappe.enqueue(
                on_change_party_master_update_transactional_document_types,
                party=doc,
                old_party_master=old_party_master,
                queue="default",
                enqueue_after_commit=True,
            )
    # Require flag before deleting document to empty doc.party_master and pass previouse validation
    if method == "on_trash" and doc.party_master:
        pm = frappe.get_doc("Party Master", doc.party_master)
        pm.add_comment("Comment", _("Party : {0} Has been deleted").format(doc.name))
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


def reset_default_on_party_master(party, party_type, party_master):
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
            method=_("Could not update documents {0}").format(
                document_type,
                error=_(
                    "Error exist as no mapping Could be this function run before update cache"
                ),
            )
        )
        return
    doctype = mapping.get("document_type")
    meta = frappe.get_meta(doctype)
    if meta.issingle or not frappe.db.count(doctype):
        return
    # fieldname = mapping.get("party_fieldname")

    # Uncomplete code


def update_linked_party_to_party_master_count(party_master):
    if isinstance(party_master, str):
        party_master = frappe.get_doc("Party Master", party_master)
    if party_master.is_group or party_master.is_new():
        party_master.total_linked_party = 0
        return
    roles = [party_master.party_type]
    if party_master.roles:
        for r in party_master.roles:
            roles.append(r.get("party_type_role"))
    total = 0
    for r in roles:
        total += frappe.db.count(
            r, filters={"party_master": party_master.name, "docstatus": ["!=", 2]}
        )
    if total:
        party_master.db_set("total_linked_party", total)


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
