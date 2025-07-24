# apps/uph/uph/hub/mdm/deduplication_service.py

import frappe
from frappe import _

from rapidfuzz import fuzz, process
from uph.hub.services.base import BaseRuleService
from uph.hub.services.registry import core_register
from uph.hub.services.condition_tree import ConditionNode, ConditionTreeBuilder
from uph.hub.services.context_builder import resolve_field_value
from uph.hub.services.action_executor import ActionExecutor


@core_register
class DeduplicationService(BaseRuleService):
    service_type = "Deduplication"
    execution_mode = "event"
    label = _("Duplication Detection Service")

    SCORERS = {
        "Levenshtein Distance": fuzz.ratio,
        "Partial Ratio": fuzz.partial_ratio,
        "Token Set Ratio": fuzz.token_set_ratio,
        "Token Sort Ratio": fuzz.token_sort_ratio,
        "Jaro-Winkler": fuzz.WRatio,
        "Exact Match": lambda s1, s2: 100 if s1 == s2 else 0,
        "Cosine Similarity": lambda s1, s2: NotImplemented,
        "Jaccard Index": lambda s1, s2: NotImplemented,
        "Soundex": lambda s1, s2: NotImplemented,
        "Metaphone": lambda s1, s2: NotImplemented,
        "Double Metaphone": lambda s1, s2: NotImplemented,
    }

    def evaluate_event(self, context):
        doc = context["doc"]
        rule = self.rule

        if not any(
            self.passes_scope_filter(doc, scope)
            for scope in rule.get("apply_scopes", [])
        ):
            return

        candidates = self.get_candidate_documents(doc.doctype)
        duplicates = self.find_duplicates_with_process(doc, candidates)

        if duplicates:
            context["duplicates"] = duplicates
            self.execute_actions(context)

    def passes_scope_filter(self, doc, scope) -> bool:
        filter_str = getattr(scope, "apply_filter_json", None)
        if not filter_str:
            return True
        try:
            filters = frappe.parse_json(filter_str)
            return all(doc.get(k) == v for k, v in filters.items())
        except Exception as e:
            frappe.log_error(
                f"Invalid apply_filter_json in RuleScope\n{e}", "DeduplicationService"
            )
            return False

    def get_candidate_documents(self, doctype):
        return frappe.get_all(
            doctype, fields=["*"], limit_page_length=500, ignore_ifnull=True
        )

    def find_duplicates_with_process(self, doc, candidates):
        """Optimized dedup using rapidfuzz.process for fuzzy fields"""
        duplicates = []
        doc_name = doc.name

        for node in self.get_weighted_conditions():
            left_val = self.get_normalized_value(doc, node.final_left_field_path, node)
            if left_val is None:
                continue

            # Prepare candidate values
            candidate_values = {}
            for cand in candidates:
                if cand.name == doc_name:
                    continue
                val = self.get_normalized_value(cand, node.final_right_field_path, node)
                if val:
                    candidate_values[cand.name] = val

            if not candidate_values:
                continue

            # Use process.extract to rank top candidates
            scorer = self.SCORERS.get(node.scorer or "Levenshtein Distance", fuzz.ratio)
            matches = process.extract(
                query=left_val,
                choices=candidate_values.items(),
                scorer=scorer,
                limit=10,
                score_cutoff=(node.fuzzy_threshold or 80),
            )

            for name, score in matches:
                duplicates.append(
                    {
                        "document": name,
                        "score": round(score / 100.0, 2),
                        "doctype": doc.doctype,
                    }
                )

        # Deduplicate result list by doc name, keeping highest score
        final = {}
        for dup in duplicates:
            key = dup["document"]
            if key not in final or dup["score"] > final[key]["score"]:
                final[key] = dup
        return list(final.values())

    def get_weighted_conditions(self):
        weighted = []

        def visit(node):
            if isinstance(node, ConditionNode) and node.operator == "fuzzy_match":
                weighted.append(node)
            elif hasattr(node, "children"):
                for child in node.children:
                    visit(child)

        tree = ConditionTreeBuilder.build(self.rule.name)
        visit(tree)
        return weighted

    def get_normalized_value(self, doc, field_path, node):
        try:
            if node.normalized_record:
                return frappe.db.get_value(
                    "Normalization Record",
                    {
                        "docname": doc.name,
                        "document_type": doc.doctype,
                        "field_path": field_path,
                    },
                    "normalized_data",
                )

            return resolve_field_value(doc, field_path)
        except Exception as e:
            frappe.log_error(f"Normalization fallback failed: {e}")
            return None

    def execute_actions(self, context):
        if not self.rule.actions:
            msg = _("Possible duplicates found: {0}").format(
                ", ".join([d["document"] for d in context["duplicates"]])
            )
            frappe.msgprint(msg, alert=True)
        else:
            executor = ActionExecutor()
            executor.execute(self.rule.actions, context)
