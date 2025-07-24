# filepath: apps/uph/uph/hub/services/rule_engine.py
import frappe
from frappe.utils.background_jobs import enqueue
from .registry import get_service

# from .context_builder import build_context
from .condition_tree import ConditionTreeBuilder
from .cache import (
    get_cached_applicable_rules,
    set_cached_applicable_rules,
    get_cached_rule_doc,
    set_cached_rule_doc,
    get_cached_condition_tree,
    set_cached_condition_tree,
    get_rule_last_updated,
    set_rule_last_updated,
    clear_rule_caches,
)


def execute(doc, method=None, dry_run=False):
    if frappe.flags.in_import or frappe.flags.in_migrate:
        return

    doctype = doc.doctype
    event_type = method

    if not has_rules_for_doctype(doctype):
        return

    rules = get_applicable_rules(doctype, event_type, get_doc_status(doc))

    base_context = {
        "doc": doc,
        "trace": [],
        "variables": {},
        "dry_run": dry_run,
        "post_actions": [],
    }

    for rule_entry in rules:
        rule_name = rule_entry.name
        if f"skip_rule_{rule_name}" in doc.get_flags():
            continue

        try:
            rule_doc = get_cached_rule_doc_with_conditions(rule_name)
            if not rule_doc.is_active:
                continue

            service_cls = get_service(rule_doc.rule_service_type)
            if not service_cls:
                frappe.log_error(
                    f"Service not found: {rule_doc.rule_service_type}",
                    "RuleEngineError",
                )
                continue

            context = frappe._dict(base_context.copy())
            context["variables"] = {}

            if rule_doc.execution_mode == "background":
                enqueue(
                    "uph.hub.services.rule_engine.run_rule_background",
                    queue="long",
                    doc=doc.as_dict(),
                    rule_name=rule_name,
                    context=context,
                )
            else:
                run_rule(rule_doc, service_cls, context)

        except Exception as e:
            handle_rule_error(e, doc, rule_name)

    run_post_actions(doc, base_context)


def get_cached_rule_doc_with_conditions(rule_name):
    """Get rule doc with cached condition tree"""
    # First try to get from cache
    rule_doc = get_cached_rule_doc(rule_name)
    condition_tree = get_cached_condition_tree(rule_name)

    if not rule_doc or not condition_tree:
        # Cache miss - build and cache
        rule_doc = frappe.get_cached_doc("Rule", rule_name)
        condition_tree = ConditionTreeBuilder.build(rule_name)

        # Update caches
        set_cached_rule_doc(rule_name, rule_doc)
        set_cached_condition_tree(rule_name, condition_tree)

    # Attach condition tree to doc
    rule_doc.condition_tree = condition_tree
    return rule_doc


def run_rule(rule_doc, service_cls, context):
    context["trace"].append(f"Running rule: {rule_doc.name}")
    service = service_cls(rule_doc)
    service.run(context)
    context["trace"].append(f"Finished: {rule_doc.name}")


def run_post_actions(doc, context):
    for action in context.get("post_actions", []):
        try:
            action(doc, context)
        except Exception as e:
            frappe.log_error(f"Post action failed: {str(e)}", "RuleEnginePostAction")


@frappe.whitelist()
def run_rule_background(doc, rule_name, context):
    rule_doc = get_cached_rule_doc_with_conditions(rule_name)
    doc = frappe.get_doc(doc["doctype"], doc["name"])
    service_cls = get_service(rule_doc.rule_service_type)
    context["doc"] = doc
    context["trace"].append(f"[Background] Running: {rule_name}")
    service = service_cls(rule_doc)
    service.run(context)


def get_applicable_rules(doctype, event_type, docstatus=0):
    cache_key = (doctype, event_type, docstatus)
    cached_rules = get_cached_applicable_rules(doctype, event_type, docstatus)

    # Check cache validity
    if cached_rules and is_cache_valid(cache_key):
        return cached_rules

    # Cache miss or invalid - load from DB
    rules = load_applicable_rules(doctype, event_type, docstatus)
    set_cached_applicable_rules(doctype, event_type, docstatus, rules)
    return rules


def is_cache_valid(cache_key):
    """Check if cache is still valid based on last updated timestamp"""
    last_updated = get_rule_last_updated()
    if not last_updated:
        return False

    # Get max modified from database
    db_last_updated = get_db_rule_last_updated()
    return last_updated >= db_last_updated


def get_db_rule_last_updated():
    result = frappe.db.sql(
        """
        SELECT GREATEST(
            (SELECT MAX(modified) FROM `tabRule`),
            (SELECT MAX(modified) FROM `tabRule Scope`)
        )
    """
    )
    return result[0][0] if result else frappe.utils.now_datetime()


def load_applicable_rules(doctype, event_type, docstatus):
    return frappe.db.sql(
        """
        SELECT DISTINCT rule.name, rule.rule_service_type, rule.priority
        FROM `tabRule` rule
        INNER JOIN `tabRule Scope` scope ON scope.parent = rule.name
        WHERE 
            rule.is_active = 1
            AND scope.document_type = %(doctype)s
            AND scope.evaluation_event = %(event)s
            AND (scope.apply_when_docstatus_is = 'Any' OR scope.apply_when_docstatus_is = %(docstatus)s)
        ORDER BY rule.priority DESC
    """,
        {"doctype": doctype, "event": event_type, "docstatus": docstatus},
        as_dict=True,
    )


def get_doc_status(doc):
    return getattr(doc, "docstatus", 0)


def has_rules_for_doctype(doctype):
    cache_key = f"has_rules_{doctype}"
    has_rules = frappe.cache().hget("rule_engine", cache_key)
    if has_rules is None:
        has_rules = frappe.db.exists("Rule Scope", {"document_type": doctype})
        frappe.cache().hset("rule_engine", cache_key, int(bool(has_rules)))
    return bool(has_rules)


def handle_rule_error(exception, doc, rule_name):
    frappe.log_error(
        {
            "title": f"Rule {rule_name} failed",
            "message": f"Error: {str(exception)}\nDoc: {doc.as_dict()}",
            "reference_doctype": doc.doctype,
            "reference_name": doc.name,
        }
    )
    doc.set_flags(**{f"skip_rule_{rule_name}": True})


def on_rule_update(doc, method):
    """Clear all caches when rule is updated"""
    clear_rule_caches(doc.name)
    set_rule_last_updated()
