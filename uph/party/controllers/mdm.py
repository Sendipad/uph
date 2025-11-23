# Copyright (c) 2024, Abdo Ruzaqi and contributors
# For license information, please see license.txt
"""
A module that controls Data Quality and deduplication. It holds many useful utility functions.
"""

import frappe
import re
import unicodedata
from functools import lru_cache
from frappe import _

try:
    from rapidfuzz import fuzz
except ImportError:
    from difflib import SequenceMatcher
    fuzz = None

# Translation table for Arabic, Persian, and Latin accented characters
TRANSLATION_TABLE = str.maketrans({
    # Arabic normalization
    "أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي", "ـ": "",
    # Persian character mapping
    "ك": "ک", "ي": "ی",
    # Digits from Indian to Arabic
    "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4", 
    "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9",
    # Latin accents (lowercase)
    "é": "e", "è": "e", "ê": "e", "ë": "e",
    "á": "a", "à": "a", "â": "a", "ä": "a",
    "í": "i", "ì": "i", "î": "i", "ï": "i",
    "ó": "o", "ò": "o", "ô": "o", "ö": "o",
    "ú": "u", "ù": "u", "û": "u", "ü": "u",
    "ç": "c", "ñ": "n",
    # Latin accents (uppercase)
    "É": "E", "È": "E", "Ê": "E", "Ë": "E",
    "Á": "A", "À": "A", "Â": "A", "Ä": "A",
    "Í": "I", "Ì": "I", "Î": "I", "Ï": "I",
    "Ó": "O", "Ò": "O", "Ô": "O", "Ö": "O",
    "Ú": "U", "Ù": "U", "Û": "U", "Ü": "U",
    "Ç": "C", "Ñ": "N",
})

# Arabic diacritic removal regex
DIACRITIC_REGEX = re.compile(r"[\u064B-\u065F]")


