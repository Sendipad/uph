"""`(Party Master )`
This is a controller functions to Validate Party Master,Validate Or fetch Party Master
on Transactional Docs,
As well it will validate Party Analytic Accounting which is a Dimension Accounting
Meanwhile it will Create the required Custom Field on Some ERPNext Doctype
Beside It Will reflect the Change of set Party Master on Party Type Doctype

"""

import frappe
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


def validate_party_master_on_document_types(doc, method=None):
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

    fetch_if_not_exist = not meta.get_field(party_field).reqd
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
            msg = _("Party Master for {0} set to {1} automatically").format(
                d.doctype, new_party_master
            )
            if msg not in alert_msg:
                alert_msg.append(msg)

        elif not party_master or party_master != new_party_master:
            frappe.throw(
                _("Party Master mismatch or missing for Party {0} ({1})").format(
                    party, party_type
                )
            )

        validate_party_analytic_accounting(d, new_party_master)

    if is_child:
        for d in doc.get_all_children():
            if d.doctype == document_type:
                set_or_validate_party_master(d)
    else:
        set_or_validate_party_master(doc, is_main=True)

    for msg in alert_msg:
        frappe.msgprint(title=_("Party Master Auto-set"), msg=msg, alert=1)


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


def validate_party_master_on_target_party_type(doc, method):
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
            # Invalidate caches
            if doc.party_master:
                update_linked_party_to_party_master_count(doc.party_master)
                SmartCache.update_party_to_pm_data(
                    doc.doctype, doc.name, new_pm=doc.party_master
                )
                # This also updates the List_Parties hash implicitly in SmartCache logic if needed
                # But let's be explicit if we want to force refresh or just let existing logic work
                # SmartCache.update_party_master_parties(doc.party_master) # This fetches fresh list

            if old_party_master:
                update_linked_party_to_party_master_count(old_party_master)
                SmartCache.update_party_to_pm_data(
                    doc.doctype, doc.name, old_pm=old_party_master
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
                counts_only=False,
                queue="long",
                enqueue_after_commit=True,
            )

    # Require flag before deleting document to empty doc.party_master and pass previous validation
    if method == "on_trash" and doc.party_master:
        pm = frappe.get_doc("Party Master", doc.party_master)
        pm.add_comment("Comment", _("Party : {0} Has been deleted").format(doc.name))
        SmartCache.update_party_to_pm_data(
            doc.doctype, doc.name, old_pm=doc.party_master
        )


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

        party.add_comment(
            "Comment", f"🎯 {content} Assigned to → {party_master or 'NULL'}"
        )

        if party_master:
            doc_pm = frappe.get_doc("Party Master", party_master)
            doc_pm.add_comment(
                "Comment", f"{party.name} Assigned and Updated: {content}"
            )
    if not counts_only:
        frappe.db.commit()


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
    doc = frappe.qb.DocType(doctype)

    # Define conditions
    conditions = doc[party_fieldname] == party

    if old_party_master:
        conditions &= doc.party_master == old_party_master
    else:
        # Match documents where party_master is NULL or empty, and different from target
        conditions &= Coalesce(doc.party_master, "") == ""
        conditions &= Coalesce(doc.party_master, "") != (party_master or "")

    # Avoid touching cancelled documents for audit integrity
    if frappe.db.has_column(doctype, "docstatus"):
        conditions &= doc.docstatus < 2

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

    if count > 0 and not counts_only:

        # Step 2: Perform bulk update separately
        frappe.qb.update(doc).set(doc.party_master, party_master).where(
            conditions
        ).run()

    return count


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
def validate_party_master_on_document_types_smart(doc, method=None):
    from uph.party.controllers.cache_utils import is_configured_doctype

    if is_configured_doctype(doc.doctype):
        validate_party_master_on_document_types(doc, method)


def validate_party_master_on_target_party_type_smart(doc, method):
    from uph.party.controllers.cache_utils import is_configured_party_type

    if is_configured_party_type(doc.doctype):
        validate_party_master_on_target_party_type(doc, method)


