# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt


from collections import defaultdict
import frappe
from frappe.model.document import Document
from frappe.utils.caching import redis_cache


class CustomRemarkRule(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from uph.unified_data_tools.doctype.custom_remark_rule_condition.custom_remark_rule_condition import (
            CustomRemarkRuleCondition,
        )

        conditions: DF.Table[CustomRemarkRuleCondition]
        document_type: DF.Link
        enabled: DF.Check
        on_child: DF.Check
        priority: DF.Int
        remark_fieldname: DF.Autocomplete
        template: DF.HTMLEditor | None
        validate_on_event: DF.Literal[
            "",
            "Before Insert",
            "Before Save",
            "Validate",
            "On Submit",
            "On Cancel",
            "On Update After Submit",
        ]
    # end: auto-generated types

    def clear_cache(self):
        get_document_type_run_validate_events.clear_cache()
        return super().clear_cache()


@frappe.whitelist()
@redis_cache()
def get_document_type_run_validate_events(document_type=None):
    filters = {"enabled": 1, "validate_on_event": ["!=", ""]}
    if document_type:
        filters["document_type"] = document_type
    rulesets = frappe.get_all(
        "Custom Remark Rule",
        filters=filters,
        order_by="priority desc",
        fields=["name", "document_type", "validate_on_event"],
    )
    result = defaultdict(lambda: defaultdict(list))

    for job in rulesets:
        result[job.document_type][job.validate_on_event].append(job.name)

    # Convert nested defaultdicts to normal dicts before returning
    return {doctype: dict(events) for doctype, events in result.items()}
