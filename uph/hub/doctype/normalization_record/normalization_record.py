# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from uph.hub.utils.normalizer import normalizer
from frappe import _


class NormalizationRecord(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        docname: DF.DynamicLink
        document_type: DF.Link
        field_path: DF.Data
        normalization_profile: DF.Link
        normalized_data: DF.Text | None
        original_data: DF.Text | None

    # end: auto-generated types
    def validate(self):
        if self.field_path and not frappe.get_meta(self.document_type).has_field(
            self.field_path
        ):
            frappe.throw(
                _("Field {0} is not in {1}").format(
                    self.field_path, _(self.document_type)
                )
            )
        if not self.original_data or not self.normalized_data or self.is_new():
            self.get_data_with_normalized()

    def get_data_with_normalized(self):
        self.original_data = frappe.db.get_value(
            self.document_type, self.docname, self.field_path
        )

        self.normalized_data = normalizer(
            self.original_data, profile=self.normalization_profile
        )
