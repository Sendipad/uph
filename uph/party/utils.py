# -----------------------------------------------------------------------------
# Project Name: UPH - Unified Party Hub
# File: utils.py
# Description: Utility functions for party management and integration in UPH, including helpers for custom fields and Arabic money in words.
#
# Author: Abdo Ruzaqi(Sendipad)
# Created: 2025-04-10
# License: GNU General Public License v3.0 (GPL-3.0)
# Repository: https://github.com/Sendipad/uph
#
# Copyright (c) 2025 Abdo  Ruzaqi(Sendipad)
# This file is part of the UPH project and is released under the GPL-3.0 license.
# See LICENSE file or https://www.gnu.org/licenses/gpl-3.0.en.html for full terms.
# -----------------------------------------------------------------------------
import frappe
from frappe.utils import unique
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

from uph.regional.arabic import money_in_words


def test_arabic():
    amount = 10000.00
    currency = "YER"
    frappe.local.lang == "ar"
    return money_in_words(amount, currency)


def get_common_party_with_party_master_fields():
    return {
        "party_name": "Customer : customer_name\nSupplier:supplier_name\nEmployee: employee_name",
        "is_internal_party": "Customer:is_internal_customer\nSupplier:is_internal_supplier",
        "party_type_group": "Customer:customer_group\nSupplier:supplier_group",
        "group_type": "Customer:_\nSupplier:_\nEmployee:_\nShareholder:_",
    }


def get_mapped_fieldnames(doctype, fields=None):

    if doctype == "Journal Entry":
        doctype = "Journal Entry Account"
    mapped = {
        "Sales Invoice": frappe._dict(
            party_fieldname="customer",
            isdynamic_party_type=0,
            party_type="Customer",
            currency_fieldname="currency",
            party_type_fieldname=None,
        ),
        "Sales Order": frappe._dict(
            party_fieldname="customer",
            isdynamic_party_type=0,
            party_type="Customer",
            currency_fieldname="currency",
            party_type_fieldname=None,
        ),
        "Delivery Note": frappe._dict(
            party_fieldname="customer",
            isdynamic_party_type=0,
            party_type="Customer",
            currency_fieldname="currency",
            party_type_fieldname=None,
        ),
        "Customer": frappe._dict(
            party_fieldname="name",
            isdynamic_party_type=0,
            party_type="Customer",
            currency_fieldname="default_currency",
            party_type_fieldname=None,
            party_name_fieldname="customer_name",
        ),
        "Payment Entry": frappe._dict(
            party_fieldname="party",
            isdynamic_party_type=1,
            party_type=None,
            party_type_fieldname="party_type",
            currency_fieldname=None,
        ),
        "Journal Entry Account": frappe._dict(
            party_fieldname="party",
            isdynamic_party_type=1,
            party_type=None,
            party_type_fieldname="party_type",
            currency_fieldname="account_currency",
        ),
        "Supplier": frappe._dict(
            party_fieldname="name",
            isdynamic_party_type=0,
            party_type="Supplier",
            currency_fieldname="default_currency",
            party_type_fieldname=None,
            party_name_fieldname="supplier_name",
        ),
        "Employee": frappe._dict(
            party_fieldname="name",
            isdynamic_party_type=0,
            party_type="Employee",
            currency_fieldname="salary_currency",
            party_type_fieldname=None,
            party_name_fieldname="employee_name",
        ),
        "ShareHolder": frappe._dict(
            party_fieldname="name",
            isdynamic_party_type=0,
            party_type="ShareHolder",
            currency_fieldname=None,
            party_type_fieldname=None,
        ),
        "Purchase Invoice": frappe._dict(
            party_fieldname="supplier",
            isdynamic_party_type=0,
            party_type="Supplier",
            currency_fieldname="currency",
            party_type_fieldname=None,
        ),
        "Purchase Order": frappe._dict(
            party_fieldname="supplier",
            isdynamic_party_type=0,
            party_type="Supplier",
            currency_fieldname="currency",
            party_type_fieldname=None,
        ),
        "Purchase Reciept": frappe._dict(
            party_fieldname="supplier",
            isdynamic_party_type=0,
            party_type="Supplier",
            currency_fieldname="currency",
            party_type_fieldname=None,
        ),
        "Expense Claim": frappe._dict(
            party_fieldname="employee",
            isdynamic_party_type=0,
            party_type="Employee",
            currency_fieldname="currency",
            party_type_fieldname=None,
        ),
    }
    result = mapped.get(doctype, None)
    if not result:
        return None

    if fields:
        if isinstance(fields, str):
            return result.get(fields, None)
        elif isinstance(fields, (list, tuple)):
            return tuple(result.get(field, None) for field in fields)
    return result


