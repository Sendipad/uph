# apps/uph/uph/hub/mdm/integrity_validation_service.py

import frappe
from frappe import _
from uph.hub.services.base import BaseRuleService
from uph.hub.services.registry import core_register
from uph.hub.services.condition_tree import ConditionEvaluator
from uph.hub.services.context_builder import build_context
from uph.hub.services.action_executor import ActionExecutor


@core_register
class IntegrityValidationService(BaseRuleService):
    service_type = "IntegrityValidation"
    execution_mode = "event"
    label = _("Integrity Validation Service")

    def evaluate_event(self, context):
        doc = context["doc"]
        if not self.passes_rule_scopes(doc):
            return

        evaluator = ConditionEvaluator(self.rule.name)
        passed = evaluator.evaluate(context)

        if not passed:
            context["integrity_failed"] = True
            context["violations"] = self.build_violation_log(context, evaluator)
            self.execute_actions(context)

    def evaluate_batch(self, context):
        """Batch validation across a filtered dataset"""
        doctype = self.rule.document_type
        filters = context.get("filters", {})
        names = frappe.get_all(doctype, filters=filters, pluck="name", limit=1000)

        for name in names:
            try:
                doc = frappe.get_doc(doctype, name)
                ctx = build_context(doc, self.rule, event_type="batch")
                self.evaluate_event(ctx)
            except Exception as e:
                frappe.log_error(f"Integrity batch error: {doctype} {name}", str(e))

    def build_violation_log(self, context, evaluator):
        """Build trace of failed condition paths or fields"""
        violations = []
        for field in evaluator.get_required_fields():
            val = context["resolve_value"](field)
            violations.append({"field": field, "value": val})
        return violations

    def execute_actions(self, context):
        if not self.rule.actions:
            frappe.msgprint(
                _("Record failed integrity check for Rule: {0}").format(self.rule.name),
                alert=True,
            )
        else:
            executor = ActionExecutor()
            executor.execute(self.rule.actions, context)

    @classmethod
    def validate_rule_doc(cls, rule_doc):
        """Ensure all Rule Conditions have required integrity fields"""
        missing = []
        for cond in rule_doc.get("conditions", []):
            if not cond.final_left_field_path:
                missing.append(cond.idx)
        if missing:
            frappe.throw(
                _("Rule Conditions missing left field path at rows: {0}").format(
                    ", ".join(str(i) for i in missing)
                )
            )
