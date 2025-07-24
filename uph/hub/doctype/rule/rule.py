# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt
from frappe.model.document import Document

# from uph.hub.services.condition_tree import ConditionTreeBuilder
from uph.hub.services.registry import get_service
from uph.hub.services.cache import clear_rule_caches, set_rule_last_updated


class Rule(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from uph.hub.doctype.rule_action.rule_action import RuleAction
        from uph.hub.doctype.rule_condition.rule_condition import RuleCondition
        from uph.hub.doctype.rule_scope.rule_scope import RuleScope

        actions: DF.Table[RuleAction]
        apply_scopes: DF.Table[RuleScope]
        conditions: DF.Table[RuleCondition]
        debug_mode: DF.Check
        default_alert_message: DF.SmallText | None
        document_type: DF.Link | None
        evaluation_count: DF.Int
        is_active: DF.Check
        last_evaluated: DF.Datetime | None
        match_threshold: DF.Float
        priority: DF.Int
        rule_service_type: DF.Link
        title: DF.Data
    # end: auto-generated types

    def before_save(self):
        service_cls = get_service(self.rule_service_type)
        if service_cls:
            service_cls.validate_rule_doc(self)

        if self.is_new():
            set_rule_last_updated()

    def after_save(self):
        clear_rule_caches(self.name)

    def after_rename(self, old_name, new_name, merge):
        clear_rule_caches(old_name)
        clear_rule_caches(new_name)

    def on_trash(self):
        clear_rule_caches(self.name)
