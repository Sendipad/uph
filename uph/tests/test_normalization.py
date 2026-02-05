# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

"""
Tests for NormalizationUtils class.
Covers text normalization for fuzzy matching and duplicate detection.
"""

from frappe.tests.utils import FrappeTestCase
from uph.party.controllers.normalization import NormalizationUtils, normalize_text


class TestNormalizationUtils(FrappeTestCase):
    """Test suite for NormalizationUtils class."""

    def test_basic_normalization(self):
        """Test basic text normalization."""
        result = NormalizationUtils.normalize("  Hello World  ")
        self.assertEqual(result, "hello world")

    def test_empty_string(self):
        """Test empty string handling."""
        self.assertEqual(NormalizationUtils.normalize(""), "")
        self.assertEqual(NormalizationUtils.normalize(None), "")

    def test_arabic_normalization(self):
        """Test Arabic character normalization."""
        # Alef variants
        result = NormalizationUtils.normalize("أحمد")
        expected = NormalizationUtils.normalize("احمد")
        self.assertEqual(result, expected)

        # Taa Marbuta to Haa
        result = NormalizationUtils.normalize("شركة")
        expected = NormalizationUtils.normalize("شركه")
        self.assertEqual(result, expected)

    def test_arabic_diacritics_removal(self):
        """Test Arabic diacritics (harakat) are removed."""
        with_harakat = "مُحَمَّد"
        without_harakat = "محمد"

        result_with = NormalizationUtils.normalize(with_harakat)
        result_without = NormalizationUtils.normalize(without_harakat)

        self.assertEqual(result_with, result_without)

    def test_persian_character_mapping(self):
        """Test Persian character mapping."""
        # Arabic kaf to Persian kaf
        arabic_k = "ك"
        persian_k = "ک"

        result_ar = NormalizationUtils.normalize(arabic_k)
        result_fa = NormalizationUtils.normalize(persian_k)

        self.assertEqual(result_ar, result_fa)

    def test_latin_accent_removal(self):
        """Test Latin accented character normalization."""
        accented = "Café résumé naïve"
        expected = NormalizationUtils.normalize("Cafe resume naive")

        result = NormalizationUtils.normalize(accented)
        self.assertEqual(result, expected)

    def test_indian_to_arabic_digits(self):
        """Test Indian numeral to Arabic numeral conversion."""
        indian = "١٢٣٤٥"
        arabic = "12345"

        result = NormalizationUtils.normalize(indian)
        self.assertEqual(result, arabic)

    def test_whitespace_normalization(self):
        """Test multiple whitespace normalization."""
        text_with_spaces = "  Hello   World  "
        result = NormalizationUtils.normalize(text_with_spaces)
        self.assertEqual(result, "hello world")

    def test_similarity_score_exact_match(self):
        """Test similarity score for exact matches."""
        score = NormalizationUtils.get_similarity_score("hello", "hello")
        self.assertEqual(score, 100.0)

    def test_similarity_score_different_texts(self):
        """Test similarity score for different texts."""
        score = NormalizationUtils.get_similarity_score("hello", "world")
        self.assertLess(score, 50.0)

    def test_similarity_score_similar_texts(self):
        """Test similarity score for similar texts."""
        score = NormalizationUtils.get_similarity_score("hello world", "hello word")
        self.assertGreater(score, 80.0)

    def test_similarity_with_empty_strings(self):
        """Test similarity with empty strings."""
        score = NormalizationUtils.get_similarity_score("", "hello")
        self.assertEqual(score, 0.0)

        score = NormalizationUtils.get_similarity_score("hello", "")
        self.assertEqual(score, 0.0)

    def test_is_similar_above_threshold(self):
        """Test is_similar with texts above threshold."""
        result = NormalizationUtils.is_similar("hello world", "hello world", 90.0)
        self.assertTrue(result)

    def test_is_similar_below_threshold(self):
        """Test is_similar with texts below threshold."""
        result = NormalizationUtils.is_similar("hello", "goodbye", 80.0)
        self.assertFalse(result)

    def test_normalize_party_name(self):
        """Test party name normalization with suffix removal."""
        name_with_suffix = "Acme Corporation LLC"
        name_without = "Acme Corporation"

        result = NormalizationUtils.normalize_party_name(name_with_suffix)
        expected = NormalizationUtils.normalize(name_without)

        self.assertEqual(result, expected)

    def test_normalize_party_name_various_suffixes(self):
        """Test party name normalization with various suffixes."""
        test_cases = [
            ("Company Inc", "company"),
            ("Business Corp", "business"),
            ("Enterprise Ltd", "enterprise"),
            ("Firma GmbH", "firma"),
        ]

        for input_name, expected_base in test_cases:
            result = NormalizationUtils.normalize_party_name(input_name)
            self.assertEqual(result, expected_base, f"Failed for: {input_name}")

    def test_backward_compatibility_normalize_text(self):
        """Test backward compatible normalize_text function."""
        result = normalize_text("Hello World")
        self.assertEqual(result, "hello world")

    def test_normalize_for_search(self):
        """Test normalize_for_search method."""
        result = NormalizationUtils.normalize_for_search("  Hello World  ")
        self.assertEqual(result, "hello world")
