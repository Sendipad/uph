import frappe
import json
from frappe import _
from frappe.utils.background_jobs import enqueue
from uph.hub.services.base import BaseRuleService
from uph.hub.utils.normalizer import normalizer
from uph.hub.services.registry import core_register


@core_register
class NormalizationService(BaseRuleService):
    service_type = "Normalization"
    execution_mode = "event"
    label = _("Normalization Service")

    def evaluate_event(self, context):
        """Apply normalization rules to document fields"""
        doc = context["doc"]

        if not frappe.db.exists(doc.doctype, doc.name):
            frappe.log_error(
                title="Normalization Skipped: Document Not Found",
                message=f"{doc.doctype} {doc.name} not found in DB.\nRule: {self.rule.name}",
            )
            return

        for condition in self.rule.conditions:
            self.process_condition(doc, condition, context)

    def process_condition(self, doc, condition, context):
        """Process a single normalization condition"""
        try:
            if not all(
                [
                    condition.operator == "normalize_field",
                    condition.normalization_profile,
                    condition.left_field_path,
                ]
            ):
                return

            field_path = condition.left_field_path
            current_value = context["resolve_value"](field_path)

            if current_value is None:
                return

            profile = condition.normalization_profile

            try:
                params = json.loads(condition.right_value_literal or "{}")
            except json.JSONDecodeError as je:
                self.log_error(
                    error=je,
                    doc=doc,
                    field_path=field_path,
                    condition=condition,
                    extra="Invalid JSON in right_value_literal",
                )
                params = {}

            normalized = normalizer(str(current_value), profile, params)

            if normalized != current_value:
                self.update_document_field(doc, field_path, normalized)
                self.create_audit_record(
                    doc, field_path, current_value, normalized, profile
                )

        except Exception as e:
            self.log_error(
                e,
                doc,
                getattr(condition, "left_field_path", "unknown"),
                condition=condition,
            )

    def update_document_field(self, doc, field_path, value):
        """Update document field safely"""
        if "." in field_path:
            parts = field_path.split(".")
            parent_field = getattr(doc, parts[0], [])

            if len(parts) == 3 and parts[1].isdigit():
                idx = int(parts[1])
                if idx < len(parent_field):
                    parent_field[idx].set(parts[2], value)
            elif len(parts) == 2 and hasattr(parent_field, "set"):
                parent_field.set(parts[1], value)
        else:
            if hasattr(doc, field_path):
                doc.set(field_path, value)

    def create_audit_record(self, doc, field_path, original, normalized, profile):
        """Create normalization audit record"""
        frappe.get_doc(
            {
                "doctype": "Normalization Record",
                "document_type": doc.doctype,
                "docname": doc.name,
                "field_path": field_path,
                "original_data": original,
                "normalized_data": normalized,
                "normalization_profile": profile,
            }
        ).insert(ignore_permissions=True, ignore_if_duplicate=True)

    def log_error(self, error, doc, field_path, condition=None, extra=None):
        """Detailed error logging with context and traceback"""
        message = (
            f"Document: {doc.doctype} {doc.name}\n"
            f"Rule: {self.rule.name}\n"
            f"Field: {field_path}\n"
            f"Condition: {getattr(condition, 'name', 'N/A')}\n"
            f"Error: {str(error)}\n"
            f"Traceback:\n{frappe.get_traceback()}"
        )
        if extra:
            message = f"{extra}\n" + message

        frappe.log_error(title="Normalization failed", message=message)

    def evaluate_batch(self, context):
        """Batch processing implementation"""
        doctype = self.rule.document_type

        if not frappe.db.exists("DocType", doctype):
            frappe.log_error(
                title="Normalization Error: DocType Missing",
                message=f"DocType {doctype} does not exist.\nRule: {self.rule.name}",
            )
            return

        names = frappe.get_all(doctype, pluck="name")
        chunk_size = 50

        for i in range(0, len(names), chunk_size):
            enqueue(
                "uph.hub.mdm.normalization_service.process_batch",
                queue="long",
                timeout=1800,
                doctype=doctype,
                names=names[i : i + chunk_size],
                rule_name=self.rule.name,
                enqueue_after_commit=True,
            )


def process_batch(doctype, names, rule_name):
    rule = frappe.get_cached_doc("Rule", rule_name)
    service = NormalizationService(rule)

    for name in names:
        try:
            if frappe.db.exists(doctype, name):
                doc = frappe.get_doc(doctype, name)
                context = {
                    "doc": doc,
                    "rule": rule,
                    "resolve_value": lambda path: resolve_field_value(doc, path),
                }
                service.evaluate_event(context)
                doc.save(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(
                title="Batch normalization failed",
                message=f"{doctype} {name}\nError: {str(e)}\n{frappe.get_traceback()}",
            )


def resolve_field_value(doc, path):
    """Resolve field value with error handling"""
    try:
        parts = path.split(".")
        value = doc
        for part in parts:
            if isinstance(value, list) and part.isdigit():
                value = value[int(part)] if int(part) < len(value) else None
            elif hasattr(value, "get"):
                value = value.get(part)
            else:
                value = getattr(value, part, None)
            if value is None:
                break
        return value
    except Exception:
        frappe.log_error(
            title="Field Path Resolution Failed",
            message=f"Path: {path}\nDoc: {doc.doctype} {doc.name}\n{frappe.get_traceback()}",
        )
        return None


@frappe.whitelist()
def run_normalization_batch(doctype, names, rule_name):
    # Ensure names is a list (handle JSON string or actual list)
    if isinstance(names, str):
        try:
            names = json.loads(names)  # Parse JSON string to list
        except json.JSONDecodeError:
            names = [names]  # Fallback to single-item list

    # Ensure names is always a list
    if not isinstance(names, list):
        names = [names]

    rule = frappe.get_cached_doc("Rule", rule_name)
    service = NormalizationService(rule)

    for name in names:
        try:
            doc = frappe.get_doc(doctype, name)
            context = {
                "doc": doc,
                "trace": [],
                "variables": {},
                "resolve_value": lambda field: doc.get(field.split(".")[-1]),
            }
            service.evaluate_event(context)
            doc.save(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(
                title="Normalization failed (manual batch)",
                message=f"{doctype} {name}\nError: {str(e)}\n{frappe.get_traceback()}",
            )