def get_party_type_currency_field(party_type):
    cf = {
        "Customer": "default_currency",
        "Supplier": "default_currency",
        "Employee": "salary_currency",
    }
    return cf.get(party_type, "")


def get_party_type_name_field(party_type):
    cf = {
        "Customer": "customer_name",
        "Supplier": "supplier_name",
        "Employee": "employee_name",
        "Shareholder": "title",
    }
    return cf.get(party_type)


def get_transactional_doctype_list_to_add_pm():
    dt = [
        "Sales Invoice",
        "Sales Order",
        "Purchase Order",
        "Delivery Note",
        "Purchase Receipt",
        "Purchase Invoice",
        "Payment Entry",
        "Journal Entry",
    ]
    if frappe.db.exists("DocType", "Expense Claim"):
        dt.append("Expense Claim")

    return dt


def get_party_field_in_doctype(doctype):
    cf = {
        "Sales Invoice": "customer",
        "Sales Order": "customer",
        "Purchase Order": "supplier",
        "Delivery Note": "customer",
        "Purchase Receipt": "supplier",
        "Purchase Invoice": "supplier",
        "Payment Entry": "party",
        "Journal Entry Account": "party",
        "Expense Claim": "employee",
        "POS Profile": "customer",
        "POS Invoice": "customer",
    }
    return cf.get(doctype)


def get_party_type_party_field_from_doc(doc, value=False, party_type=None):

    if doc.doctype in ("Payment Entry", "Journal Entry Account") and party_type is None:
        party_type = doc.party_type

    list_dict = {
        "Sales Invoice": {"party_type": "Customer", "party": "customer"},
        "Sales Order": {"party_type": "Customer", "party": "customer"},
        "Purchase Order": {"party_type": "Supplier", "party": "supplier"},
        "Delivery Note": {"party_type": "Customer", "party": "customer"},
        "Purchase Receipt": {"party_type": "Supplier", "party": "supplier"},
        "Purchase Invoice": {"party_type": "Supplier", "party": "supplier"},
        "Payment Entry": {"party_type": party_type, "party": "party"},
        "Journal Entry Account": {"party_type": party_type, "party": "party"},
        "Expense Claim": {"party_type": "Employee", "party": "employee"},
    }
    if doc.doctype in list_dict.keys() and not value:
        return list_dict.get(doc.doctype)
    else:
        fields = list_dict.get(doc.doctype)
        return {
            "party_type": fields.get("party_type"),
            "party": doc.get(fields.get("party")),
        }


def get_party_type_from_doctype(doctype):
    pt_map = {
        "Sales Invoice": "Customer",
        "Sales Order": "Customer",
        "Purchase Order": "Supplier",
        "Delivery Note": "Customer",
        "Purchase Receipt": "Supplier",
        "Purchase Invoice": "Supplier",
        "Journal Entry Account": "party",
        "Expense Claim": "Employee",
    }
    if pt_map.get(doctype):
        return pt_map.get(doctype)
    return ""


