import frappe
from frappe.utils import getdate, date_diff
from uph.controllers.mdm.normalization import normalize_text
from uph.controllers.mdm.utils import get_field_value

from rapidfuzz import fuzz, process

class ScoringStrategy:
    def score(self, doc_val, cand_val, condition, is_normalized=False):
        raise NotImplementedError

    def score_lists(self, doc_vals, cand_vals, condition, is_normalized=False):
        """
        Compare two lists of values and return the best score.
        Default implementation: Nested loop (Cross-product).
        """
        best_score = 0.0
        for dv in doc_vals:
            for cv in cand_vals:
                if not dv or not cv:
                    continue
                s = self.score(dv, cv, condition, is_normalized=is_normalized)
                if s > best_score:
                    best_score = s
        return best_score

class ExactMatch(ScoringStrategy):
    def score(self, doc_val, cand_val, condition, is_normalized=False):
        if doc_val == cand_val:
            return condition.weight
        return 0.0

class DateRange(ScoringStrategy):
    def score(self, doc_val, cand_val, condition, is_normalized=False):
        window = condition.window_days or 0
        try:
            d1 = getdate(doc_val)
            d2 = getdate(cand_val)
            diff = abs(date_diff(d1, d2))
            if diff <= window:
                return condition.weight
        except Exception:
            pass
        return 0.0

class FuzzyMatch(ScoringStrategy):
    def score(self, doc_val, cand_val, condition, is_normalized=False):
        # Single value comparison
        if doc_val is None or cand_val is None:
            return 0.0
        return self._calculate_fuzzy(str(doc_val), str(cand_val), condition, is_normalized)

    def score_lists(self, doc_vals, cand_vals, condition, is_normalized=False):
        # Optimized list comparison using rapidfuzz.process
        # Convert all to string once, filtering out None
        query_strings = [str(v) for v in doc_vals if v is not None]
        choice_strings = [str(v) for v in cand_vals if v is not None]
        
        if not query_strings or not choice_strings:
            return 0.0

        max_similarity = 0.0
        
        # Determine processor
        # If already normalized, we don't need to normalize again.
        # rapidfuzz.utils.default_process is a good default if we don't need custom normalization.
        # Or None if we want raw string comparison.
        processor = None if is_normalized else normalize_text
        
        # For each query, find best match in choices
        for query in query_strings:
            result = process.extractOne(
                query,
                choice_strings,
                scorer=fuzz.token_set_ratio,
                processor=processor
            )
            if result:
                score = result[1]
                if score > max_similarity:
                    max_similarity = score
        
        threshold = (condition.minimum_similarity if condition.minimum_similarity is not None else 80)
        if max_similarity >= threshold:
            return condition.weight * (max_similarity / 100.0)
        return 0.0

    def _calculate_fuzzy(self, s1, s2, condition, is_normalized=False):
        if is_normalized:
            n1, n2 = s1, s2
        else:
            n1 = normalize_text(s1)
            n2 = normalize_text(s2)
            
        if not n1 or not n2:
            return 0.0
            
        similarity = fuzz.token_set_ratio(n1, n2) / 100.0
        
        threshold = (condition.minimum_similarity if condition.minimum_similarity is not None else 80) / 100.0
        if similarity >= threshold:
            return condition.weight * similarity
        return 0.0

STRATEGIES = {
    "Exact Match": ExactMatch(),
    "Date Range": DateRange(),
    "Fuzzy Match": FuzzyMatch()
}

def calculate_score(doc, candidate, conditions):
    total_score = 0.0
    
    for condition in conditions:
        strategy = STRATEGIES.get(condition.check_type)
        if not strategy:
            continue
            
        # Optimization: Check for pre-normalized field or explicit configuration
        # Convention: normalized_{field_name}
        norm_field = f"normalized_{condition.field}"
        
        # We only use pre-normalized values for Fuzzy Match
        use_normalized = False
        if condition.check_type == "Fuzzy Match":
            # Explicit configuration from rule condition
            if condition.get("is_normalized"):
                use_normalized = True
                doc_vals = get_field_value(doc, condition.field)
                cand_vals = get_field_value(candidate, condition.field)
            else:
                # Automatic detection (fallback/optimization)
                # Handle dicts (including frappe._dict) separately from Objects
                if isinstance(doc, dict):
                    doc_has_norm = norm_field in doc
                else:
                    doc_has_norm = hasattr(doc, norm_field)
                    
                if isinstance(candidate, dict):
                    cand_has_norm = norm_field in candidate
                else:
                    cand_has_norm = hasattr(candidate, norm_field)
                
                if doc_has_norm and cand_has_norm:
                    doc_vals = get_field_value(doc, norm_field)
                    cand_vals = get_field_value(candidate, norm_field)
                    use_normalized = True
                else:
                    doc_vals = get_field_value(doc, condition.field)
                    cand_vals = get_field_value(candidate, condition.field)
        else:
            doc_vals = get_field_value(doc, condition.field)
            cand_vals = get_field_value(candidate, condition.field)
        
        # Normalize to lists for uniform handling
        if not isinstance(doc_vals, list):
            doc_vals = [doc_vals]
        if not isinstance(cand_vals, list):
            cand_vals = [cand_vals]
            
        # Delegate to strategy
        score = strategy.score_lists(doc_vals, cand_vals, condition, is_normalized=use_normalized)
        total_score += score
        
    return total_score
