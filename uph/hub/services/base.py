import frappe
import time
from frappe import _
from abc import ABC, abstractmethod
from .context_builder import build_context as build_base_context


class BaseRuleService(ABC):
    """
    Abstract base class for all rule services.
    Implements execution routing, condition scope filtering,
    caching, error handling, and trace reporting.
    """

    service_type = None  # Must be set by subclass
    execution_mode = "event"  # Default execution mode (can be "batch", "manual")

    def __init__(self, rule_doc):
        if not self.service_type:
            frappe.throw(
                _("Service type not defined for {0}").format(self.__class__.__name__)
            )
        self.rule = rule_doc
        self.cache_key = f"service_{self.service_type}_{rule_doc.name}"

    def run(self, context=None, mode=None, **kwargs):
        """
        Main entry point for executing the rule service
        Handles dispatching, trace logging, scope filtering and error capture.
        """
        mode = mode or self.execution_mode
        method_name = f"evaluate_{mode}"
        method = getattr(self, method_name, None)

        if not method:
            frappe.throw(
                _("Execution mode '{0}' not supported by {1}").format(
                    mode, self.service_type
                )
            )

        # Build context if not already passed
        if context is None:
            context = build_base_context(
                doc=kwargs.get("doc"),
                rule=self.rule,
                event_type=kwargs.get("event_type"),
            )

        # Add service-specific metadata
        context.update(
            {
                "service": self,
                "service_type": self.service_type,
            }
        )

        # Skip this rule or service if explicitly flagged
        if context.get(f"skip_rule::{self.rule.name}") or context.get(
            f"skip_service::{self.service_type}"
        ):
            context.setdefault("trace", []).append(
                f"⏭️ Skipped: {self.service_type} / Rule '{self.rule.name}'"
            )
            return

        start = time.time()
        try:
            result = method(context, **kwargs)
            context.setdefault("trace", []).append(
                f"✅ {self.service_type} '{self.rule.name}' executed in {round(time.time() - start, 3)}s"
            )
            return result
        except Exception as e:
            self.handle_service_error(e, context)
            context.setdefault("trace", []).append(
                f"❌ {self.service_type} '{self.rule.name}' failed: {str(e)}"
            )

    def run_safe(self, context=None, mode=None, **kwargs):
        """
        Safe wrapper that swallows any exceptions
        (useful for background/batch jobs)
        """
        try:
            return self.run(context=context, mode=mode, **kwargs)
        except Exception:
            return None

    def passes_scope_filter(self, doc, scope) -> bool:
        """
        Checks if a document matches a specific RuleScope
        Includes support for docstatus and advanced filter JSON
        """
        # Docstatus match
        if scope.apply_when_docstatus_is != "Any":
            if str(doc.docstatus) != scope.apply_when_docstatus_is:
                return False

        # JSON filter
        if scope.apply_filter_json:
            try:
                filters = frappe.parse_json(scope.apply_filter_json)
                for field, condition in filters.items():
                    value = doc.get(field)

                    if isinstance(condition, dict):
                        op = condition.get("operator", "==")
                        target = condition.get("value")

                        if op == "==" and value != target:
                            return False
                        elif op == "!=" and value == target:
                            return False
                        elif op == ">" and not (value > target):
                            return False
                        elif op == "<" and not (value < target):
                            return False
                        elif op == ">=" and not (value >= target):
                            return False
                        elif op == "<=" and not (value <= target):
                            return False
                        elif op == "in" and value not in target:
                            return False
                        elif op == "not in" and value in target:
                            return False
                    else:
                        if value != condition:
                            return False
            except Exception as e:
                frappe.log_error(
                    f"Invalid apply_filter_json in RuleScope\n{scope.apply_filter_json}\n{e}",
                    "RuleScopeError",
                )
                return False

        return True

    def passes_rule_scopes(self, doc):
        """
        Returns True if document passes at least one scope
        """
        if not self.rule.get("apply_scopes"):
            return True

        return any(
            self.passes_scope_filter(doc, scope) for scope in self.rule.apply_scopes
        )

    def handle_service_error(self, error, context):
        """
        Standard logging + trace capture for any rule failure
        """
        doc = context.get("doc", {})
        frappe.log_error(
            title=_("Rule service error: {0}").format(self.service_type),
            message=_("Rule: {0}\nDoc: {1}\nError: {2}").format(
                self.rule.name,
                getattr(doc, "name", "N/A"),
                str(error),
            ),
        )
        context.setdefault("errors", []).append(str(error))

    # -------------------- Mode Methods --------------------

    @abstractmethod
    def evaluate_event(self, context):
        """Required. Triggered on event-based doc hooks"""
        raise NotImplementedError(_("Event execution not implemented"))

    def evaluate_batch(self, context):
        """Override this for long-running/batch jobs"""
        frappe.throw(
            _("Batch execution not implemented for {0}").format(self.service_type)
        )

    def evaluate_manual(self, context):
        """Optional: override for admin/test calls"""
        frappe.throw(
            _("Manual execution not implemented for {0}").format(self.service_type)
        )

    # -------------------- Metadata & UI --------------------

    @classmethod
    def validate_rule_doc(cls, rule_doc):
        """
        Optional validation hook for Rule save
        """
        pass

    @classmethod
    def get_custom_fields(cls):
        """
        Optional field injector
        Return structure like:
        {
            "Rule": [field_def],
            "Rule Condition": [field_def],
            "Rule Action": [field_def]
        }
        """
        return {}

    def get_filter_summary(self):
        """
        Utility: summarize all filters for UI/debug
        """
        filters = []
        for scope in self.rule.get("apply_scopes", []):
            filters.append(
                f"{scope.document_type} [{scope.evaluation_event}] → {scope.apply_filter_json}"
            )
        return filters

    # -------------------- Redis Cache Helpers --------------------

    def get_cached_data(self, key, generator, expiry=3600):
        """
        Per-rule/service cache helper
        Automatically generates + stores if not present
        """
        cache_key = f"{self.cache_key}_{key}"
        cached = frappe.cache().get_value(cache_key)
        if cached is not None:
            return cached

        data = generator()
        frappe.cache().set_value(cache_key, data, expires_in_sec=expiry)
        return data

    def clear_cache(self, key=None):
        """
        Clear any sub-cache values for this service
        """
        if key:
            frappe.cache().delete_key(f"{self.cache_key}_{key}")
        else:
            for k in frappe.cache().get_keys(f"{self.cache_key}_*"):
                frappe.cache().delete_key(k)