def setup_party_master_custom_fields():
    dt_df = frappe._dict()
    doclist = frappe.get_hooks("tx_doctype_with_party_master")
    doclist.extend(["POS Invoice", "POS Profile"])
    for d in doclist:
        # Use `d` directly as the Doctype name
        doctype = d  # ✅ No need for getattr()

        # Skip if the Doctype doesn't exist (except for "Expense Claim")
        if doctype == "Expense Claim" and not frappe.db.exists("DocType", doctype):
            continue

        # Get the party field in the Doctype
        party_field = get_party_field_in_doctype(d)
        fetch_from = f"doc.{party_field}.party_master"
        mandatory_depends_on = "eval:frm.is_new()===1"
        # Determine where to insert the field
        insert_after = (
            "naming_series"
            if frappe.get_meta(d).has_field("naming_series")
            else party_field
        )
        if doctype == "Journal Entry Account":
            insert_after = "bank_account"
            mandatory_depends_on = mandatory_depends_on + "doc.party_type && doc.party"
        if doctype == "Payment Reconciliation":
            insert_after = "company"

        # Add field definition to dictionary
        dt_df.update(
            {
                doctype: frappe._dict(
                    fieldname="party_master",
                    fieldtype="Link",
                    options="Party Master",
                    fetch_if_empty=1,
                    fetch_from=fetch_from,
                    allow_on_submit=1,
                    mandatory_depends_on="'{0}'".format(mandatory_depends_on),
                    in_list_view=1,
                    in_standard_filter=1,
                    bold=1,
                    read_only_depends_on="eval:doc.docstatus==1",
                    label="Party Master",
                    insert_after=insert_after,
                )
            }
        )

    # Create custom fields
    for dt, df in dt_df.items():
        try:
            if cf := frappe.get_list(
                "Custom Field",
                filters={"dt": dt, "fieldname": "party_master"},
                fields=["name"],
            ):
                dfdoc = frappe.get_doc("Custom Field", cf[0].get("name"))
                for key, value in df.items():
                    dfdoc.set(key, value)
                dfdoc.save()
                continue
            create_custom_field(dt, dt_df.get(dt))
        except Exception as e:
            frappe.log_error(e)
            frappe.db.rollback()
            raise e
        finally:
            frappe.db.commit()


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_party_master_list(doctype, txt, searchfield, start, page_len, filters):
    """
    SECURE: Rewritten using pypika query builder to prevent SQL injection.
    Returns list of Party Masters for link field searches.

    Security fixes:
    - No string formatting in SQL
    - All parameters properly escaped by pypika
    - Field names validated against meta
    """
    from frappe.query_builder import DocType
    from frappe.query_builder.functions import Locate
    from functools import reduce
    import operator

    # Force doctype to Party Master (avoid injection via doctype param)
    doctype = "Party Master"
    meta = frappe.get_meta(doctype)
    PartyMaster = DocType("Party Master")

    # === Build field list (validated against meta) ===
    fields = ["name"]
    search_fields = meta.get_search_fields() or []

    # Add title field if configured
    if meta.get("show_title_field_in_link") and (tf := meta.get("title_field")):
        if tf not in search_fields:
            search_fields.insert(0, tf)
        if tf not in fields:
            fields.append(tf)

    # Validate all search fields exist in meta
    for field in search_fields:
        if meta.has_field(field) and field not in fields:
            fields.append(field)

    # === Build base query ===
    query = frappe.qb.from_(PartyMaster).select(
        *[getattr(PartyMaster, f) for f in fields]
    )

    # Base filter: exclude cancelled docs
    query = query.where(PartyMaster.docstatus < 2)

    # === Party type filter (SECURE - no string formatting) ===
    if party_type := filters.get("party_type"):
        # Subquery for party masters with secondary roles
        PartyMasterRole = DocType("Party Master Role")
        secondary_role_subquery = (
            frappe.qb.from_(PartyMasterRole)
            .select(PartyMasterRole.parent)
            .where(PartyMasterRole.party_type_role == party_type)
        )

        # Main party type OR has secondary role
        query = query.where(
            (PartyMaster.party_type == party_type)
            | PartyMaster.name.isin(secondary_role_subquery)
        )

    elif on_doctype := filters.get("on_doctype"):
        # Get party type from doctype
        pt = get_party_type_from_doctype(on_doctype)
        if pt:
            PartyMasterRole = DocType("Party Master Role")
            secondary_role_subquery = (
                frappe.qb.from_(PartyMasterRole)
                .select(PartyMasterRole.parent)
                .where(PartyMasterRole.party_type_role == pt)
            )
            query = query.where(
                (PartyMaster.party_type == pt)
                | PartyMaster.name.isin(secondary_role_subquery)
            )

    # === Additional filters from filters dict (SECURE) ===
    if isinstance(filters, dict):
        for key, value in filters.items():
            if key not in ("party_type", "on_doctype") and meta.has_field(key):
                query = query.where(getattr(PartyMaster, key) == value)
    elif isinstance(filters, list):
        for filter_item in filters:
            if len(filter_item) >= 3:
                field, operator_str, value = (
                    filter_item[0],
                    filter_item[1],
                    filter_item[2],
                )
                if meta.has_field(field):
                    field_obj = getattr(PartyMaster, field)
                    # Map operator strings to pypika operators
                    if operator_str == "=":
                        query = query.where(field_obj == value)
                    elif operator_str == "!=":
                        query = query.where(field_obj != value)
                    elif operator_str == "in":
                        query = query.where(field_obj.isin(value))
                    # Add more operators as needed

    # === Text search across search fields (SECURE) ===
    if txt and search_fields:
        # Build OR conditions for text search
        search_conditions = []
        for field in search_fields:
            if meta.has_field(field):
                search_conditions.append(getattr(PartyMaster, field).like(f"%{txt}%"))

        if search_conditions:
            # Combine with OR
            combined_search = reduce(operator.or_, search_conditions)
            query = query.where(combined_search)

    # === Order by relevance (SECURE - pypika handles escaping) ===
    if txt:
        # Order by: closest match in name, then party_name, then idx
        cleaned_txt = txt.replace("%", "")  # Remove wildcards for LOCATE
        query = query.orderby(
            Locate(cleaned_txt, PartyMaster.name),
            Locate(cleaned_txt, PartyMaster.party_name),
            PartyMaster.idx.desc(),
            PartyMaster.name,
            PartyMaster.party_name,
        )
    else:
        query = query.orderby(PartyMaster.name)

    # === Pagination (SECURE - int conversion prevents injection) ===
    start = int(start) if start else 0
    page_len = int(page_len) if page_len else 20
    query = query.limit(page_len).offset(start)

    # Execute and return
    return query.run()


