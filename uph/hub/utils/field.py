# File uph/hub/utils/field.py
import frappe
from frappe import _
from typing import Union


@frappe.whitelist()
def get_field_path(doctype: Union[str, list], basefieldname=None):
    """Unified API to fetch field structure including child tables, with Redis cache support."""

    if isinstance(doctype, str):
        try:
            doctypes = frappe.parse_json(doctype)
            if not isinstance(doctypes, list):
                doctypes = [doctype]
        except Exception:
            doctypes = [doctype]
    else:
        doctypes = list(doctype)

    cache_key = f"field_path::{','.join(sorted(doctypes))}"
    cached = frappe.cache().get_value(cache_key)

    if cached:
        if basefieldname:
            if basefieldname in cached.get("child_tables", {}):
                return {
                    "fields": [],
                    "child": {basefieldname: cached["child_tables"][basefieldname]},
                }
            return {"fields": [], "child": {}}
        return cached

    # Not in cache: build and store
    result = _build_field_path_structure(doctypes)
    frappe.cache().set_value(cache_key, result, expires_in_sec=3600)

    if basefieldname:
        child = result.get("child_tables", {}).get(basefieldname)
        if child:
            return {"fields": [], "child": {basefieldname: child}}
        return {"fields": [], "child": {}}

    return result


def _build_field_path_structure(doctypes: list[str]) -> dict:
    """Build the complete field structure with optional merging/intersecting."""

    is_single = len(doctypes) == 1
    fields, child_tables = [], {}

    if is_single:
        doctype = doctypes[0]
        meta = frappe.get_meta(doctype)

        # Add system fields
        if not meta.istable:
            fields.extend(get_system_fields())

        # Add parent fields
        for field in meta.fields:
            if field.fieldtype in no_value_fields:
                continue

            fields.append(
                {
                    "label": field.label,
                    "fieldname": field.fieldname,
                    "fieldtype": field.fieldtype,
                    "options": field.options,
                }
            )

            # Add child table fields
            if field.fieldtype == "Table" and field.options:
                child_meta = frappe.get_meta(field.options)
                child_fields = []
                for child_field in child_meta.fields:
                    if child_field.fieldtype in no_value_fields:
                        continue
                    child_fields.append(
                        {
                            "label": child_field.label,
                            "fieldname": child_field.fieldname,
                            "fieldtype": child_field.fieldtype,
                            "options": child_field.options,
                        }
                    )
                child_tables[field.fieldname] = child_fields

    else:
        # Multiple doctypes → intersect fields
        fields = _get_common_fields(doctypes)

        # Merge common child tables
        reference_meta = frappe.get_meta(doctypes[0])
        for field in reference_meta.fields:
            if field.fieldtype != "Table" or not field.options:
                continue

            table_fieldname = field.fieldname
            merged_children = []
            seen_keys = set()

            for dt in doctypes:
                dt_meta = frappe.get_meta(dt)
                dt_field = next(
                    (
                        f
                        for f in dt_meta.fields
                        if f.fieldname == table_fieldname and f.fieldtype == "Table"
                    ),
                    None,
                )

                if not dt_field or not dt_field.options:
                    continue

                child_meta = frappe.get_meta(dt_field.options)
                for child_field in child_meta.fields:
                    key = (
                        child_field.fieldname,
                        child_field.fieldtype,
                        child_field.options,
                    )
                    if key in seen_keys or child_field.fieldtype in no_value_fields:
                        continue
                    seen_keys.add(key)
                    merged_children.append(
                        {
                            "label": child_field.label,
                            "fieldname": child_field.fieldname,
                            "fieldtype": child_field.fieldtype,
                            "options": child_field.options,
                        }
                    )

            if merged_children:
                child_tables[table_fieldname] = merged_children

    return {"fields": fields, "child_tables": child_tables}


def _get_common_fields(doctypes: list[str]) -> list:
    """Return intersecting fields (by fieldname/type/options) for multiple doctypes."""

    if not doctypes:
        return []

    field_counter = {}
    field_definitions = {}

    for dt in doctypes:
        meta = frappe.get_meta(dt)
        seen = set()

        for field in meta.fields:
            if field.fieldtype in no_value_fields:
                continue

            key = (field.fieldname, field.fieldtype, field.options)
            if key not in seen:
                seen.add(key)
                field_counter[key] = field_counter.get(key, 0) + 1
                if key not in field_definitions:
                    field_definitions[key] = {
                        "label": field.label,
                        "fieldname": field.fieldname,
                        "fieldtype": field.fieldtype,
                        "options": field.options,
                    }

    total = len(doctypes)
    return [field_definitions[k] for k, v in field_counter.items() if v == total]


def get_system_fields():
    """Return system fields for non-child doctypes"""
    return [
        {
            "label": "ID (name)",
            "fieldname": "name",
            "fieldtype": "Data",
            "options": None,
        },
        {
            "label": "Document Status (docstatus)",
            "fieldname": "docstatus",
            "fieldtype": "Select",
            "options": [
                {"label": "Draft", "value": 0},
                {"label": "Submitted", "value": 1},
                {"label": "Cancelled", "value": 2},
            ],
        },
        {
            "label": "Created At (creation)",
            "fieldname": "creation",
            "fieldtype": "Datetime",
            "options": None,
        },
        {
            "label": "Created By (owner)",
            "fieldname": "owner",
            "fieldtype": "Link",
            "options": "User",
        },
        {
            "label": "Modified At (modified)",
            "fieldname": "modified",
            "fieldtype": "Datetime",
            "options": None,
        },
        {
            "label": "Modified By (modified_by)",
            "fieldname": "modified_by",
            "fieldtype": "Link",
            "options": "User",
        },
    ]


