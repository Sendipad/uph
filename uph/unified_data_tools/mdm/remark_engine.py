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
