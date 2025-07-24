# -----------------------------------------------------------------------------
# uph.unified_data_tools.mdm.auto_text_generator_engine.py
# Project Name: UPH - Unified Party Hub
# File: auto_text_generator_engine.py
# Description: Provides the Auto Text generator for generating custom remarks based on rules and templates for documents in the UPH system.
#
# Author: Abdo Ruzaqi(Sendipad)
# Created: 2025-04-10
# License: GNU General Public License v3.0 (GPL-3.0)
# Repository: https://github.com/Sendipad/uph
#
# Copyright (c) 2025 Abdo Ruzaqi(Sendipad)
# This file is part of the UPH project and is released under the GPL-3.0 license.
# See LICENSE file or https://www.gnu.org/licenses/gpl-3.0.en.html for full terms.
# -----------------------------------------------------------------------------
import frappe
from frappe import _
import re
from collections import defaultdict
from frappe.utils.caching import redis_cache

# No imports from auto_text_generator_rule.py here for the functions defined below,
# as they are now defined here. We will still need to retrieve AutoTextGeneratorRule
# DocType objects using frappe.get_cached_doc() to access their methods and fields.

# Define the markers for text manipulation using regex
APPEND_MARKER = r"\*\*\s*(.*?)\s*\*\*"  # ** text ** for append
PREPEND_MARKER = r"\*\*\*\s*(.*?)\s*\*\*\*"  # *** text *** for prepend
OVERWRITE_MARKER = r"\/\/\s*(.*?)\s*\/\/"  # // text // for full overwrite


def _process_and_merge_text(
    rule_doc, current_value: str, context: dict, is_submitting: bool
) -> str:
    compiled_template = rule_doc._get_compiled_template()
    if not compiled_template:
        return current_value

    rendered_text = compiled_template.render(context).strip()
    final_text = current_value

    # --- Marker-based merge (from existing value!) ---
    overwrite_match = re.search(OVERWRITE_MARKER, current_value)
    prepend_match = re.search(PREPEND_MARKER, current_value)
    append_match = re.search(APPEND_MARKER, current_value)

    markers_were_present = bool(overwrite_match or prepend_match or append_match)

    if overwrite_match:
        if not current_value.strip():
            final_text = rendered_text
        else:
            # Replace marker with rendered
            final_text = re.sub(OVERWRITE_MARKER, rendered_text, current_value)
    elif prepend_match:
        final_text = re.sub(PREPEND_MARKER, rendered_text + r"\g<0>", current_value)
    elif append_match:
        final_text = re.sub(APPEND_MARKER, r"\g<0>" + rendered_text, current_value)
    else:
        # No marker? Fallback to text_merge_mode logic
        if rule_doc.text_merge_mode == "Overwrite":
            if not current_value.strip():
                final_text = rendered_text
        elif rule_doc.text_merge_mode == "Append":
            final_text = current_value + rendered_text
        elif rule_doc.text_merge_mode == "Prepend":
            final_text = rendered_text + current_value

    # --- Marker removal ---
    should_remove_markers = (rule_doc.remove_markers_on_submit and is_submitting) or (
        not is_submitting and markers_were_present
    )

    if should_remove_markers:
        final_text = re.sub(OVERWRITE_MARKER, r"\g<1>", final_text)
        final_text = re.sub(PREPEND_MARKER, r"\g<1>", final_text)
        final_text = re.sub(APPEND_MARKER, r"\g<1>", final_text)
        final_text = final_text.strip()

    return final_text.strip()


def text_generator(doc, method=None):
    # Only proceed if applicable
    if doc.doctype not in get_cached_set_document_types() or not method:
        return
    _text_generator(doc, method=None)


def evaluate_filters(conditions, doc_context):
    for cond in conditions:
        field_parts = cond.fieldname.split(".", 1)
        if len(field_parts) == 2:
            field = field_parts[1]
        else:
            field = cond.fieldname

        value = doc_context.get(field)
        if not match_condition(value, cond.condition, cond.value):
            return False
    return True