# ============================================================================
# NORMALIZATION UTILS (Moved from mdm.normalization)
# ============================================================================

import re
import unicodedata
from functools import lru_cache

# Constants for normalization
DIACRITIC_REGEX = re.compile(r"[\u0610-\u061A\u064B-\u065F\u06D6-\u06ED]")
WHITESPACE_REGEX = re.compile(r"\s+")

TRANSLATION_TABLE = str.maketrans(
    {
        # Arabic normalization
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ى": "ي",
        "ة": "ه",
        "ؤ": "و",
        "ئ": "ي",
        "ـ": "",
        # Persian character mapping
        "ك": "ک",
        "ي": "ی",
        # Digits from Indian to Arabic
        **{chr(0x660 + i): str(i) for i in range(10)},
        # Latin accents (lowercase)
        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",
        "á": "a",
        "à": "a",
        "â": "a",
        "ä": "a",
        "í": "i",
        "ì": "i",
        "î": "i",
        "ï": "i",
        "ó": "o",
        "ò": "o",
        "ô": "o",
        "ö": "o",
        "ú": "u",
        "ù": "u",
        "û": "u",
        "ü": "u",
        "ç": "c",
        "ñ": "n",
        # Latin accents (uppercase)
        "É": "E",
        "È": "E",
        "Ê": "E",
        "Ë": "E",
        "Á": "A",
        "À": "A",
        "Â": "A",
        "Ä": "A",
        "Í": "I",
        "Ì": "I",
        "Î": "I",
        "Ï": "I",
        "Ó": "O",
        "Ò": "O",
        "Ô": "O",
        "Ö": "O",
        "Ú": "U",
        "Ù": "U",
        "Û": "U",
        "Ü": "U",
        "Ç": "C",
        "Ñ": "N",
    }
)


