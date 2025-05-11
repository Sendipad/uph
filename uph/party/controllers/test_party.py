"""
import frappe
from uph.party.controllers.party import update_transactional_docs,get_parties

def test_batch_update():
    cl=frappe.get_all('Customer',filters={'party_master':['is','set']})
    for c in cl:
        party_doc = frappe.get_doc('Customer', c.get('name')).as_dict()
        update_transactional_docs(party_doc)
def test_get_parties():
    pm='132000001'
    pt='Customer'
    return get_parties(pm,pt)

def test_update_transactional_doc():
    # Enable test mode
    party='YER-مبيعات المعرض'

    party_doc = frappe.get_doc('Customer', party).as_dict()
    # Set a new Party Master for testing

    #frappe.logger().info(f"Running test_update_transactional_docs for {party_doc.name}")

    # Run the function
    update_transactional_docs(party_doc)

    # Log results



def test_update_transactional_docs(party_doc):

    frappe.log_error(f"🔹 Starting update_transactional_docs for Party Master: {party_doc.party_master}")
    party_master=party_doc.party_master
    party_type=party_doc.doctype
    party=party_doc.name
    changes = {}

    for doctype in frappe.get_hooks('tx_doctype_with_party_master'):
        pfs = get_maped_fieldnames(doctype)
        pf = pfs.get('party_fieldname')
        ptf = pfs.get('party_type_fieldname')

        if not pf:
            frappe.logger().warning(f"⚠️ Skipping {doctype}, no party_fieldname found.")
            continue

        if not frappe.get_meta(doctype).has_field('party_master'):
            frappe.logger().warning(f"⚠️ Skipping {doctype}, 'party_master' field not found.")
            continue

        trans_doc = frappe.qb.DocType(doctype)

        # Define conditions
        conditions = ((trans_doc[pf] == party) &  (Coalesce(trans_doc.party_master, '') != party_doc.party_master))
        if ptf:
            conditions &= (trans_doc[ptf] == party_type)

        # Define fields before condition
        fields = (trans_doc.name, trans_doc.party_master)

        if doctype == "Journal Entry Account":
            fields = (trans_doc.parent.as_('name'), trans_doc.party_master)

        # Print the SQL query for debugging
        query = frappe.qb.from_(trans_doc).select(*fields).where(conditions)
        sql_query = str(query)  # Convert to string to log
        frappe.logger().info(f"📌 Executing SQL for {doctype}: {sql_query}")

        affected_records = query.run(as_dict=True)

        frappe.logger().info(f"📌 Affected Records in {doctype}: {affected_records}")

        if affected_records:
            changes[doctype] = [{'name': r['name'], 'old_pm': r['party_master']} for r in affected_records]

            # Perform bulk update
            update_query = (
                frappe.qb.update(trans_doc)
                .set(trans_doc.party_master, party_doc.party_master)
                .where(conditions)
            )
            update_query.run()

            frappe.logger().info(f"✅ Updated {len(affected_records)} records in {doctype}")

    # Logging Changes
    frappe.log_error(f"🎯 Completed update_transactional_docs. Changes: {changes}")

    return changes



###########################################################
# Mark Deprecated
def validate_party_master(doc, method=None):
    doctype = doc.doctype
    party_type_list = uph.get_party_type_list()
    party_settings = frappe.get_cached_doc(Party_Master_Settings, None)
    transactional_documents = [
        r.get("parent_doctype") for r in party_settings.document_type
    ]
    if doctype in party_type_list:
        return on_party_type_validate(doc, method)
    # Handle Journal Entry specifically
    if doctype == "Journal Entry":
        if doc.is_system_generated:
            doc.flags.pass_duplicate_validation = True
        return validate_party_master_journal_entry_account(doc, method)

    meta = frappe.get_meta(doctype)
    party_settings = frappe.get_doc("Party Settings")
    pm_is_mandatory = party_settings.is_party_master_mandatory
    has_pm_field = meta.has_field("party_master")

    pm_name = doc.get("party_master") if has_pm_field else None

    # Validate mandatory Party Master
    if pm_is_mandatory and not pm_name and not frappe.flags.ignore_pm_reqd:
        if doc.docstatus == 1 and method == "on_update_after_submit":
            frappe.msgprint(_("Warning: Party Master is mandatory but missing."))
            return
        frappe.throw(_("Party Master is mandatory for this document."))

    # Retrieve mapped field configurations
    mapped = get_mapped_fieldnames(doctype) or get_linked_transactional_doctype().get(
        doctype
    )
    if not mapped:
        return

    # Determine party_type and party_fieldname from mappings
    party_type = get_mapped_fieldnames(doctype, "party_type")
    party_field = get_mapped_fieldnames(doctype, "party_fieldname")
    party = doc.get(party_field) if party_field else None

    # Fallback to dynamic party_type field if needed
    if not party_type:
        party_type_field = get_mapped_fieldnames(doctype, "party_type_fieldname")
        party_type = doc.get(party_type_field) if party_type_field else None

    # Validate essential fields
    if not party_type or not party:
        return  # No party information to validate against

    # Fetch actual Party Master from the party record
    actual_pm = (
        frappe.db.get_value(party_type, party, "party_master") if party else None
    )
    doc_pm = doc.get("party_master")

    # Check Party Master consistency
    if actual_pm != doc_pm:
        if not actual_pm and doc_pm:
            frappe.throw(
                _("{0} {1} is not linked to Party Master {2}").format(
                    _(party_type), party, doc_pm
                )
            )
        elif actual_pm and not doc_pm:
            if not pm_is_mandatory:
                doc.party_master = actual_pm
            else:
                frappe.throw(
                    _("Party Master is mandatory. Expected: {0}").format(actual_pm)
                )
        else:
            frappe.throw(
                _("Mismatched Party Master. {0} has {1}, document shows {2}").format(
                    party, actual_pm, doc_pm
                )
            )

    # Handle dynamic party type mapping
    if mapped.get("isdynamic") and not party_type:
        party_type = doc.get("party_type")

    # Validate analytic accounting if applicable
    if (
        meta.has_field("party_analytic_accounting")
        and doc.party_master
        and method == "before_submit"
    ):
        validate_party_analytic_accounting(doc, method)


# This will Apply Validation on All Doctype That Contains 'party_master' Field
def validate_party_analytic_accounting(doc, method):
    pm = doc.get("party_master")
    enforce = frappe.db.get_value(
        "Party Master", pm, "enforce_party_analaytic_accounting_selection"
    )
    if enforce and not doc.party_analytic_accounting:
        frappe.throw(Error_msg.get("PAA_Mandatory").formate(pm))
    if (
        doc.party_master
        and doc.doc.party_analytic_accounting
        and doc.party_master
        != frappe.db.get_value(
            "Party Analytic Accounting", doc.party_analytic_accounting, "party_master"
        )
    ):
        frappe.throw(
            _("This Dimension {0} is not for Party Master {1}").format(
                _("Party Analytic Accounting"), doc.party_master
            )
        )


# To validate Changes in Party Type(Customer,Supplier,Employee or Shareholder)Changes with Party Master
# Mark Deprecated
def on_party_type_document_validate(doc, method):
    if (
        frappe.flags.in_patch
        or frappe.flags.in_install
        or frappe.flags.in_migrate
        or frappe.flags.in_import
        or frappe.flags.in_setup_wizard
        or doc.doctype not in uph.get_party_type_list
    ):
        return
    party_master = doc.get("party_master", None)
    # party_master_doc=frappe.get_doc('Party Master',party_master)
    if party_master and (
        not frappe.db.exists("Party Master", party_master)
        or not is_valide_party_master_to_party(party_master, doc.doctype)
    ):
        return validate_party_master("throw", "NonExistPartyMaster", None, party_master)

    old_party_master = None
    change_party_master = False
    if not doc.is_new():
        old_party_master = frappe.db.get_value(doc.doctype, doc.name, "party_master")
    if party_master != old_party_master:
        change_party_master = True
    party_fields = get_mapped_fieldnames(doc.doctype)

    # validate Party Master with this Party Unique Currency
    if change_party_master:
        filters = {"party_master": party_master}
        if party_fields.get("currency_fieldname"):
            filters.update(
                {party_fields.get("currency_fieldname"): doc.get("currency_fieldname")}
            )
        if frappe.db.exists(doc.doctype, filters):
            return validate_party_master(
                "throw", "DuplicateCurrencyLinked", None, party_master
            )
        add_coments(doc, party_master, old_party_master)
        # frappe.cache.delete_value("pm_parties_{0}".format(party_master.name))
        # frappe.cache.delete_value("pm_parties_{0}".format(old_party_master))
    if not frappe.flags.in_renaming_party_master:
        frappe.enqueue(
            on_change_party_master_update_transactional_document_types,
            party_doc=doc,
            queue="short",
        )


def validate_party_master_journal_entry_account(doc, method):
    if not frappe.get_meta("Journal Entry Account").has_field("party_master"):
        return
    for d in doc.accounts:
        if (
            method == "before_insert"
            and doc.doctype == "Journal Entry"
            and doc.is_system_generated
        ):
            if d.party_type and d.party and d.party_master:
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


def validation_msg_or_error(type, msg, custom_msg=None, additional=None, alert=1):
    msg_mapped = {
        "NonExistPartyMaster": _("This Party Master {0} Does Not Exist"),
        "Mandatory": (
            _("Mandatory"),
            _(
                "Party Master Is Mandatory /n<small> You can go to Party Setting and Uncheck Mandatory</small>"
            ),
        ),
        "Assigned": (
            None,
            _("Party Master {0} has been fetched from {1} and Assigned"),
        ),
        "NotMatchedPMP": (None, _("{0} {1} Unmatched Party Master To {2}")),
    }
    msgtxt = msg_mapped.get(msg, "")
    if additional:
        msgtxt.format(additional)

    if type == "throw":
        return frappe.throw(msgtxt)
    frappe.msgprint(msgtxt, alert=alert)


def add_coments(doc, new_party_master=None, old_party_master=None):
    fullname = frappe.utils.get_fullname(frappe.session.user)
    new_pm = new_party_master

    doc.add_comment(
        "Comment",
        _("{0} Has {1} This {2} To Party Master :{3}").format(
            frappe.bold(fullname),
            frappe.bold(_("Assign")),
            _(doc.doctype),
            frappe.bold(new_pm),
        ),
    )
    if new_party_master:
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
    if old_party_master:
        opm = frappe.get_doc("Party Master", old_party_master)
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


# Get All Doctype That Had Party Master Link Field , and Has GL Party Field
def get_linked_transactional_doctype():
    cache = frappe.cache()
    key = "uph_App_Party_mapped_field"

    # Retrieve cached result
    result = cache.get_value(key)
    if result:
        return result

    # Compute result and cache it
    result = _get_linked_transactional_doctype()
    cache.set_value(key, result, expires_in_sec=3600)
    return result


def _get_linked_transactional_doctype_one():
    party_type = frappe.get_all("Party Type", pluck="name")
    # We Hope This app will be Standard in Erpnext until then we stick with created Custom Fields
    cf = frappe.db.get_all(
        "Custom Field", filters={"options": "Party Master"}, fields=["dt", "fieldname"]
    )
    filtered_doctype = {d.get("dt"): {"fieldname": d.get("fieldname")} for d in cf}
    field = ["party", "customer", "supplier", "employee"]
    docfield = frappe.db.get_all(
        "DocField",
        filters={"options": ["in", party_type], "parent": ["!=", "Party Master"]},
        fields=["parent", "fieldname", "options", "reqd"],
        order_by="reqd desc,parent",
    )
    development_sug = []
    err = None
    err_msg = ""
    grouped_doctype_field = defaultdict(list)
    docfield = frappe.db.get_all(
        "DocField",
        filters={"options": ["in", party_type], "parent": ["!=", "Party Master"]},
        fields=["parent", "fieldname", "options", "reqd"],
        order_by="reqd desc,parent",
    )

    for d in docfield:
        key = d["parent"]
        rest = {k: v for k, v in d.items() if k != "parent"}
        grouped_doctype_field[key].append(rest)
    grouped_doctype_field = dict(grouped_doctype_field)
    for k, v in grouped_doctype_field.items():
        if k in filtered_doctype and len(v) > 0:
            dic = filtered_doctype.get(k)
            if len(v) == 1 and v[0]["reqd"] == 1:
                dic.update(
                    {
                        "party_fieldname": v[0]["fieldname"],
                    }
                )
                continue

            # picked_field={}
            suggested_field = None
            pt = get_mapped_fieldnames(k, "party_type")
            for r in v:
                if r.get("reqd") == 1:
                    suggested_field = r["fieldname"]
                    pt = r["options"]
            match = get_mapped_fieldnames(k, "party_fieldname")
            if match is not None and match == suggested_field:
                dic.update(
                    {
                        "party_fieldname": match,
                    }
                )
                filtered_doctype[k] = {
                    "party_fieldname": match,
                    "party_type": pt,
                }
                continue
            if suggested_field and match is None:
                pt = r["options"]
                development_sug.append(
                    f" Must Add Mapped Field name For Doctype {k} in the (get_maped_fieldname)"
                )
                dic.update(
                    {
                        "party_fieldname": suggested_field,
                    }
                )
                filtered_doctype[k] = {
                    "party_fieldname": match,
                    "party_type": pt,
                }
                continue
            err_msg = err_msg + (
                f" {k} DocType Must has pointed Field name to match with Party Master"
            )
        development_sug.append(
            f" {k} DocType has These Field {v} Which could improve UPH App Functionality /n"
        )

    for k in filtered_doctype.keys():

        if k in ("Payment Entry", "Journal Entry Account"):
            filtered_doctype[k] = {
                "fieldname": "party_master",
                "party_fieldname": "party",
                "isdynmic": 1,
                "party_type_fieldname": "party_type",
            }
            continue
        err_msg = (
            err_msg + f"For Doctype {k} you must implement match to functional Party"
        )
    if len(development_sug) > 0:
        frappe.log_error(
            f"🎯 Improvment Suggestion For UPH App", f"{' /n '.join(development_sug)}"
        )
    if err_msg != "":
        frappe.log_error(
            f"Error at Matching Functional Party to Party Master", f"{err_msg}"
        )
    r = (
        {k: v}
        for k, v in filtered_doctype.items()
        if isinstance(v, dict) and v.get("party_fieldname")
    )


def _get_linked_transactional_doctype():
    party_types = frappe.get_all("Party Type", pluck="name")
    custom_fields = frappe.db.get_all(
        "Custom Field", filters={"options": "Party Master"}, fields=["dt", "fieldname"]
    )
    filtered_doctypes = {
        cf["dt"]: {"fieldname": cf["fieldname"]} for cf in custom_fields
    }

    docfields = frappe.db.get_all(
        "DocField",
        filters={"options": ["in", party_types], "parent": ["!=", "Party Master"]},
        fields=["parent", "fieldname", "options", "reqd"],
        order_by="reqd desc, parent",
    )

    grouped_doctype_fields = defaultdict(list)
    for df in docfields:
        dic = {k: v for k, v in df.items() if k != "parent"}
        grouped_doctype_fields[df["parent"]].append(dic)

    error_messages = []
    grouped_doctype_fields = dict(grouped_doctype_fields)

    for doctype, fields in grouped_doctype_fields.items():
        if doctype in filtered_doctypes:
            dic = filtered_doctypes[doctype]
            pf = get_mapped_fieldnames(doctype, "party_fieldname")
            pt = get_mapped_fieldnames(doctype, "party_type")
            if not pf and not pt:
                if len(fields) == 1 and fields[0]["reqd"] == 1:
                    pf = fields[0]["fieldname"]
                    pt = fields[0]["options"]
                else:
                    for f in fields:
                        if f.get("reqd"):
                            pf = f.get("fieldname")
                            pt = f.get("options")
                        else:
                            if f.get("fieldname") in (
                                "customer",
                                "supplier",
                                "employee",
                            ):
                                error_messages.append(f"{doctype} {f.get('fieldname')}")
            dic.update({"party_fieldname": pf, "party_type": pt})
            filtered_doctypes[doctype] = dic

    for doctype in filtered_doctypes.keys():
        if doctype in ("Payment Entry", "Journal Entry Account"):
            filtered_doctypes[doctype] = {
                "fieldname": "party_master",
                "party_fieldname": "party",
                "isdynamic": 1,
                "party_type_fieldname": "party_type",
            }
        else:
            error_messages.append(
                f"For Doctype {doctype}, you must implement a match to functional Party"
            )
    # if error_messages:
    # frappe.log_error(title='UPH get_linked_transactional_doctype Found',error=' ,'.join(error_messages))
    r = {k: v for k, v in filtered_doctypes.items() if v.get("party_fieldname")}
    return r



def compare_documents(current_doc, existing_doc, meta, child_tables):

    comparison = {"is_duplicate": True, "matches": {"parent": [], "children": {}}}

    # Parent field comparison
    parent_fields = [
        df.fieldname
        for df in meta.fields
        if df.fieldtype not in ["Section Break", "Column Break", "Tab Break"]
        and df.fieldname not in ["name", "creation", "modified"]
    ]

    for field in parent_fields:
        current_val = current_doc.get(field)
        existing_val = existing_doc.get(field)

        if current_val == existing_val and current_val not in [None, ""]:
            comparison["matches"]["parent"].append(
                {"label": meta.get_field(field).label or field, "value": existing_val}
            )
        elif current_val != existing_val:
            comparison["is_duplicate"] = False

    # Child table comparison
    for table in child_tables:
        current_items = normalize_child_table(current_doc.get(table, []))
        existing_items = normalize_child_table(existing_doc.get(table, []))
        table_label = (meta.get_field(table).label or frappe.unscrub(table)) + " Items"

        comparison["matches"]["children"][table_label] = {
            "matched": current_items == existing_items,
            "current_count": len(current_items),
            "existing_count": len(existing_items),
        }

        if current_items != existing_items:
            comparison["is_duplicate"] = False

    return comparison


def normalize_child_table(items):

    try:
        return sorted(
            [
                frappe.as_json(
                    {
                        k: cstr(v)
                        for k, v in item.items()
                        if k
                        not in ["name", "parent", "parentfield", "parenttype", "idx"]
                    },
                    sort_keys=True,
                )
                for item in items
            ]
        )
    except Exception:
        return []

@frappe.whitelist()
def allow_duplicate_submission(doctype, name):

    try:
        if not frappe.has_permission(doctype, "submit", doc=name):
            frappe.throw(_("Insufficient Permissions"), frappe.PermissionError)

        doc = frappe.get_doc(doctype, name)
        doc.flags.ignore_duplicate_check = True        doc.submit()
        frappe.db.commit()
        return True
    except Exception as e:
        frappe.log_error(
            _("Duplicate Submission Failed"),
            reference_doctype=doctype,
            reference_name=name,
        )
        return False
"""