@frappe.whitelist()
@lru_cache(maxsize=1024)
def normalize_text(text: str) -> str:
    """Normalize text for fuzzy matching (removes diacritics, normalizes characters)."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = DIACRITIC_REGEX.sub("", text)
    text = text.translate(TRANSLATION_TABLE)
    return text.strip()


def validate_document_quality(doc, method):
    """
    Validate document against Data Quality Rules with optimized performance.
    Groups rules by condition fingerprint to avoid redundant candidate fetching.
    """
    if frappe.flags.in_import or frappe.flags.in_patch or frappe.flags.in_install:
        return

    trigger_map = {
        "validate": "On Save",
        "on_submit": "On Submit"
    }
    trigger = trigger_map.get(method)
    if not trigger:
        return

    # Fetch active rules for this DocType and Trigger
    rules = frappe.get_all(
        "Data Quality Rule",
        filters={
            "document_type": doc.doctype,
            "trigger": trigger,
            "enabled": 1
        },
        fields=["name", "rule_name", "action", "threshold_score", "filter_condition"]
    )

    if not rules:
        return

    # Process rules with optimization
    violations = []  # List of (rule, duplicates, priority)
    candidate_cache = {}  # Cache candidates by condition fingerprint
    
    for rule_data in rules:
        rule = frappe.get_doc("Data Quality Rule", rule_data.name)

        # Check Bypass Roles
        if has_bypass_role(rule.bypass_roles):
            continue

        # Check Filter Condition
        if rule.filter_condition:
            try:
                if not frappe.safe_eval(rule.filter_condition, None, {"doc": doc}):
                    continue
            except Exception:
                frappe.log_error(f"Error evaluating filter condition for rule {rule.name}")
                continue

        # Generate cache key based on fields being checked
        cache_key = _get_rule_cache_key(rule)
        
        # Use cached candidates if available
        if cache_key in candidate_cache:
            candidates = candidate_cache[cache_key]
        else:
            candidates = _fetch_candidates(doc, rule)
            candidate_cache[cache_key] = candidates
        
        # Score candidates against this rule
        duplicates = _score_candidates(doc, rule, candidates)

        if duplicates:
            priority = 1 if rule.action == "Block" else 2  # Block has higher priority
            violations.append((rule, duplicates, priority))
    
    # Handle violations (Block takes precedence over Warn)
    if violations:
        violations.sort(key=lambda x: x[2])  # Sort by priority
        rule, duplicates, _ = violations[0]
        handle_rule_action(rule, duplicates, doc)


def has_bypass_role(bypass_roles):
    """Check if current user has any of the bypass roles."""
    if not bypass_roles:
        return False
    user_roles = frappe.get_roles(frappe.session.user)
    allowed_roles = [d.role for d in bypass_roles]
    return any(role in allowed_roles for role in user_roles)


def _get_rule_cache_key(rule):
    """Generate a cache key based on rule conditions to enable candidate caching."""
    if not rule.conditions:
        return None
    
    # Sort fields to ensure consistent cache key for same fields
    fields = sorted([c.field for c in rule.conditions])
    return f"{rule.document_type}:{':'.join(fields)}"


def _fetch_candidates(doc, rule):
    """
    Fetch candidate documents that might be duplicates.
    Separated from scoring to enable caching.
    """
    conditions = rule.conditions
    if not conditions:
        return []

    # Build query filters
    filters = {"name": ["!=", doc.name]}
    or_filters = []
    field_list = ["name"] + [c.field for c in conditions]
    
    for condition in conditions:
        field_value = doc.get(condition.field)
        if not field_value:
            continue

        if condition.check_type == "Exact Match":
            or_filters.append([condition.field, "=", field_value])
        
        elif condition.check_type == "Date Range":
            window = condition.window_days or 0
            date_val = frappe.utils.getdate(field_value)
            start_date = frappe.utils.add_days(date_val, -window)
            end_date = frappe.utils.add_days(date_val, window)
            or_filters.append([condition.field, "between", [start_date, end_date]])

    # Fetch candidates
    if or_filters:
        return frappe.get_all(
            doc.doctype, 
            filters=filters, 
            or_filters=or_filters, 
            fields=field_list
        )
    else:
        # Fallback for pure fuzzy match: Limit to 1000 recent
        return frappe.get_all(
            doc.doctype, 
            filters=filters, 
            fields=field_list, 
            limit=1000, 
            order_by="modified desc"
        )


def _score_candidates(doc, rule, candidates):
    """
    Score candidate documents against rule conditions.
    Returns list of duplicates that exceed threshold.
    """
    if not candidates or not rule.conditions:
        return []
    
    duplicates = []
    
    for candidate in candidates:
        total_score = 0.0
        
        for condition in rule.conditions:
            doc_val = doc.get(condition.field)
            cand_val = candidate.get(condition.field)
            
            if not doc_val or not cand_val:
                continue

            score = 0.0
            
            if condition.check_type == "Exact Match":
                if doc_val == cand_val:
                    score = condition.weight
            
            elif condition.check_type == "Date Range":
                window = condition.window_days or 0
                doc_date = frappe.utils.getdate(doc_val)
                cand_date = frappe.utils.getdate(cand_val)
                diff = abs(frappe.utils.date_diff(doc_date, cand_date))
                if diff <= window:
                    score = condition.weight
            
            elif condition.check_type == "Fuzzy Match":
                val1 = normalize_text(str(doc_val))
                val2 = normalize_text(str(cand_val))
                
                if fuzz:
                    similarity = fuzz.ratio(val1, val2) / 100.0
                else:
                    similarity = SequenceMatcher(None, val1, val2).ratio()
                
                # Use configured threshold or default to 80%
                threshold = (condition.minimum_similarity or 80) / 100.0
                
                if similarity > threshold:
                    score = condition.weight * similarity

            total_score += score

        if total_score >= rule.threshold_score:
            duplicates.append({
                "docname": candidate.name,
                "score": total_score
            })

    return duplicates


def find_potential_duplicates(doc, rule):
    """
    Find duplicates based on rule conditions.
    Returns a list of dicts: {'docname': name, 'score': score}
    (Maintained for backward compatibility)
    """
    candidates = _fetch_candidates(doc, rule)
    return _score_candidates(doc, rule, candidates)


def handle_rule_action(rule, duplicates, doc):
    """Display warning or throw error based on rule action."""
    msg = _("<b>Data Quality Alert:</b> Potential duplicates found for rule '{0}'").format(rule.rule_name) + "<br>"
    msg += "<ul>"
    for d in duplicates:
        msg += f"<li>{frappe.utils.get_link_to_form(doc.doctype, d['docname'])} ({_('Score')}: {d['score']:.1f})</li>"
    msg += "</ul>"

    if rule.action == "Block":
        frappe.throw(msg, title=_("Duplicate Blocked"))
    else:
        frappe.msgprint(msg, title=_("Duplicate Warning"), indicator="orange")