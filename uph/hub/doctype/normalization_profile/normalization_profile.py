# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _
from frappe.model.document import Document
from uph.hub.utils.normalizer import NormalizationPipeline


class NormalizationProfile(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        parameters: DF.Code | None
        pipeline: DF.Data | None
        profile_name: DF.Data
    # end: auto-generated types

    def validate(self):
        self.validate_pipeline()
        self.validate_parameters()

    def validate_pipeline(self):
        if not self.pipeline:
            return

        methods = [m.strip() for m in self.pipeline.split(",")]
        invalid = [m for m in methods if m not in NormalizationPipeline.METHODS]
        if invalid:
            frappe.throw(
                _("Invalid normalization methods: {0}").format(", ".join(invalid))
            )
        seen = set()
        duplicates = [m for m in methods if m in seen or seen.add(m)]
        if duplicates:
            frappe.throw(
                _("Duplicate methods are not allowed in pipeline: {0}").format(
                    ", ".join(set(duplicates))
                )
            )

    def validate_parameters(self):
        if not self.parameters:
            return
        try:
            json.loads(self.parameters)
        except json.JSONDecodeError:
            frappe.throw(_("Parameters must be valid JSON."))