@frappe.whitelist()
def get_party_master_details_with_parties(party_master, party_type=None):
    if not party_master:
        return {}

    pm_doc = frappe.get_doc("Party Master", party_master)
    from uph.party.controllers.queries import get_party_master_parties

    parties = get_party_master_parties(party_master, party_type=party_type)

    return {"party_master": pm_doc, "parties": parties}


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
    # 1. Call standard ERPNext logic
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

    # 2. UPH Override Logic
    settings = frappe.get_cached_doc("Party Master Settings")
    if not settings.override_party_details_api:
        return party_details

    # If party_master is not provided, try to fetch it from the party
    if not party_master and party:
        party_master = frappe.db.get_value(party_type, party, "party_master")

    if not party_master:
        return party_details

    # Fetch PM details
    pm = frappe.get_doc("Party Master", party_master)

    # 3. Apply PM Details to party_details (Enrichment only if missing)
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
    if not party_details.get(account_fieldname):
        transaction_currency = currency or party_details.get("currency")
        if party_master and company and transaction_currency:
            enforce_strict = settings.enforce_strict_currency
            target_account = get_hierarchical_pm_account(
                party_master,
                company,
                transaction_currency,
                enforce_strict=enforce_strict,
            )
            if target_account:
                party_details[account_fieldname] = target_account

    return party_details


def get_hierarchical_pm_account(pm_name, company, currency, enforce_strict=False):
    """
    Traverses the PM tree upwards to find an account matching company and currency.
    1. Looks for exact currency match in PM Accounts.
    2. If not strict, looks for generic match (empty currency) in PM Accounts.
    3. Handles both leaf accounts and group accounts (expanding by currency).
    """
    print(
        f"DEBUG UPH: Looking for account for PM {pm_name}, Company {company}, Currency {currency}, Strict {enforce_strict}"
    )
    while pm_name:
        # 1. Try exact currency match
        acc_data = frappe.db.get_value(
            "Party Master Accounts",
            {"parent": pm_name, "company": company, "currency": currency},
            ["account"],
            as_dict=1,
        )
        print(f"DEBUG UPH: PM {pm_name} exact match result: {acc_data}")

        if not acc_data and not enforce_strict:
            # 2. Try generic match (fallback)
            generic_acc = frappe.db.sql(
                """
                SELECT account FROM `tabParty Master Accounts`
                WHERE parent = %s AND company = %s AND (currency IS NULL OR currency = '')
                LIMIT 1
            """,
                (pm_name, company),
                as_dict=1,
            )
            acc_data = generic_acc[0] if generic_acc else None
            print(f"DEBUG UPH: PM {pm_name} generic match result: {acc_data}")

        if acc_data and acc_data.get("account"):
            target_account = acc_data.account
            acc_meta = frappe.db.get_value(
                "Account", target_account, ["is_group", "account_currency"], as_dict=1
            )
            print(f"DEBUG UPH: Found Account {target_account} metadata: {acc_meta}")

            if acc_meta:
                if acc_meta.is_group:
                    # Expansion logic for group accounts
                    leaf_filters = {
                        "parent_account": target_account,
                        "account_currency": currency,
                        "is_group": 0,
                        "company": company,
                        "disabled": 0,
                    }
                    leaf_match = frappe.db.get_value(
                        "Account",
                        leaf_filters,
                        "name",
                    )
                    print(
                        f"DEBUG UPH: Group expansion under {target_account} with {leaf_filters} result: {leaf_match}"
                    )
                    if leaf_match:
                        return leaf_match
                else:
                    # It's a leaf account
                    # If strict, verify account currency matches transaction currency
                    is_match = (
                        not enforce_strict or acc_meta.account_currency == currency
                    )
                    print(f"DEBUG UPH: Leaf account {target_account} match: {is_match}")
                    if is_match:
                        return target_account

        # Move up to parent PM
        pm_name = frappe.db.get_value("Party Master", pm_name, "parent_party_master")
        print(f"DEBUG UPH: Moving up to parent PM: {pm_name}")

    print(f"DEBUG UPH: No account found for {pm_name}")
    return None
