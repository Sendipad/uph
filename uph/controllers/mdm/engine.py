import frappe
from frappe import _
from frappe.utils import get_link_to_form
from uph.controllers.mdm.blocking import get_blocking_filters
from uph.controllers.mdm.strategies import calculate_score

class DuplicateFinder:
    def __init__(self, doc, rule_name):
        self.doc = doc
        self.rule = frappe.get_cached_doc("Data Quality Rule", rule_name)
    
    def find_duplicates(self):
        if self.should_skip():
            return []

        candidates = self.fetch_candidates()
        return self.score_candidates(candidates)

    def should_skip(self):
        if not self.rule.enabled:
            return True
        
        if self.rule.bypass_roles:
            user_roles = frappe.get_roles(frappe.session.user)
            allowed_roles = [d.role for d in self.rule.bypass_roles]
            if any(role in allowed_roles for role in user_roles):
                return True
        
        return False

    def fetch_candidates(self):
        conditions = self.rule.conditions
        if not conditions:
            return []

        # Base filter: exclude self and cancelled docs
        filters = {
            "name": ["!=", self.doc.name],
            "docstatus": ["<", 2]
        }
        
        # Get optimized blocking filters
        or_filters = get_blocking_filters(self.doc, conditions)
        
        if not or_filters:
            return []

        # Fields to fetch
        field_list = ["name"]
        
        # Get meta to check for normalized fields
        meta = frappe.get_meta(self.doc.doctype)
        
        for c in conditions:
            # Only fetch parent fields directly. Child tables are fetched on demand or via join (complex).
            if "." not in c.field:
                if c.field not in field_list:
                    field_list.append(c.field)
                
                # Optimization: Fetch normalized field if exists
                norm_field = f"normalized_{c.field}"
                if meta.has_field(norm_field) and norm_field not in field_list:
                    field_list.append(norm_field)
        
        # Check if any condition involves child tables
        has_child_table_condition = any("." in c.field for c in conditions)
        
        candidates = frappe.get_all(
            self.doc.doctype,
            filters=filters,
            or_filters=or_filters,
            fields=field_list if not has_child_table_condition else ["name"], # If child table needed, just get name and load doc?
            limit=1000,
            order_by="modified desc"
        )
        
        # If we need child table data, we have a problem with get_all.
        # Loading 1000 docs is too slow.
        # Solution: Only load full doc if we really need to score it and it's a high potential match?
        # Or use SQL to fetch child table data for these candidates.
        # For now, to be safe and correct, if there are child table conditions, we might have to load docs.
        # But let's try to avoid it. 
        # If we return dicts, calculate_score needs to handle missing keys by returning 0?
        # Or we load the doc in the loop.
        return candidates

    def score_candidates(self, candidates):
        duplicates = []
        has_child_table_condition = any("." in c.field for c in self.rule.conditions)
        
        for candidate in candidates:
            # If we need child table data, we must load the doc
            candidate_doc = candidate
            if has_child_table_condition:
                candidate_doc = frappe.get_doc(self.doc.doctype, candidate.name)
            
            total_score = calculate_score(self.doc, candidate_doc, self.rule.conditions)

            if total_score >= self.rule.threshold_score:
                duplicates.append({
                    "docname": candidate.name,
                    "score": total_score
                })
        
        return duplicates

def validate_document_quality(doc, method):
    if frappe.flags.in_import or frappe.flags.in_patch or frappe.flags.in_install:
        return

    trigger_map = {
        "validate": "On Save",
        "on_submit": "On Submit"
    }
    trigger = trigger_map.get(method)
    if not trigger:
        return

    # Fetch active rules
    # Optimization: Cache rules per doctype?
    rules = frappe.get_all(
        "Data Quality Rule",
        filters={
            "document_type": doc.doctype,
            "trigger": trigger,
            "enabled": 1
        },
        fields=["name", "rule_name", "action", "threshold_score", "filter_condition", "bypass_roles"]
    )

    if not rules:
        return

    violations = []

    for rule_data in rules:
        # Check Bypass Roles (optimization: check before creating finder)
        if rule_data.bypass_roles:
             # We need to fetch the child table if it wasn't fetched (get_all doesn't fetch children)
             # But we can't easily check without fetching.
             # Let's rely on DuplicateFinder loading the cached doc which has children.
             pass

        # Check Filter Condition
        if rule_data.filter_condition:
            try:
                if not frappe.safe_eval(rule_data.filter_condition, None, {"doc": doc}):
                    continue
            except Exception:
                frappe.log_error(f"Error evaluating filter condition for rule {rule_data.name}")
                continue

        finder = DuplicateFinder(doc, rule_data.name)
        duplicates = finder.find_duplicates()

        if duplicates:
            priority = 1 if rule_data.action == "Block" else 2
            violations.append((rule_data, duplicates, priority))

    if violations:
        violations.sort(key=lambda x: x[2])
        rule, duplicates, _ = violations[0]
        handle_rule_action(rule, duplicates, doc)

def handle_rule_action(rule, duplicates, doc):
    msg = "<b>" + _("Data Quality Alert:</b> Potential duplicates found for rule '{0}'").format(rule.rule_name) + "<br>"
    msg += "<ul>"
    for d in duplicates:
        msg += f"<li>{get_link_to_form(doc.doctype, d['docname'])} ({_('Score')}: {d['score']:.1f})</li>"
    msg += "</ul>"

    if rule.action == "Block":
        frappe.throw(msg, title=_("Duplicate Blocked"))
    else:
        frappe.msgprint(msg, title=_("Duplicate Warning"), indicator="orange")

def find_potential_duplicates(doc, rule_name):
    finder = DuplicateFinder(doc, rule_name)
    return finder.find_duplicates()