def match_condition(field_value, operator, condition_value):
    if operator == "==":
        return str(field_value) == str(condition_value)
    elif operator == "!=":
        return str(field_value) != str(condition_value)
    elif operator == ">":
        try:
            return float(field_value) > float(condition_value)
        except (ValueError, TypeError):
            return False
    elif operator == "<":
        try:
            return float(field_value) < float(condition_value)
        except (ValueError, TypeError):
            return False
    elif operator == ">=":
        try:
            return float(field_value) >= float(condition_value)
        except (ValueError, TypeError):
            return False
    elif operator == "<=":
        try:
            return float(field_value) <= float(condition_value)
        except (ValueError, TypeError):
            return False
    elif operator == "in":
        try:
            values = frappe.parse_json(condition_value)
            return field_value in values
        except Exception:
            if isinstance(field_value, str) and isinstance(condition_value, str):
                return field_value in [v.strip() for v in condition_value.split(",")]
            return False
    elif operator == "not in":
        try:
            values = frappe.parse_json(condition_value)
            return field_value not in values
        except Exception:
            if isinstance(field_value, str) and isinstance(condition_value, str):
                return field_value not in [
                    v.strip() for v in condition_value.split(",")
                ]
            return False
    elif operator == "is set":
        return field_value is not None and field_value != ""
    elif operator == "not set":
        return field_value is None or field_value == ""
    else:
        return False


def _text_generator(doc, method=None):
    if not method:
        method = "before save"

    is_submitting = method.lower() == "on submit"
    force_run = frappe.flags.get("force_generate_auto_text", False)

    rule_names = (
        get_document_type_run_validate_events(document_type=doc.doctype, method=method)
        or []
    )

    if not rule_names:
        return

    context_parent = {"doc": doc.as_dict()}

    for rule_name in rule_names:
        rule_doc = frappe.get_cached_doc("Auto Text Generator Rule", rule_name)

        if not rule_doc.template or not rule_doc.template.strip():
            continue

        run_rule = True
        fields_changed = False
        run_anyway = False

        # --- Dependency Fields Check ---
        if method.lower() == "before save" and rule_doc.dependency_fields:
            dependencies = [
                f.strip() for f in rule_doc.dependency_fields.split(",") if f.strip()
            ]
            is_new_doc = doc.is_new()
            old_doc = None

            if not is_new_doc:
                try:
                    if (
                        hasattr(doc, "get_doc_before_save")
                        and doc.get_doc_before_save()
                    ):
                        old_doc = doc.get_doc_before_save()
                    else:
                        old_doc = frappe.get_doc(doc.doctype, doc.name)
                except Exception as e:
                    frappe.log_error(
                        f"Could not retrieve old document: {e}",
                        "AutoTextGenerator Rule",
                    )
                    old_doc = None

            for dep_field in dependencies:
                if "." in dep_field:
                    table_name, child_field_name = dep_field.split(".", 1)
                    new_rows = doc.get(table_name) or []
                    old_rows = old_doc.get(table_name) if old_doc else []

                    if len(new_rows) != len(old_rows):
                        fields_changed = True
                        break

                    new_dict = {
                        r.name: r.as_dict() for r in new_rows if hasattr(r, "name")
                    }
                    old_dict = {
                        r.name: r.as_dict() for r in old_rows if hasattr(r, "name")
                    }

                    for name in new_dict:
                        if name not in old_dict:
                            fields_changed = True
                            break
                        if new_dict[name].get(child_field_name) != old_dict[name].get(
                            child_field_name
                        ):
                            fields_changed = True
                            break
                    if fields_changed:
                        break
                else:
                    if is_new_doc and doc.get(dep_field):
                        fields_changed = True
                        break
                    elif not is_new_doc and doc.has_value_changed(dep_field):
                        fields_changed = True
                        break

            # Fallback: if remark field is empty, allow execution
            if rule_doc.on_child and "." in rule_doc.target_field:
                table_field, child_field = rule_doc.target_field.split(".", 1)
                for row in doc.get(table_field, []):
                    val = row.get(child_field)
                    if val is None or not str(val).strip():
                        run_anyway = True
                        break
            else:
                val = doc.get(rule_doc.target_field)
                if val is None or not str(val).strip():
                    run_anyway = True

            run_rule = force_run or fields_changed or run_anyway

        if not run_rule:
            continue

        # --- Child Table Case ---
        if rule_doc.on_child:
            if "." not in rule_doc.target_field:
                frappe.log_error(
                    f"Invalid target_field for child rule {rule_name}: {rule_doc.target_field}",
                    "AutoTextGeneratorRule Error",
                )
                continue

            table_field, child_field = rule_doc.target_field.split(".", 1)
            rows = doc.get(table_field, [])

            for row in rows:
                context = {"doc": row.as_dict(), "parent": doc.as_dict()}
                if evaluate_filters(rule_doc.conditions, row):
                    try:
                        current_value = row.get(child_field) or ""
                        merged_remark = _process_and_merge_text(
                            rule_doc, current_value, context, is_submitting
                        )
                        if merged_remark != current_value:
                            row.set(child_field, merged_remark)
                            frappe.msgprint(
                                _("Text Set by Rule {0} to: {1} at row {2}").format(
                                    rule_doc.title, merged_remark, row.idx
                                ),
                                alert=1,
                            )
                    except Exception as e:
                        frappe.log_error(
                            f"Render/Merge error (child): {e} for rule {rule_name}",
                            "AutoTextGenerator Rule",
                        )

        # --- Parent Field Case ---
        else:
            if evaluate_filters(rule_doc.conditions, doc):
                try:
                    current_value = doc.get(rule_doc.target_field) or ""
                    merged_remark = _process_and_merge_text(
                        rule_doc,
                        current_value,
                        context_parent,
                        is_submitting,
                    )
                    if merged_remark != current_value:
                        doc.set(rule_doc.target_field, merged_remark)
                        frappe.msgprint(
                            _("Text Set by Rule {0} to: {1}").format(
                                rule_doc.title, merged_remark
                            ),
                            alert=1,
                        )
                except Exception as e:
                    frappe.log_error(
                        f"Render/Merge error (parent): {e} for rule {rule_name}",
                        "AutoTextGenerator Rule",
                    )

    return doc


