# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt
from frappe import _
import frappe
from frappe.model.document import Document
from jinja2 import exceptions, Template


class DynamicRecordTemplate(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        document_type: DF.Link | None
        is_global: DF.Check
        output_format: DF.Literal["Plain Text", "HTML", "JSON", "XML", "Markdown"]
        template_content: DF.TextEditor
        title: DF.Data | None
    # end: auto-generated types

    def validate(self):
        self.validate_applicability()
        self.validate_template_syntax()

    def validate_applicability(self):
        if self.is_global and self.applicable_doctypes:
            frappe.throw(_("Cannot specify applicable doctypes for global templates"))

    def validate_template_syntax(self):
        # Test rendering with dummy data
        try:
            frappe.get_jenv().parse(self.template or "")

            self.render_template({"doc": {"name": "TEST"}})
        except exceptions.TemplateSyntaxError as e:
            frappe.throw(f"Template syntax error at line {e.lineno}: {e.message}")

    def before_save(self):
        if self.is_new() or not self.has_value_changed("template_content"):
            return
        self.clear_compiled_template_cache()

    def render_template(self, context):
        return frappe.render_template(self.template_content, context)

    def get_applicable_doctypes(self):
        if self.is_global:
            self.document_type = ""
        if not self.is_global and not self.document_type:
            frappe.throw(_("You must Set at least one document Type"))

    def _get_compiled_template(self) -> Template | None:
        """
        Compiles the Jinja2 template and caches it.
        Returns the compiled Jinja2 Template object.
        """
        if cached := frappe.cache.get_value(
            f"DynamicRecordTemplate._get_compiled_template-{self.name}"
        ):
            return cached
        if not self.template or not self.template.strip():
            return None
        try:
            # KEY CHANGE: Use frappe.get_jenv() to get Frappe's default Jinja2 environment
            # This environment already has 'frappe', '_', etc., in its globals.
            compiled_template = frappe.get_jenv().from_string(self.template)
            return compiled_template
        except Exception as e:
            frappe.log_error(
                f"Error compiling template for rule {self.name}: {e}",
                "DynamicRecordTemplate Template Compilation",
            )
            return None

    def clear_compiled_template_cache(self):
        """Clears the cached compiled template for this rule."""
        frappe.cache.delete_key(
            f"DynamicRecordTemplate._get_compiled_template-{self.name}"
        )
