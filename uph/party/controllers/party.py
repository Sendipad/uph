"""`(Party Master )`
This is a controller functions to Validate Party Master,Validate Or fetch Party Master
on Transactional Docs,
As well it will validate Party Analytic Accounting which is a Dimension Accounting
Meanwhile it will Create the required Custom Field on Some ERPNext Doctype
Beside It Will reflect the Change of set Party Master on Party Type Doctype

"""

import frappe
from erpnext import get_company_currency
from erpnext.accounts.party import get_party_details as erp_get_party_details

from uph.party.utils import get_mapped_fieldnames
from pypika.functions import Coalesce

from frappe import _
from frappe.query_builder.functions import Count
import uph
from uph.party.controllers.cache_utils import (
    get_doctypes_functional_fields_mapping_as_dict,
    clear_all_caches,
    SmartCache,
)


# Caching
def on_update_document_types_clear_cache():
    clear_all_caches()


def get_document_type_mapping_with_party_master(document_type):
    def generator():
        docs = get_doctypes_functional_fields_mapping_as_dict()
        if document_type in docs:
            return docs[document_type]
        for v in docs.values():
            if v.get("document_type") == document_type:
                return v
        return frappe.db.get_value(
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


def validate_party_master_on_document_types(doc, method=None, *args, **kwargs):
    if (
        frappe.flags.in_patch
        or frappe.flags.in_install
        or frappe.flags.in_migrate
        or frappe.flags.in_import
        or frappe.flags.in_setup_wizard
    ):
        return
    mapping = get_doctypes_functional_fields_mapping_as_dict()
    doctype = doc.doctype
    map_conf = mapping.get(doctype)
    if not map_conf:
        return

    document_type = map_conf.get("document_type")
    is_child = document_type != doctype
    party_field = map_conf.get("party_fieldname")
    party_type_field = map_conf.get("party_type_fieldname")

    meta = frappe.get_meta(document_type)
    if not meta.has_field(party_field):
        return

    is_mandatory = map_conf.get("reqd")
    alert_msg = []

    # Pre-fetch logic for performance
    party_master_map = {}

    # Collect all parties to fetch in one go (Main doc and children)
    parties_to_fetch = set()
    default_party_type = map_conf.get("party_type")

    # 1. Main Doc
    p_main = doc.get(party_field)
    pt_main = default_party_type or doc.get(party_type_field)
    if p_main and pt_main:
        parties_to_fetch.add((pt_main, p_main))

    # 2. Child Table
    if is_child:
        items = doc.get_all_children()
        for d in items:
            if d.doctype != document_type:
                continue
            p = d.get(party_field)
            pt = default_party_type or d.get(party_type_field)
            if p and pt:
                parties_to_fetch.add((pt, p))

    # Bulk Fetch
    for pt, p_list in _group_by_party_type(parties_to_fetch).items():
        if not p_list:
            continue
        results = frappe.get_all(
            pt, filters={"name": ["in", p_list]}, fields=["name", "party_master"]
        )
        for r in results:
            party_master_map[(pt, r.name)] = r.party_master

    def set_or_validate_party_master(d, is_main=False):
        party = d.get(party_field)
        party_type = map_conf.get("party_type") or d.get(party_type_field)
        party_master = d.get("party_master")

        if not (party and party_type):
            return

        new_party_master = party_master_map.get((party_type, party))

        # 1. Strategy: If Party Master is missing but exists on the linked Party (Customer/Supplier),
        # ALWAYS try to set it to maintain data integrity.
        if not party_master and new_party_master:
            d.party_master = new_party_master
            party_master = new_party_master
            msg = _("Party Master for {0} set to {1} automatically").format(
                d.doctype, new_party_master
            )
            if msg not in alert_msg:
                alert_msg.append(msg)

        # 2. Strategy: Validate Mismatch
        if party_master and new_party_master and party_master != new_party_master:
            frappe.throw(
                _(
                    "Party Master mismatch for Party {0} ({1}): Expected {2}, found {3}"
                ).format(party, party_type, new_party_master, party_master)
            )

        # 3. Strategy: Validate Mandatory
        if not party_master and is_mandatory:
            frappe.throw(
                _(
                    "Party Master is mandatory for {0}, but not set and not found on Party {1} ({2})"
                ).format(_(doctype), party, party_type)
            )

        if party_master:
            _ensure_party_contact_link(d, party_type, party, party_master)
            validate_party_analytic_accounting(d, party_master)

    if is_child:
        for d in doc.get_all_children():
            if d.doctype == document_type:
                set_or_validate_party_master(d)
    else:
        set_or_validate_party_master(doc, is_main=True)

    for msg in alert_msg:
        frappe.msgprint(title=_("Party Master Auto-set"), msg=msg, alert=1)


def _ensure_party_contact_link(doc, party_type, party, party_master=None):
    """Ensure Contact is linked to the ERP Party when it comes from Party Master."""
    if not (doc and party_type and party):
        return

    meta = doc.meta
    if not meta or not meta.has_field("contact_person"):
        return

    contact = doc.get("contact_person")
    if not contact:
        return

    if frappe.db.exists(
        "Dynamic Link",
        {
            "parenttype": "Contact",
            "parent": contact,
            "link_doctype": party_type,
            "link_name": party,
        },
    ):
        return

    if not party_master:
        return

    pm_contact = frappe.db.get_value(
        "Party Master", party_master, "party_primary_contact"
    )

    if contact != pm_contact and not frappe.db.exists(
        "Dynamic Link",
        {
            "parenttype": "Contact",
            "parent": contact,
            "link_doctype": "Party Master",
            "link_name": party_master,
        },
    ):
        return

    frappe.get_doc(
        {
            "doctype": "Dynamic Link",
            "parenttype": "Contact",
            "parent": contact,
            "parentfield": "links",
            "link_doctype": party_type,
            "link_name": party,
        }
    ).db_insert()


def _group_by_party_type(party_tuples):
    """Helper to group (party_type, party) tuples by party_type"""
    grouped = {}
    for pt, p in party_tuples:
        grouped.setdefault(pt, []).append(p)
    return grouped


def validate_party_analytic_accounting(doc, party_master):
    if not doc.get("party_analytic_accounting"):
        return

    # Check if PAA is enabled globally
    if not frappe.db.get_single_value(
        "Party Master Settings", "enable_party_analytic_accounting"
    ):
        return

    paa_party_master = frappe.db.get_value(
        "Party Analytic Accounting", doc.party_analytic_accounting, "party_master"
    )

    if paa_party_master != party_master:
        frappe.throw(
            _(
                "Party Analytic Accounting {0} belongs to Party Master {1}, but this document is linked to {2}"
            ).format(doc.party_analytic_accounting, paa_party_master, party_master)
        )


def validate_party_master_on_target_party_type(doc, method=None, *args, **kwargs):
    if (
        frappe.flags.in_patch
        or frappe.flags.in_install
        or frappe.flags.in_migrate
        # or frappe.flags.in_import
        or frappe.flags.in_setup_wizard
        or doc.doctype not in SmartCache.get_party_type_list()
    ):
        return
    party_type_rule = get_party_type_validation_rule(party_type=doc.doctype)

    if method == "validate":
        if party_type_rule.get("reqd") and not doc.party_master:
            if frappe.flags.in_test and not getattr(
                doc, "force_validate_party_master", False
            ):
                return

            frappe.throw(
                _(
                    "Party Master is mandatory for {0},<br> You can unset Mandatory in Party Master Settings"
                ).format(_(doc.doctype))
            )
        if doc.party_master:
            if not frappe.db.exists("Party Master", doc.party_master):
                # If the linked Party Master doesn't exist (e.g., after app reset),
                # allow the save so the user can re-assign it.
                return

            if not is_valide_party_master_to_party(doc.party_master, doc.doctype):
                pm_data = frappe.get_cached_doc("Party Master", doc.party_master)
                reason = (
                    _("is disabled")
                    if pm_data.disabled
                    else (
                        _("is a group")
                        if pm_data.is_group
                        else _("missing the role of {0}").format(_(doc.doctype))
                    )
                )
                frappe.throw(
                    _("Party Master {0} is invalid for {1}: {2}").format(
                        doc.party_master, _(doc.doctype), reason
                    )
                )
        if doc.party_master:
            rule_fieldname = get_party_type_validation_rule(doc.doctype).get(
                "rule_fieldname"
            )
            allowed = get_party_type_validation_rule(doc.doctype).get("allowed")

            # Only check for duplicates if multiple records are not allowed,
            # or if they are allowed but must be unique by a specific field (rule_fieldname).
            if not allowed or (allowed and rule_fieldname):
                filters = [["party_master", "=", doc.party_master]]
                if rule_fieldname:
                    filters.append([rule_fieldname, "=", doc.get(rule_fieldname)])

                all_linked = frappe.db.get_all(
                    doc.doctype, filters=filters, pluck="name"
                )
                existing = [n for n in all_linked if n != doc.name]

                if existing:
                    existing = existing[0]
                    frappe.throw(
                        title=_("Duplicate Exists"),
                        msg=_(
                            "Party Master {0} already has a Party {1} linked (we are {2})"
                        ).format(doc.party_master, existing, doc.name),
                    )

        # Sync Naming if enabled
        sync_party_name_from_party_master(doc)

        # Enforce cross-type uniqueness
        settings = frappe.get_cached_doc("Party Master Settings")
        if settings.enforce_cross_type_uniqueness and doc.name:
            from uph.party.controllers.cache_utils import get_configured_party_types

            for pt in get_configured_party_types():
                if pt == doc.doctype:
                    continue
                if frappe.db.exists(pt, doc.name):
                    frappe.throw(
                        _(
                            "Party '{0}' already exists as a {1}. Cross-type uniqueness is enforced."
                        ).format(doc.name, pt)
                    )

    if method in ("on_update", "after_rename"):
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
            # Invalidate caches
            if doc.party_master:
                update_linked_party_to_party_master_count(doc.party_master)
                SmartCache.update_party_to_pm_data(
                    doc.doctype, doc.name, new_pm=doc.party_master
                )

            if old_party_master:
                update_linked_party_to_party_master_count(old_party_master)
                SmartCache.update_party_to_pm_data(
                    doc.doctype, doc.name, old_pm=old_party_master
                )

        if doc.party_master != old_party_master or method == "after_rename":
            if frappe.flags.in_test:
                on_change_party_master_update_transactional_document_types(
                    party=doc, old_party_master=old_party_master, counts_only=False
                )
                return

            frappe.enqueue(
                on_change_party_master_update_transactional_document_types,
                party=doc,
                old_party_master=old_party_master,
                counts_only=False,
                queue="long",
                enqueue_after_commit=True,
            )

    # Require flag before deleting document to empty doc.party_master and pass previous validation
    if method == "on_trash" and doc.party_master:
        if not frappe.db.exists("Party Master", doc.party_master):
            return
        pm = frappe.get_doc("Party Master", doc.party_master)
        pm.add_comment("Comment", _("Party : {0} Has been deleted").format(doc.name))
        SmartCache.update_party_to_pm_data(
            doc.doctype, doc.name, old_pm=doc.party_master
        )


def is_valide_party_master_to_party(party_master, role):
    if isinstance(party_master, str):
        if not frappe.db.exists("Party Master", party_master):
            return False
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


def on_change_party_master_update_transactional_document_types(
    party, old_party_master=None, document_type=None, counts_only=True
):
    changes = []
    party_master = party.get("party_master")
    doclist = get_functional_document_types(document_type)
    party_type = party.doctype
    for d in doclist:
        if not d.party_fieldname:
            continue
        if d.is_dynamic_party_type and not d.party_type_fieldname:
            continue
        if d.party_type and d.party_type != party_type:
            continue
        doctype = d.document_type
        party_fieldname = d.get("party_fieldname")
        party_type_fieldname = d.get("party_type_fieldname", None)

        count = _update_party_master_field_on_exists_transactional_document_types(
            doctype=doctype,
            party_fieldname=party_fieldname,
            party=party.name,
            party_master=party_master,
            party_type=party_type,
            party_type_fieldname=party_type_fieldname,
            old_party_master=old_party_master,
            counts_only=counts_only,
        )
        if count:
            changes.append(frappe._("{0} Count: {1}").format(frappe._(doctype), count))
    if changes:
        content = ", ".join(changes)

        try:
            party.add_comment(
                "Comment", f"🎯 {content} Assigned to → {party_master or 'NULL'}"
            )

            if party_master and frappe.db.exists("Party Master", party_master):
                doc_pm = frappe.get_doc("Party Master", party_master)
                doc_pm.add_comment(
                    "Comment", f"{party.name} Assigned and Updated: {content}"
                )
        except Exception as e:
            # Prevent QueryDeadlockError or other comment insertion failures from breaking the voucher sync loop
            frappe.logger("uph").warning(
                f"Failed to add comment to {party.name} during voucher sync: {e}"
            )

    # Let Frappe request/patch transaction boundaries handle commits.
    # Avoid controller-level commits in deep business logic.


def _update_party_master_field_on_exists_transactional_document_types(
    doctype,
    party_fieldname,
    party,
    party_master,
    party_type=None,
    party_type_fieldname=None,
    old_party_master=None,
    counts_only=True,
):
    """
    This FunctionReceived Args as Str without commiting Change
    Return Count of Effected Docs
    """
    # Refactored to explicit SQL for guaranteed index usage and production safety
    where_clause = f"`{party_fieldname}` = %s"
    params = [party]

    if old_party_master:
        where_clause += " AND `party_master` = %s"
        params.append(old_party_master)
    else:
        if party_master:
            where_clause += " AND (`party_master` IS NULL OR `party_master` = '')"
        else:
            where_clause += " AND (`party_master` IS NOT NULL AND `party_master` != '')"

    if frappe.db.has_column(doctype, "docstatus"):
        where_clause += " AND `docstatus` < 2"

    if party_type_fieldname:
        where_clause += f" AND `{party_type_fieldname}` = %s"
        params.append(party_type)

    if counts_only:
        return frappe.db.sql(
            f"SELECT COUNT(*) FROM `tab{doctype}` WHERE {where_clause}", params
        )[0][0]

    frappe.db.sql(
        f"UPDATE `tab{doctype}` SET `party_master` = %s WHERE {where_clause}",
        [party_master] + params,
    )
    return frappe.db.count(
        doctype, filters={party_fieldname: party, "party_master": party_master}
    )  # Approximated count after update


def get_functional_document_types(document_type=None):
    doclist = frappe.get_doc("Party Master Settings").document_types
    doclist = [d for d in doclist if not frappe.get_meta(d.parent_doctype).issingle]
    if document_type:
        doclist = [
            d
            for d in doclist
            if d.document_type == document_type or d.parent_doctype == document_type
        ]
    return doclist


def update_linked_party_to_party_master_count(party_master):
    if isinstance(party_master, str):
        if not frappe.db.exists("Party Master", party_master):
            return
        party_master = frappe.get_doc("Party Master", party_master)
    if party_master.is_group or party_master.is_new():
        party_master.total_linked_party = 0
        return
    roles = [party_master.party_type]
    if party_master.roles:
        for r in party_master.roles:
            roles.append(r.get("party_type_role"))
    total = 0
    # Batch count for all roles
    for role_doctype in roles:
        if not frappe.db.exists("DocType", role_doctype):
            continue
        total += frappe.db.count(
            role_doctype,
            filters={"party_master": party_master.name, "docstatus": ["<", 2]},
        )

    if party_master.total_linked_party != total:
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
    settings = frappe.get_cached_doc("Party Master Settings")
    if not settings.check_party_master_duplicate_vouchers:
        return {"duplicates": [], "settings": {}}

    pfn = get_mapped_fieldnames(doctype, "party_fieldname")
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

    return {
        "duplicates": duplicates,
        "settings": {
            "action": settings.duplicate_voucher_action,
            "has_bypass": allow_duplicate_submission(doctype, current_name),
        },
    }


# Smart wrappers for hooks
def validate_party_master_on_document_types_smart(doc, method=None, *args, **kwargs):
    from uph.party.controllers.cache_utils import is_configured_doctype

    if (
        frappe.flags.in_patch
        or frappe.flags.in_install
        or frappe.flags.in_migrate
        or frappe.flags.in_import
        or frappe.flags.in_setup_wizard
    ):
        return

    if is_configured_doctype(doc.doctype):
        validate_party_master_on_document_types(doc, method, *args, **kwargs)


def validate_party_master_on_target_party_type_smart(doc, method=None, *args, **kwargs):
    from uph.party.controllers.cache_utils import is_configured_party_type

    if (
        frappe.flags.in_patch
        or frappe.flags.in_install
        or frappe.flags.in_migrate
        or frappe.flags.in_import
        or frappe.flags.in_setup_wizard
    ):
        return

    if is_configured_party_type(doc.doctype):
        validate_party_master_on_target_party_type(doc, method, *args, **kwargs)


@frappe.whitelist()
def get_party_master_details_with_parties(party_master, party_type=None):
    if not party_master:
        return {}

    if not frappe.db.exists("Party Master", party_master):
        return None
    pm_doc = frappe.get_doc("Party Master", party_master)
    from uph.party.controllers.queries import get_party_master_parties

    parties = get_party_master_parties(party_master, party_type=party_type)

    return {"party_master": pm_doc, "parties": parties}


@frappe.whitelist()
def get_party_master_defaults(party_type=None, party=None, party_master=None):
    """Return Party Master defaults mapped to transactional fields."""
    if not party_master and party_type and party:
        party_master = frappe.db.get_value(party_type, party, "party_master")

    if not party_master or not frappe.db.exists("Party Master", party_master):
        return {}

    defaults = frappe.db.get_value(
        "Party Master",
        party_master,
        ["default_cost_center", "default_project", "default_party_analytic_accounting"],
        as_dict=1,
    )

    if not defaults:
        return {}

    out = {}
    if defaults.get("default_cost_center"):
        out["cost_center"] = defaults["default_cost_center"]
    if defaults.get("default_project"):
        out["project"] = defaults["default_project"]
    if defaults.get("default_party_analytic_accounting"):
        out["party_analytic_accounting"] = defaults["default_party_analytic_accounting"]

    return out


@frappe.whitelist()
def allow_duplicate_submission(doctype, docname):
    settings = frappe.get_cached_doc("Party Master Settings")
    if not settings.check_party_master_duplicate_vouchers:
        return True

    bypass_role = settings.role_to_bypass_duplicate_voucher
    if bypass_role and bypass_role in frappe.get_roles():
        return True

    return False


@frappe.whitelist()
def get_party_details(
    party=None,
    account=None,
    party_type="Customer",
    company=None,
    posting_date=None,
    bill_date=None,
    price_list=None,
    currency=None,
    doctype=None,
    ignore_permissions=False,
    fetch_payment_terms_template=True,
    party_address=None,
    company_address=None,
    shipping_address=None,
    dispatch_address=None,
    pos_profile=None,
    party_master=None,  # Added by UPH
):
    settings = frappe.get_cached_doc("Party Master Settings")
    if not settings.override_party_details_api:
        return erp_get_party_details(
            party=party,
            account=account,
            party_type=party_type,
            company=company,
            posting_date=posting_date,
            bill_date=bill_date,
            price_list=price_list,
            currency=currency,
            doctype=doctype,
            ignore_permissions=ignore_permissions,
            fetch_payment_terms_template=fetch_payment_terms_template,
            party_address=party_address,
            company_address=company_address,
            shipping_address=shipping_address,
            dispatch_address=dispatch_address,
            pos_profile=pos_profile,
        )

    # If party_master is not provided, try to fetch it from the party
    if not party_master and party:
        party_master = frappe.db.get_value(party_type, party, "party_master")

    if not party_master:
        return erp_get_party_details(
            party=party,
            account=account,
            party_type=party_type,
            company=company,
            posting_date=posting_date,
            bill_date=bill_date,
            price_list=price_list,
            currency=currency,
            doctype=doctype,
            ignore_permissions=ignore_permissions,
            fetch_payment_terms_template=fetch_payment_terms_template,
            party_address=party_address,
            company_address=company_address,
            shipping_address=shipping_address,
            dispatch_address=dispatch_address,
            pos_profile=pos_profile,
        )

    # Fetch PM details
    if not frappe.db.exists("Party Master", party_master):
        return erp_get_party_details(
            party=party,
            account=account,
            party_type=party_type,
            company=company,
            posting_date=posting_date,
            bill_date=bill_date,
            price_list=price_list,
            currency=currency,
            doctype=doctype,
            ignore_permissions=ignore_permissions,
            fetch_payment_terms_template=fetch_payment_terms_template,
            party_address=party_address,
            company_address=company_address,
            shipping_address=shipping_address,
            dispatch_address=dispatch_address,
            pos_profile=pos_profile,
        )
    pm = frappe.get_doc("Party Master", party_master)

    # Prefer PM defaults in the original ERPNext call to avoid re-fetching
    party_default_currency = None
    if party:
        party_default_currency = frappe.db.get_value(
            party_type, party, "default_currency"
        )

    if not currency and not party_default_currency and pm.default_currency:
        currency = pm.default_currency

    if not price_list and pm.default_price_list:
        price_list = pm.default_price_list

    pm_address = pm.party_primary_address
    if pm_address:
        if not party_address:
            party_address = pm_address
        if party_type in ["Customer", "Lead"] and not shipping_address:
            shipping_address = pm_address
        elif party_type not in ["Customer", "Lead"] and not dispatch_address:
            dispatch_address = pm_address

    # 1. Call standard ERPNext logic with PM-preferred defaults
    from erpnext.accounts import party as erp_party

    original_get_default_contact = erp_party.get_default_contact

    def _pm_default_contact(doctype, name):
        if pm.party_primary_contact and doctype == party_type and name == party:
            return pm.party_primary_contact
        return original_get_default_contact(doctype, name)

    if pm.party_primary_contact:
        erp_party.get_default_contact = _pm_default_contact

    try:
        party_details = erp_get_party_details(
            party=party,
            account=account,
            party_type=party_type,
            company=company,
            posting_date=posting_date,
            bill_date=bill_date,
            price_list=price_list,
            currency=currency,
            doctype=doctype,
            ignore_permissions=ignore_permissions,
            fetch_payment_terms_template=fetch_payment_terms_template,
            party_address=party_address,
            company_address=company_address,
            shipping_address=shipping_address,
            dispatch_address=dispatch_address,
            pos_profile=pos_profile,
        )
    finally:
        if pm.party_primary_contact:
            erp_party.get_default_contact = original_get_default_contact

    # 2. Apply PM Details to party_details (Enrichment only if missing)
    # Contact Logic
    if not party_details.get("contact_person") and pm.party_primary_contact:
        party_details.contact_person = pm.party_primary_contact
        from erpnext.accounts.party import complete_contact_details

        complete_contact_details(party_details)

    # Address Logic
    address_field = (
        "customer_address" if party_type == "Customer" else "supplier_address"
    )
    if not party_details.get(address_field) and pm.party_primary_address:
        party_details[address_field] = pm.party_primary_address
        if not party_details.get("address_display"):
            from frappe.contacts.doctype.address.address import get_address_display

            party_details["address_display"] = get_address_display(
                pm.party_primary_address
            )

    # Common Fields Mapping
    mapping = {
        "tax_id": "tax_id",
        "language": "language",
        "territory": "territory",
        "default_currency": "currency",
        "tax_category": "tax_category",
        "default_cost_center": "cost_center",
        "default_project": "project",
        "default_party_analytic_accounting": "party_analytic_accounting",
    }

    if party_type == "Customer":
        mapping["party_type_group"] = "customer_group"
    elif party_type == "Supplier":
        mapping["party_type_group"] = "supplier_group"

    for pm_field, target_field in mapping.items():
        if not party_details.get(target_field):
            val = pm.get(pm_field)
            if val:
                party_details[target_field] = val

    # Hierarchical Account Lookup
    account_fieldname = "debit_to" if party_type == "Customer" else "credit_to"
    transaction_currency = party_details.get("currency") or currency
    if not transaction_currency and company:
        transaction_currency = get_company_currency(company)
    if party_master and company and transaction_currency:
        enforce_strict = settings.enforce_strict_currency
        target_account = get_hierarchical_pm_account(
            party_master,
            company,
            transaction_currency,
            enforce_strict=enforce_strict,
        )

        current_account = party_details.get(account_fieldname)
        if not current_account:
            if target_account:
                party_details[account_fieldname] = target_account
        else:
            if enforce_strict:
                account_currency = frappe.get_cached_value(
                    "Account", current_account, "account_currency"
                )
                if account_currency and account_currency != transaction_currency:
                    if target_account:
                        party_details[account_fieldname] = target_account
                    else:
                        party_details[account_fieldname] = None

    # Advance Account (ERPNext v15+)
    if party_master and company and transaction_currency:
        advance_account = get_hierarchical_pm_account(
            party_master,
            company,
            transaction_currency,
            enforce_strict=settings.enforce_strict_currency,
            account_field="advance_account",
        )
        if advance_account and not party_details.get("advance_account"):
            party_details["advance_account"] = advance_account

    return party_details


def sync_party_name_from_party_master(doc):
    """
    Syncs the Party (Customer/Supplier) name with Party Master numbering
    based on the 'Role Prefix Mode' setting.
    """
    if not doc.party_master:
        return

    settings = frappe.get_cached_doc("Party Master Settings")
    if not settings.sync_erp_party_naming:
        return

    if not frappe.db.exists("Party Master", doc.party_master):
        return

    pm = frappe.get_cached_doc("Party Master", doc.party_master)
    if not pm.party_number:
        return

    mode = settings.role_prefix_mode
    party_type = doc.doctype
    new_name = pm.party_number

    # Determine if this is a secondary role
    is_primary = pm.party_type == party_type

    # 2-letter abbreviation (e.g., Cu, Su)
    abbr = party_type[:2].capitalize()

    if mode and "Prefix" in mode:
        prefix = f"{abbr}-"
        if mode == "Prefix for All Role":
            new_name = f"{prefix}{pm.party_number}"
        elif mode == "Prefix for Secondary Role" and not is_primary:
            new_name = f"{prefix}{pm.party_number}"

    elif mode and "Suffix" in mode:
        suffix = f"-{abbr}"
        if mode == "Suffix for All Role":
            new_name = f"{pm.party_number}{suffix}"
        elif mode == "Suffix Secondary Roles" and not is_primary:
            new_name = f"{pm.party_number}{suffix}"

    # Multi-party uniqueness suffix: if multi-party is allowed, append the rule field value (e.g. Currency)
    rule = get_party_type_validation_rule(party_type)
    if rule and rule.get("allowed") and rule.get("rule_fieldname"):
        suffix_val = doc.get(rule.get("rule_fieldname"))
        if suffix_val:
            new_name = f"{new_name}-{suffix_val}"

    # If name is different, we need to rename or set name
    if doc.name != new_name:
        if not doc.name or doc.is_new():
            doc.name = new_name
        else:
            # Rename existing document
            # We must use frappe.rename_doc but be careful about recursion
            # and transaction handling. rename_doc commits by default.
            # Ideally, we shouldn't rename inside validate/save loops.
            # But the user asked for sync.
            # We'll use enqueue to avoid blocking/recursion issues.
            frappe.enqueue(
                "frappe.model.rename_doc.rename_doc",
                doctype=doc.doctype,
                old=doc.name,
                new=new_name,
                force=True,
                show_alert=False,
            )


def get_hierarchical_pm_account(
    pm_name, company, currency, enforce_strict=False, account_field="account"
):
    """
    Traverses the PM tree upwards to find an account matching company and currency.
    1. Looks for exact currency match in PM Accounts.
    2. If not strict, looks for generic match (empty currency) in PM Accounts.
    3. Handles both leaf accounts and group accounts (expanding by currency).
    """
    while pm_name:
        # 1. Try exact currency match
        acc_data = frappe.db.get_value(
            "Party Master Accounts",
            {"parent": pm_name, "company": company, "currency": currency},
            [account_field, "currency"],
            as_dict=1,
        )

        if (not acc_data or not acc_data.get(account_field)) and not enforce_strict:
            # 2. Try generic match (fallback) - Robust Python-based filtering
            all_pm_accounts = frappe.db.get_values(
                "Party Master Accounts",
                {"parent": pm_name, "company": company},
                [account_field, "currency"],
                as_dict=1,
            )
            for row in all_pm_accounts:
                if row.get(account_field) and not row.get("currency"):
                    acc_data = row
                    break

        if acc_data and acc_data.get(account_field):
            target_account = acc_data[account_field]
            acc_meta = frappe.db.get_value(
                "Account", target_account, ["is_group", "account_currency"], as_dict=1
            )

            if acc_meta:
                if acc_meta.get("is_group"):
                    # Expansion logic for group accounts - Robust get_all
                    leaf_matches = frappe.get_all(
                        "Account",
                        filters={
                            "parent_account": target_account,
                            "account_currency": currency,
                            "is_group": 0,
                            "company": company,
                            "disabled": 0,
                        },
                        pluck="name",
                        limit=1,
                    )
                    if leaf_matches:
                        return leaf_matches[0]
                else:
                    # It's a leaf account
                    # If strict, verify account currency matches transaction currency
                    is_match = (
                        not enforce_strict
                        or acc_meta.get("account_currency") == currency
                    )
                    if is_match:
                        return target_account

        # Move up to parent PM
        pm_name = frappe.db.get_value("Party Master", pm_name, "parent_party_master")

    return None
