"""
Optimized Execution Engines for Data Quality Policies

This module contains two execution engines:
1. QualityCheckEngine - For single-doc validation (on save/submit)
2. BulkDuplicateScanner - For bulk scanning (background jobs)

Both use blocking strategy with QueryBuilder for performance.
"""

import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Left
import time
from functools import reduce
import operator


class QualityCheckEngine:
    """
    Engine for single-doc validation (on save/submit hooks).
    
    Performance optimized for low-latency (<100ms).
    Uses blocking strategy to reduce candidate set by 90%+.
    """
    
    def __init__(self, doc, policy, rule):
        self.doc = doc
        self.policy = policy
        self.rule = rule
        self.meta = frappe.get_meta(doc.doctype)
    
    def find_matches(self):
        """
        Main entry point - finds duplicates for single document.
        
        Returns dict with:
        - matches: List of {docname, score}
        - stats: Performance metrics
        """
        start_time = time.perf_counter()
        
        # Phase 1: Fetch candidates using blocking
        candidates = self._fetch_candidates_optimized()
        query_time = (time.perf_counter() - start_time) * 1000
        
        if not candidates:
            return {
                "matches": [],
                "stats": {
                    "candidates": 0,
                    "query_time_ms": round(query_time, 2),
                    "scoring_time_ms": 0
                }
            }
        
        # Phase 2: Score candidates
        scoring_start = time.perf_counter()
        matches = self._score_candidates(candidates)
        scoring_time = (time.perf_counter() - scoring_start) * 1000
        
        return {
            "matches": matches,
            "stats": {
                "candidates": len(candidates),
                "matches": len(matches),
                "query_time_ms": round(query_time, 2),
                "scoring_time_ms": round(scoring_time, 2),
                "total_time_ms": round(query_time + scoring_time, 2)
            }
        }
    
    def _fetch_candidates_optimized(self):
        """
        Fetch candidates using Frappe QueryBuilder with blocking strategy.
        
        Reduces search space from 100K+ to ~1K records.
        """
        DocTypeTable = DocType(self.doc.doctype)
        
        # Base conditions (always applied)
        base_conditions = (
            (DocTypeTable.name != self.doc.name) &
            (DocTypeTable.docstatus < 2)
        )
        
        # Build blocking conditions
        blocking_filters = []
        
        for condition in self.rule.conditions:
            # Skip child table fields for blocking
            if "." in condition.field:
                continue
            
            # Only use high-weight conditions for blocking
            if condition.weight < 30:
                continue
            
            doc_value = self.doc.get(condition.field)
            if not doc_value:
                continue
            
            # Exact Match blocking
            if condition.check_type == "Exact Match":
                blocking_filters.append(
                    getattr(DocTypeTable, condition.field) == doc_value
                )
            
            # Fuzzy Match blocking (use normalized prefix)
            elif condition.check_type == "Fuzzy Match":
                norm_field = f"normalized_{condition.field}"
                if self.meta.has_field(norm_field):
                    if condition.is_normalized:
                        norm_value = self.doc.get(norm_field)
                    else:
                        from uph.controllers.mdm.normalization import normalize_text
                        norm_value = normalize_text(str(doc_value))
                    
                    if norm_value and len(norm_value) >= 3:
                        # Prefix match uses index
                        blocking_filters.append(
                            Left(getattr(DocTypeTable, norm_field), 3) == norm_value[:3]
                        )
            
            # Date Range blocking
            elif condition.check_type == "Date Range":
                window = condition.window_days or 0
                try:
                    from frappe.utils import add_days, getdate
                    doc_date = getdate(doc_value)
                    date_from = add_days(doc_date, -window)
                    date_to = add_days(doc_date, window)
                    
                    blocking_filters.append(
                        getattr(DocTypeTable, condition.field).between(date_from, date_to)
                    )
                except:
                    pass
        
        # Combine conditions
        if blocking_filters:
            # OR logic for blocking (at least one must match)
            blocking_condition = reduce(operator.or_, blocking_filters)
            query_condition = base_conditions & blocking_condition
        else:
            query_condition = base_conditions
        
        # Build select fields
        select_fields = [DocTypeTable.name]
        for condition in self.rule.conditions:
            if "." not in condition.field:
                select_fields.append(getattr(DocTypeTable, condition.field))
                if condition.is_normalized and condition.check_type == "Fuzzy Match":
                    norm_field = f"normalized_{condition.field}"
                    if self.meta.has_field(norm_field):
                        select_fields.append(getattr(DocTypeTable, norm_field))
        
        # Build and execute query
        query = (
            frappe.qb.from_(DocTypeTable)
            .select(*select_fields)
            .where(query_condition)
            .limit(self.policy.max_candidates or 1000)
            .orderby(DocTypeTable.modified, order=frappe.qb.desc)
        )
        
        return query.run(as_dict=True)
    
    def _score_candidates(self, candidates):
        """Score each candidate using fuzzy logic."""
        matches = []
        
        for candidate in candidates:
            score = self.rule.evaluate(self.doc, candidate)
            
            if score >= self.policy.threshold_score:
                matches.append({
                    "docname": candidate.name,
                    "score": round(score, 2)
                })
        
        # Sort by score descending
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches
