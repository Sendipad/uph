import frappe
from jinja2 import exceptions, Template
from frappe.model.document import Document
from uph.unified_data_tools.utils.field import get_field_options
from frappe import _
from uph.unified_data_tools.mdm.auto_text_generator_engine import (
    get_document_type_run_validate_events,
    delete_set_document_types_cache,
)


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
        remove_markers_on_submit: DF.Check
        target_field: DF.Autocomplete
        template: DF.HTMLEditor | None
        text_merge_mode: DF.Literal["Overwrite", "Append", "Prepend"]
        title: DF.Data | None
        validate_on_event: DF.Literal["", "Before Insert", "Before Save", "On Submit"]
    # end: auto-generated types

    def clear_cache(self):
        get_document_type_run_validate_events.clear_cache()  # Clear cache for event rules
        return super().clear_cache()

    def validate(self):
        try:
            # KEY CHANGE: Use frappe.get_jenv() to parse for validation
            frappe.get_jenv().parse(self.template or "")
        except exceptions.TemplateSyntaxError as e:
            frappe.throw(f"Template syntax error at line {e.lineno}: {e.message}")

    def delete_cached_list_document_types(self):
        if self.is_new():
            if self.enabled:
                delete_set_document_types_cache()
        else:
            if self.has_value_changed("enabled"):
                delete_set_document_types_cache()

    def before_save(self):
        self.delete_cached_list_document_types()

        # Clear cache only if the template itself has changed
        # or if the rule is new (since the template might have been set)
        if self.is_new() or self.has_value_changed("template"):
            self.clear_compiled_template_cache()

        if not self.title:
            if self.target_field:
                fields = get_field_options(self.document_type)
                fields = [
                    f.get("label")
                    for f in fields
                    if f.get("value") == self.target_field
                ]
                if fields:
                    self.title = _("{0} : {1}").format(
                        _(self.document_type), _(fields[0])
                    )
                else:
                    self.title = _("{0} : {1}").format(
                        _(self.document_type), self.target_field
                    )

    def _get_compiled_template(self) -> Template | None:
        """
        Compiles the Jinja2 template and caches it.
        Returns the compiled Jinja2 Template object.
        """
        if cached := frappe.cache.get_value(
            f"AutoTextGeneratorRule._get_compiled_template-{self.name}"
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
                "AutoTextGeneratorRule Template Compilation",
            )
            return None

    def clear_compiled_template_cache(self):
        """Clears the cached compiled template for this rule."""
        frappe.cache.delete_key(
            f"AutoTextGeneratorRule._get_compiled_template-{self.name}"
        )