no_value_fields = (
    "Section Break",
    "Column Break",
    "Tab Break",
    "HTML",
    "Button",
    "Image",
    "Fold",
    "Heading",
)


@frappe.whitelist()
def get_common_fields_in_doctypes(doctypes=None):
    if not doctypes:
        return []

    if isinstance(doctypes, str):
        doctypes = frappe.parse_json(doctypes)

    key = f"field_options:{','.join(sorted(doctypes))}"
    result = frappe.cache.get_value(key)
    if result:
        result = get_translated_label(result)
        result = get_system_fields() + result
        return result

    result = get_common_fields_in(doctypes)
    frappe.cache.set_value(key, result, expires_in_sec=84000)
    result = get_translated_label(result)
    result = get_system_fields() + result

    return result


def get_translated_label(fields):
    for f in fields:
        # Check if the fieldname contains a dot, indicating a child table field
        if "." in f.get("value"):
            label_parts = f.get("label").split(" → ")
            # Translate each part of the label and join them back
            label_parts = [_(part) for part in label_parts]
            f["label"] = " → ".join(label_parts)
        else:
            f["label"] = _(f["label"])
    return fields


def get_common_fields_in(doctypes):
    if not doctypes:
        return []

    common_fields_map = {}
    field_count = {}

    for doctype in doctypes:
        meta = frappe.get_meta(doctype)
        seen = set()

        def add_field(fieldname, fieldtype, options, label):
            key = (fieldname, fieldtype, options)
            if key not in seen:
                seen.add(key)
                field_count[key] = field_count.get(key, 0) + 1
                common_fields_map[key] = {
                    "label": label,
                    "value": fieldname,
                    "fieldtype": fieldtype,
                    "options": options,
                }

        for field in meta.fields:
            if field.fieldtype not in no_value_fields:
                add_field(field.fieldname, field.fieldtype, field.options, field.label)

        for table_field in meta.get_table_fields():
            child_meta = frappe.get_meta(table_field.options)
            for child_field in child_meta.fields:
                if child_field.fieldtype not in no_value_fields:
                    full_fieldname = f"{table_field.fieldname}.{child_field.fieldname}"
                    full_label = f"{table_field.label} → {child_field.label}"
                    add_field(
                        full_fieldname,
                        child_field.fieldtype,
                        child_field.options,
                        full_label,
                    )

    # Filter to only fields that appear in all doctypes
    total = len(doctypes)
    return [
        common_fields_map[key] for key, count in field_count.items() if count == total
    ]


@frappe.whitelist()
def get_field_options(doctype: str) -> list:
    """
    Get field options for a doctype with caching

    :param doctype: The document type to get field options for
    :return: List of field options dictionaries
    """
    if not doctype:
        frappe.throw("get_field_options called without doctype")

    cache_key = f"field_options:{doctype}"
    cached = frappe.cache.get_value(cache_key)

    if cached:
        return cached

    result = _get_field_options(doctype)
    frappe.cache.set_value(cache_key, result, expires_in_sec=3600)
    return result


def _get_field_options(doctype):
    """Return all available fields including child tables and system fields"""
    if not doctype:
        return []

    meta = frappe.get_meta(doctype)
    options = []

    system_fields = [
        {
            "label": _("ID") + " (name)",
            "value": "name",
            "fieldtype": "Data",
            "options": None,
        },
        {
            "label": _("Document Status") + " (docstatus)",
            "value": "docstatus",
            "fieldtype": "Select",
            "options": "0\n1\n2",
        },
        {
            "label": _("Created At") + " (creation)",
            "value": "creation",
            "fieldtype": "Datetime",
            "options": None,
        },
        {
            "label": _("Created By") + " (owner)",
            "value": "owner",
            "fieldtype": "Link",
            "options": "User",
        },
        {
            "label": _("Modified At") + " (modified)",
            "value": "modified",
            "fieldtype": "Datetime",
            "options": None,
        },
        {
            "label": _("Modified By") + " (modified_by)",
            "value": "modified_by",
            "fieldtype": "Link",
            "options": "User",
        },
    ]
    options.extend(system_fields)

    for field in meta.fields:
        if field.fieldtype not in no_value_fields:
            options.append(
                {
                    "label": _(f"{field.label}") + f" ({field.fieldname})",
                    "value": field.fieldname,
                    "fieldtype": field.fieldtype,
                    "options": field.options,
                }
            )

    for table_field in meta.get_table_fields():
        child_meta = frappe.get_meta(table_field.options)
        for child_field in child_meta.fields:
            if child_field.fieldtype not in no_value_fields:
                options.append(
                    {
                        "label": _(f"{table_field.label}")
                        + " → "
                        + _(f"{child_field.label}"),
                        "value": f"{table_field.fieldname}.{child_field.fieldname}",
                        "fieldtype": child_field.fieldtype,
                        "options": child_field.options,
                    }
                )

    return options
