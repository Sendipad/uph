# File uph/hub/utils/field.py
import frappe
from frappe import _
from frappe.model import no_value_fields


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


def get_system_fields():
    """Return system fields that are always available"""
    return [
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