@frappe.whitelist()
def generate_remarks_for_save_doc(doctype, docname, rule_name=None):
    """
    Forcefully runs Auto Text Generator rules on a saved document,
    optionally filtering by a specific rule name. Designed for testing/debugging.
    """
    doc = frappe.get_doc(doctype, docname)

    frappe.flags.force_generate_auto_text = True
    _text_generator(doc, method="before save")

    # Save the document after modification
    doc.save()

    return _("Text generation complete for {0}").format(docname)


@frappe.whitelist()
@redis_cache()
def get_document_type_run_validate_events(document_type=None, method=None):
    """Get rules filtered by doctype and event method"""
    filters = [["enabled", "=", 1], ["validate_on_event", "not in", ["", None]]]

    if document_type:
        filters.append(["document_type", "=", document_type])

    if method:
        filters.append(["validate_on_event", "like", method.lower()])

    rules = frappe.get_all(
        "Auto Text Generator Rule",
        filters=filters,
        order_by="priority desc",
        fields=[
            "name",
            "document_type",
            "validate_on_event",
            "text_merge_mode",
            "remove_markers_on_submit",
            "dependency_fields",
            "on_child",
            "target_field",
        ],
    )

    if method:
        return [rule.name for rule in rules]

    result = defaultdict(lambda: defaultdict(list))
    for rule in rules:
        event_key = rule.validate_on_event.lower()
        result[rule.document_type][event_key].append(rule.name)

    return {doctype: dict(events) for doctype, events in result.items()}


def get_cached_set_document_types():
    key = "Auto Text Generator Rule.set_of_document_types"
    cached_value = frappe.cache.get_value(key)
    if cached_value:
        return cached_value

    document_types = frappe.get_all(
        "Auto Text Generator Rule", filters={"enabled": 1}, fields=["document_type"]
    )
    document_types = list(set([d.document_type for d in document_types]))

    frappe.cache.set_value(key, document_types)
    return document_types


def delete_set_document_types_cache():
    key = "Auto Text Generator Rule.set_of_document_types"
    frappe.cache.delete_value(key)
    return True