@frappe.whitelist()
def normalize_text(text: str) -> str:
    """Wrapper for _normalize_text_cached to be used in API calls."""
    return _normalize_text_cached(text)


def normalize_for_blocking(text: str) -> str:
    """
    Normalize text for blocking key generation.
    Removes all spaces and punctuation for use as blocking keys.
    """
    if not text:
        return ""
    normalized = normalize_text(text)
    return re.sub(r"[^a-z0-9]", "", normalized)


@lru_cache(maxsize=1024)
def _normalize_text_cached(text: str) -> str:
    """
    Normalize text for fuzzy matching.
    Applies: trim, unicode normalization (NFKD), remove diacritics, casefold,
    character translation, and whitespace normalization.
    """
    if not text:
        return ""

    # 1. Trim whitespace
    text = text.strip()

    # 2. Unicode Normalize (NFKD decomposes characters)
    text = unicodedata.normalize("NFKD", text)

    # 3. Remove Diacritics (All combining marks + Arabic diacritics)
    # We use category 'Mn' (Mark, Nonspacing) to catch all combining marks
    text = "".join(c for c in text if not unicodedata.category(c).startswith("M"))

    # Also apply Arabic specific regex if needed (though Mn might cover it, let's be safe)
    text = DIACRITIC_REGEX.sub("", text)

    # 4. Casefold (lower case + aggressive normalization)
    text = text.casefold()

    # 5. Character Translation (unify chars)
    text = text.translate(TRANSLATION_TABLE)

    # 6. Normalize Whitespace (collapse multiple spaces)
    text = WHITESPACE_REGEX.sub(" ", text).strip()

    return text


@frappe.whitelist()
def get_field_options(doctype):
    if not doctype:
        return []
    meta = frappe.get_meta(doctype)
    fields = []
    for df in meta.fields:
        if df.fieldtype not in frappe.model.no_value_fields:
            fields.append(
                {"label": df.label, "value": df.fieldname, "fieldtype": df.fieldtype}
            )
    return fields


@frappe.whitelist()
def get_common_fields_in_doctypes(doctypes):
    import json

    if isinstance(doctypes, str):
        doctypes = json.loads(doctypes)

    if not doctypes:
        return []

    common_fields = {}
    first_doctype = doctypes[0]
    meta = frappe.get_meta(first_doctype)

    # Initialize with first doctype fields
    for df in meta.fields:
        if df.fieldtype not in frappe.model.no_value_fields:
            common_fields[df.fieldname] = {
                "label": df.label,
                "value": df.fieldname,
                "fieldtype": df.fieldtype,
            }

    # Intersect with others
    for dt in doctypes[1:]:
        meta = frappe.get_meta(dt)
        current_fieldnames = {df.fieldname for df in meta.fields}
        common_fields = {
            k: v for k, v in common_fields.items() if k in current_fieldnames
        }

    return list(common_fields.values())


@frappe.whitelist()
def get_field_path(doctype, basefieldname=None):
    # This seems to be used for child tables or nested fields
    # Based on JS usage: const child = cached.child_tables?.[basefieldname];
    # It might return structure of child table fields.
    meta = frappe.get_meta(doctype)
    if basefieldname:
        df = meta.get_field(basefieldname)
        if df and df.fieldtype == "Table":
            child_meta = frappe.get_meta(df.options)
            fields = []
            for cdf in child_meta.fields:
                if cdf.fieldtype not in frappe.model.no_value_fields:
                    fields.append(
                        {
                            "label": cdf.label,
                            "value": cdf.fieldname,
                            "fieldtype": cdf.fieldtype,
                        }
                    )
            return {"fields": fields}

    # default return doc fields
    return {"fields": get_field_options(doctype)}
