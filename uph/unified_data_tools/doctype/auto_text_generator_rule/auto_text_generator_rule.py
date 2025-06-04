# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt


from collections import defaultdict
import frappe
from jinja2 import Environment, exceptions

from frappe.model.document import Document
from frappe.utils.caching import redis_cache
from uph.unified_data_tools.utils.field import get_field_options
from frappe import _


class AutoTextGeneratorRule(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from uph.unified_data_tools.doctype.custom_remark_rule_condition.custom_remark_rule_condition import (
            CustomRemarkRuleCondition,
        )

        conditions: DF.Table[CustomRemarkRuleCondition]
        dependency_fields: DF.Data | None
        document_type: DF.Link
        enabled: DF.Check
        on_child: DF.Check
        priority: DF.Int
        remark_fieldname: DF.Autocomplete
        template: DF.HTMLEditor | None
        title: DF.Data | None
        validate_on_event: DF.Literal["", "Before Insert", "Before Save", "On Submit"]
    # end: auto-generated types

    def clear_cache(self):
        get_document_type_run_validate_events.clear_cache()
        return super().clear_cache()

    def validate(self):
        env = Environment()
        try:
            # Parse the template to check syntax errors
            env.parse(self.template or "")
        except exceptions.TemplateSyntaxError as e:
            # Raise a validation error with info about the syntax problem
            frappe.throw(f"Template syntax error at line {e.lineno}: {e.message}")

    def before_save(self):
        if not self.title:
            if self.remark_fieldname:
                fields = get_field_options(self.document_type)
                fields = [
                    f.get("label")
                    for f in fields
                    if f.get("value") == self.remark_fieldname
                ]
                if fields:
                    self.title = _("{0} : {1}").format(
                        _(self.document_type), _(fields[0])
                    )
                else:
                    self.title = _("{0} : {1}").format(
                        _(self.document_type), self.remark_fieldname
                    )


@frappe.whitelist()
@redis_cache()
def get_document_type_run_validate_events(document_type=None, method=None):
    """Get rules filtered by doctype and event method"""
    # Build base filters
    filters = [["enabled", "=", 1], ["validate_on_event", "not in", ["", None]]]

    # Add document type filter if provided
    if document_type:
        filters.append(["document_type", "=", document_type])

    # Add method filter if provided (case-insensitive)
    if method:
        filters.append(["validate_on_event", "like", method.lower()])

    # Fetch matching rules
    rules = frappe.get_all(
        "Auto Text Generator Rule",
        filters=filters,
        order_by="priority desc",
        fields=["name", "document_type", "validate_on_event"],
    )

    # Return rule names if method is specified
    if method:
        return [rule.name for rule in rules]

    # Group by doctype and event if no method specified
    result = defaultdict(lambda: defaultdict(list))
    for rule in rules:
        event_key = rule.validate_on_event.lower()
        result[rule.document_type][event_key].append(rule.name)

    return {doctype: dict(events) for doctype, events in result.items()}
