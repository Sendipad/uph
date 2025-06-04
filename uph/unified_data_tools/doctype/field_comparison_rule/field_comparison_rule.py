# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class FieldComparisonRule(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        comparison_type: DF.Literal[
            "Equals",
            "Not Equals",
            "Greeter Than",
            "Less Than",
            "Both Empty",
            "Only One Set",
            "Both Set",
            "Custom Expression",
            "Link",
        ]
        document_type: DF.Link
        enabled: DF.Check
        field_allowed_values: DF.SmallText | None
        fieldname: DF.Autocomplete | None
        fieldname_type: DF.Data | None
        priority: DF.Literal["High", "Medium", "Low"]
        skip_if_outside_scope: DF.Check
        title: DF.Data | None
        type: DF.Literal[
            "In-Doc Comparison", "Cross-Doc Comparison", "Cross-DocType Comparison"
        ]
        with_doctype: DF.Link | None
        with_field: DF.Autocomplete | None
        with_field_allowed_values: DF.SmallText | None
        with_field_type: DF.Data | None
    # end: auto-generated types

    def before_insert(self):
        from uph.unified_data_tools.utils.field import get_field_options

        fields_a = get_field_options(self.document_type)
        fields_b = get_field_options(
            self.with_doctype
            if self.type == "Cross-DocType Comparison"
            else self.document_type
        )

        field_a = field_b = _("(Unknown)")

        for field in fields_a:
            if field["value"] == self.fieldname:
                field_a = _(field["label"])

        for field in fields_b:
            if field["value"] == self.with_field:
                field_b = _(field["label"])

        if not self.title:
            self.title = _("{0} {1} {2} in {3}").format(
                field_a,
                _(self.comparison_type or "Compared"),
                field_b,
                self.document_type,
            )

    def validate(self):
        if not self.document_type or not self.fieldname or not self.with_field:
            frappe.throw(_("Document Type, Field A, and Field B are required."))

        meta_a = frappe.get_meta(self.document_type)
        meta_b = (
            frappe.get_meta(self.with_doctype)
            if self.type == "Cross-DocType Comparison"
            else meta_a
        )

        self.validate_field_exists(meta_a, self.fieldname, _("Field A"))
        self.validate_field_exists(meta_b, self.with_field, _("Field B"))

        if self.field_allowed_values:
            self.validate_field_type_allows_values(meta_a, self.fieldname, _("Field A"))

        if self.with_field_allowed_values:
            self.validate_field_type_allows_values(
                meta_b, self.with_field, _("Field B")
            )

    def validate_field_exists(self, meta, path, field_label):
        if "." in path:
            parent_field, child_field = path.split(".")
            parent_df = meta.get_field(parent_field)
            if not parent_df or parent_df.fieldtype != "Table":
                frappe.throw(
                    _("{0} parent field '{1}' is not a valid child table.").format(
                        field_label, parent_field
                    )
                )
            child_meta = frappe.get_meta(parent_df.options)
            if not child_meta.has_field(child_field):
                frappe.throw(
                    _(
                        "{0} child field '{1}' does not exist in child doctype {2}."
                    ).format(field_label, child_field, parent_df.options)
                )
        else:
            if not meta.has_field(path):
                frappe.throw(
                    _("{0} '{1}' does not exist in {2}.").format(
                        field_label, path, meta.name
                    )
                )

    def validate_field_type_allows_values(self, meta, path, field_label):
        if "." in path:
            parent_field, child_field = path.split(".")
            parent_df = meta.get_field(parent_field)
            child_meta = frappe.get_meta(parent_df.options)
            df = child_meta.get_field(child_field)
        else:
            df = meta.get_field(path)

        valid_types = ["Select", "Link", "Data", "Read Only"]
        if df.fieldtype not in valid_types:
            frappe.throw(
                _(
                    "{0} '{1}' is of type '{2}', which does not support allowed values."
                ).format(field_label, df.fieldname, df.fieldtype)
            )
