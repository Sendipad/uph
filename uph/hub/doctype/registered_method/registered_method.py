# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt
from frappe import _
import json
import importlib
import frappe
from frappe.model.document import Document


class RegisteredMethod(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from uph.hub.doctype.registered_method_parameter.registered_method_parameter import (
            RegisteredMethodParameter,
        )

        description: DF.Text | None
        execution_context: DF.Literal["Synchronous", "Background", "User Context"]
        method_path: DF.Data
        parameters: DF.Table[RegisteredMethodParameter]
        requires_auth: DF.Check
        return_type: DF.Literal[
            "String", "Integer", "Float", "Boolean", "List", "Dict", "Document", "Any"
        ]
        signature: DF.Code | None
        title: DF.Data
        version: DF.Data | None
        whitelisted: DF.Check
    # end: auto-generated types

    def before_save(self):
        self.validate_method_path()
        self.generate_signature()
        self.apply_security_rules()

    def validate_method_path(self):
        forbidden_paths = [
            "os.",
            "sys.",
            "subprocess.",
            "shutil.",
            "frappe.utils.password.",
            "frappe.client.",
        ]

        if any(fp in self.method_path for fp in forbidden_paths):
            frappe.throw(_("Invalid method path: Restricted module detected"))

        if self.method_path.count(".") < 1:
            frappe.throw(_("Method path must be in format: module.path.function_name"))

        # Verify the method exists
        try:
            self._get_method_function()
        except (ImportError, AttributeError):
            frappe.throw(f"Method not found at path: {self.method_path}")

    def _get_method_function(self):
        """Get the actual Python function"""
        module_path, function_name = self.method_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, function_name)

    def generate_signature(self):
        """Auto-generate method signature documentation"""
        params = []
        for param in self.parameters:
            param_info = {
                "name": param.parameter_name,
                "type": param.parameter_type,
                "required": bool(param.required),
                "default": param.default_value,
                "doctype": (
                    param.target_doctype if param.parameter_type == "DocType" else None
                ),
                "is_context_var": bool(param.is_context_var),
            }
            params.append(param_info)

        signature = {
            "name": self.method_name,
            "path": self.method_path,
            "description": self.description,
            "return_type": self.return_type,
            "parameters": params,
            "context_aware": any(p.is_context_var for p in self.parameters),
        }

        self.method_signature = json.dumps(signature, indent=2)

    def apply_security_rules(self):
        """Apply security defaults"""
        if self.whitelisted and not self.requires_authentication:
            self.requires_authentication = 1
            frappe.msgprint("Enabled authentication for whitelisted method")

    def execute(self, context_doc=None, params=None):
        """Execute method with security checks"""
        from uph.hub.services.method_service import MethodService

        return MethodService().execute(
            method_name=self.name, context_doc=context_doc, params=params or {}
        )
