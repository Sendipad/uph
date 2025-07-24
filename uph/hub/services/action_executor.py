# uph/hub/services/action_executor.py
import frappe
import json


class ActionExecutor:
    __slots__ = ("handlers",)

    def __init__(self):
        self.handlers = {
            "block_saving": self.handle_block_saving,
            "add_error": self.handle_add_error,
            "add_warning": self.handle_add_warning,
            "set_custom_status": self.handle_set_custom_status,
            "raise_error": self.handle_raise_error,
            "show_warning": self.handle_show_warning,
            "set_field_value": self.handle_set_field_value,
            "call_registered_method": self.handle_call_registered_method,
        }

    def handle_block_saving(self, action, context):
        """Block document from being saved"""
        context["doc"].block_saving = True
        context.setdefault("errors", []).append(
            action.custom_message or "Document saving blocked due to validation errors"
        )

    def handle_add_error(self, action, context):
        """Add custom error message"""
        context.setdefault("errors", []).append(
            action.custom_message or "Validation error"
        )

    def handle_add_warning(self, action, context):
        """Add custom warning message"""
        context.setdefault("warnings", []).append(
            action.custom_message or "Validation warning"
        )

    def handle_set_custom_status(self, action, context):
        """Set custom document status"""
        doc = context["doc"]
        if hasattr(doc, "status"):
            doc.status = action.status_value
            context.setdefault("info", []).append(
                f"Status changed to: {action.status_value}"
            )

    def execute(self, actions, context):
        """Execute actions with proper error handling"""
        for action in actions:
            action_type = action.action_type.replace(" ", "_").lower()
            handler = self.handlers.get(action_type, self.handle_unknown)
            try:
                handler(action, context)
            except Exception as e:
                self.log_error(action, e)

    def handle_raise_error(self, action, context):
        message = action.custom_message or "Validation error"
        context["errors"].append(message)

    def handle_show_warning(self, action, context):
        message = action.custom_message or "Warning"
        context["warnings"].append(message)

    def handle_set_field_value(self, action, context):
        doc = context["doc"]
        field = action.target_field
        value = context.get("variables", {}).get(action.source_variable)

        if value is not None and hasattr(doc, field):
            doc.set(field, value)

    def handle_call_registered_method(self, action, context):
        method = frappe.get_cached_doc("Registered Method", action.method_name)
        params = json.loads(action.parameters or "{}")
        resolved_params = {k: self.resolve_param(v, context) for k, v in params.items()}
        result = frappe.call(method.method, **resolved_params)

        if action.result_variable:
            context["variables"][action.result_variable] = result

    def resolve_param(self, value, context):
        """Resolve context variables in parameters"""
        if isinstance(value, str) and value.startswith("ctx:"):
            return context["variables"].get(value[4:])
        return value

    def handle_unknown(self, action, context):
        frappe.log_error(
            f"Unhandled action: {action.action_type}", "ActionExecutionError"
        )

    def log_error(self, action, error):
        frappe.log_error(
            title=f"Action failed: {action.action_type}",
            message=f"Action: {action.name}\nError: {str(error)}",
        )
