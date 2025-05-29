# -----------------------------------------------------------------------------
# Project Name: UPH - Unified Party Hub
# File: remark_engine.py
# Description: Provides the RemarkEngine class for generating custom remarks based on rules and templates for documents in the UPH system.
#
# Author: Abdo Ruzaqi(Sendipad)
# Created: 2025-04-10
# License: GNU General Public License v3.0 (GPL-3.0)
# Repository: https://github.com/Sendipad/uph
#
# Copyright (c) 2025 Abdo  Ruzaqi(Sendipad)
# This file is part of the UPH project and is released under the GPL-3.0 license.
# See LICENSE file or https://www.gnu.org/licenses/gpl-3.0.en.html for full terms.
# -----------------------------------------------------------------------------
import frappe


class RemarkEngine:
    def __init__(self, doc):
        self.doc = doc
        self.context = {"doc": self.doc.as_dict()}

    def generate(self):
        rulesets = frappe.get_all(
            "Custom Remark Rule",
            filters={
                "document_type": self.doc.doctype,
                "enabled": 1,
            },
            order_by="priority desc",
            fields=["name"],
        )

        for ruleset in rulesets:
            rule_doc = frappe.get_doc("Custom Remark Rule", ruleset.name)

            # Skip rules with no template
            if not rule_doc.template or not rule_doc.template.strip():
                continue

            if self.evaluate_filters(rule_doc.conditions):
                try:
                    remark = frappe.render_template(
                        rule_doc.template, self.context
                    ).strip()
                    if remark:  # only accept if rendering produces something
                        return remark
                except Exception as e:
                    frappe.log_error(f"Error rendering template: {e}", "Remark Engine")
                    continue  # continue to next rule if render failed

        return ""
