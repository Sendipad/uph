import frappe
import unittest
from frappe.utils import add_days, nowdate
from uph.controllers.mdm.normalization import normalize_for_blocking, normalize_text
from uph.controllers.mdm.strategies import STRATEGIES
from uph.controllers.mdm.blocking import get_blocking_filters
from uph.controllers.mdm.utils import get_field_value

class TestMDMEngine(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(normalize_text("  Hello   World  "), "hello world")
        self.assertEqual(normalize_for_blocking("Hello World!"), "helloworld")
        self.assertEqual(normalize_text("Café"), "cafe")

    def test_strategies(self):
        # Exact Match
        exact = STRATEGIES["Exact Match"]
        condition = frappe._dict(weight=10)
        self.assertEqual(exact.score("A", "A", condition), 10)
        self.assertEqual(exact.score("A", "B", condition), 0)

        # Date Range
        date_strat = STRATEGIES["Date Range"]
        today = nowdate()
        tomorrow = add_days(today, 1)
        condition = frappe._dict(weight=10, window_days=1)
        self.assertEqual(date_strat.score(today, tomorrow, condition), 10)
        self.assertEqual(date_strat.score(today, add_days(today, 2), condition), 0)

        # Fuzzy Match
        fuzzy = STRATEGIES["Fuzzy Match"]
        condition = frappe._dict(weight=10, minimum_similarity=80)
        self.assertGreater(fuzzy.score("Apple", "Apple", condition), 0)
        self.assertGreater(fuzzy.score("Apple", "Appel", condition), 0)
        self.assertEqual(fuzzy.score("Apple", "Banana", condition), 0)

    def test_blocking(self):
        doc = {"name": "test", "field1": "Value", "field2": "2024-01-01"}
        conditions = [
            frappe._dict(field="field1", check_type="Exact Match"),
            frappe._dict(field="field2", check_type="Date Range", window_days=1),
            frappe._dict(field="field1", check_type="Fuzzy Match")
        ]
        
        filters = get_blocking_filters(doc, conditions)
        # Expecting 3 filters
        self.assertEqual(len(filters), 3)
        self.assertIn(["field1", "=", "Value"], filters)
        self.assertIn(["field1", "like", "Val%"], filters)
        # Date range filter is complex to assert exactly due to date calculation, but we can check structure
        date_filter = next((f for f in filters if f[0] == "field2"), None)
        self.assertIsNotNone(date_filter)
        self.assertEqual(date_filter[1], "between")

    def test_utils_dotted_path(self):
        doc = {
            "parent_field": "parent",
            "child_table": [
                {"child_field": "child1"},
                {"child_field": "child2"}
            ]
        }
        self.assertEqual(get_field_value(doc, "parent_field"), "parent")
        self.assertEqual(get_field_value(doc, "child_table.child_field"), ["child1", "child2"])

    def test_docstatus_filtering(self):
        from uph.controllers.mdm.engine import DuplicateFinder
        
        # Create a dummy rule
        rule = frappe.get_doc({
            "doctype": "Data Quality Rule",
            "rule_name": "Test Docstatus",
            "document_type": "Company",
            "trigger": "On Save",
            "action": "Warn",
            "threshold_score": 50,
            "conditions": [{
                "field": "company_name",
                "check_type": "Exact Match",
                "weight": 100
            }]
        }).insert(ignore_permissions=True)

        # Create a cancelled company
        cancelled = frappe.get_doc({
            "doctype": "Company",
            "company_name": "_Cancelled Company",
            "abbr": "_CC",
            "default_currency": "USD",
            "country": "United States",
            "docstatus": 0
        }).insert(ignore_permissions=True)
        cancelled.submit()
        cancelled.cancel()
        
        # Create a new doc to check against
        doc = frappe.get_doc({
            "doctype": "Company",
            "company_name": "_Cancelled Company",
            "abbr": "_CC2",
            "default_currency": "USD",
            "country": "United States"
        })
        
        finder = DuplicateFinder(doc, rule.name)
        candidates = finder.fetch_candidates()
        
        # Should not find the cancelled company
        self.assertFalse(any(c.name == cancelled.name for c in candidates))
        
        # Cleanup
        rule.delete()
        cancelled.delete()

    def test_normalized_field_optimization(self):
        from uph.controllers.mdm.strategies import calculate_score
        
        # Mock objects with normalized fields
        doc = frappe._dict({
            "party_name": "Café",
            "normalized_party_name": "cafe" # Pre-normalized
        })
        candidate = frappe._dict({
            "party_name": "Cafe",
            "normalized_party_name": "cafe" # Pre-normalized
        })
        
        condition = frappe._dict({
            "field": "party_name",
            "check_type": "Fuzzy Match",
            "weight": 100,
            "minimum_similarity": 80
        })
        
        # This should use the normalized fields and return 100% match
        score = calculate_score(doc, candidate, [condition])
        self.assertEqual(score, 100.0)
        
        # Test with mismatch
        candidate_mismatch = frappe._dict({
            "party_name": "Other",
            "normalized_party_name": "other"
        })
        score = calculate_score(doc, candidate_mismatch, [condition])
        self.assertLess(score, 50.0)

    def test_explicit_normalization_config(self):
        from uph.controllers.mdm.strategies import calculate_score
        
        # Mock objects with already normalized values in the main field
        # e.g. user points to "normalized_party_name" field directly
        doc = frappe._dict({
            "normalized_party_name": "cafe"
        })
        candidate = frappe._dict({
            "normalized_party_name": "cafe"
        })
        
        condition = frappe._dict({
            "field": "normalized_party_name",
            "check_type": "Fuzzy Match",
            "weight": 100,
            "minimum_similarity": 80,
            "is_normalized": 1 # Explicitly set
        })
        
        # This should use the values directly without normalization
        score = calculate_score(doc, candidate, [condition])
        self.assertEqual(score, 100.0)
        
        # Test with un-normalized values but flag set (should fail or be low score if case differs)
        doc_raw = frappe._dict({
            "normalized_party_name": "Cafe" # Capitalized
        })
        candidate_raw = frappe._dict({
            "normalized_party_name": "cafe"
        })
        
        # Since we skip normalization, "Cafe" != "cafe" in exact match, 
        # but fuzzy match might still be high depending on scorer.
        # token_set_ratio is case insensitive? No, rapidfuzz/fuzzywuzzy is usually case sensitive unless processed.
        # Let's check. token_set_ratio usually normalizes.
        # But we pass processor=None.
        # So it should be case sensitive.
        
        score = calculate_score(doc_raw, candidate_raw, [condition])
        # "Cafe" vs "cafe" -> token_set_ratio might be 100 if it lowercases internally?
        # RapidFuzz token_set_ratio DOES NOT lowercase by default if processor is None.
        # Wait, actually fuzz.token_set_ratio in rapidfuzz might.
        # Let's assume it might not match perfectly if we skip normalization.
        # Actually, let's use a better example: "Café" vs "Cafe"
        
        doc_dia = frappe._dict({ "normalized_party_name": "Café" })
        cand_dia = frappe._dict({ "normalized_party_name": "Cafe" })
        
        # If we normalize, this is 100.
        # If we skip normalization, this should be less than 100.
        
        score = calculate_score(doc_dia, cand_dia, [condition])
        self.assertLess(score, 100.0)

    def test_none_handling_and_zero_threshold(self):
        from uph.controllers.mdm.strategies import calculate_score
        
        # Test None handling
        doc = frappe._dict({ "party_name": None })
        candidate = frappe._dict({ "party_name": None })
        
        condition = frappe._dict({
            "field": "party_name",
            "check_type": "Fuzzy Match",
            "weight": 100,
            "minimum_similarity": 80
        })
        
        # None vs None should be 0, not 100 (str(None) == str(None))
        score = calculate_score(doc, candidate, [condition])
        self.assertEqual(score, 0.0)
        
        # Test 0% threshold
        doc_diff = frappe._dict({ "party_name": "Apple" })
        cand_diff = frappe._dict({ "party_name": "App" })
        
        condition_zero = frappe._dict({
            "field": "party_name",
            "check_type": "Fuzzy Match",
            "weight": 100,
            "minimum_similarity": 0 # Should match everything
        })
        
        score = calculate_score(doc_diff, cand_diff, [condition_zero])
        # Even with 0 threshold, it returns weight * similarity.
        # Similarity between Apple and App is > 0 (approx 75% with difflib).
        self.assertGreater(score, 0.0)
        
        # Ensure it doesn't default to 80%
        # If it defaulted to 80, score would be 0 because similarity is < 80.
        # Apple vs App is ~75%, so it should pass with 0 threshold but fail with 80 default.
        self.assertGreater(score, 0.0)


