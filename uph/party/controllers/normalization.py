# Copyright (c) 2024, Abdo Ruzaqi and contributors
# For license information, please see license.txt

"""
Consolidated Normalization Utilities for UPH
Provides text normalization for fuzzy matching and duplicate detection.
Handles Arabic, Persian, and Latin character normalization.
"""

import re
import unicodedata
from functools import lru_cache
from typing import Optional


class NormalizationUtils:
    """
    Centralized normalization utilities for text processing.
    Consolidates logic from mdm.py and utils.py.
    """

    # Translation table for Arabic, Persian, and Latin accented characters
    TRANSLATION_TABLE = str.maketrans(
        {
            # Arabic normalization
            "أ": "ا",
            "إ": "ا",
            "آ": "ا",
            "ى": "ي",
            "ة": "ه",
            "ؤ": "و",
            "ئ": "ي",
            "ـ": "",
            # Persian character mapping
            "ك": "ک",
            "ي": "ی",
            # Digits from Indian to Arabic
            "٠": "0",
            "١": "1",
            "٢": "2",
            "٣": "3",
            "٤": "4",
            "٥": "5",
            "٦": "6",
            "٧": "7",
            "٨": "8",
            "٩": "9",
            # Latin accents (lowercase)
            "é": "e",
            "è": "e",
            "ê": "e",
            "ë": "e",
            "á": "a",
            "à": "a",
            "â": "a",
            "ä": "a",
            "í": "i",
            "ì": "i",
            "î": "i",
            "ï": "i",
            "ó": "o",
            "ò": "o",
            "ô": "o",
            "ö": "o",
            "ú": "u",
            "ù": "u",
            "û": "u",
            "ü": "u",
            "ç": "c",
            "ñ": "n",
            # Latin accents (uppercase)
            "É": "E",
            "È": "E",
            "Ê": "E",
            "Ë": "E",
            "Á": "A",
            "À": "A",
            "Â": "A",
            "Ä": "A",
            "Í": "I",
            "Ì": "I",
            "Î": "I",
            "Ï": "I",
            "Ó": "O",
            "Ò": "O",
            "Ô": "O",
            "Ö": "O",
            "Ú": "U",
            "Ù": "U",
            "Û": "U",
            "Ü": "U",
            "Ç": "C",
            "Ñ": "N",
        }
    )

    # Combining diacritical marks regex (Arabic + Latin)
    # Includes: Harakat (Arabic), Tanwin, Combining accents (Latin), etc.
    DIACRITIC_REGEX = re.compile(
        r"["
        r"\u064B-\u065F"  # Arabic harakat and tanwin
        r"\u06D6-\u06ED"  # Arabic extended harakat
        r"\u0300-\u036F"  # Combining diacritical marks (Latin)
        r"]+"
    )

    # Whitespace normalization regex
    WHITESPACE_REGEX = re.compile(r"\s+")

    @classmethod
    @lru_cache(maxsize=1024)
    def normalize(cls, text: str) -> str:
        """
        Normalize text for fuzzy matching.
        Removes diacritics, normalizes Arabic/Persian characters.
        Returns lowercase result for consistent comparison.
        """
        if not text:
            return ""

        # First, normalize unicode to NFD (decomposed form)
        # This separates accented characters into base + combining chars
        text = unicodedata.normalize("NFD", text)

        # Remove combining diacritical marks (Harakat, Arabic, Latin)
        text = cls.DIACRITIC_REGEX.sub("", text)

        # Translate characters (Arabic, Persian, Latin accents)
        text = text.translate(cls.TRANSLATION_TABLE)

        # Normalize again after translation (some chars may need re-normalization)
        text = unicodedata.normalize("NFC", text)

        # Normalize whitespace
        text = cls.WHITESPACE_REGEX.sub(" ", text)

        return text.strip().lower()

    @classmethod
    def normalize_for_search(cls, text: str) -> str:
        """
        Normalize text for search purposes.
        Less aggressive than full normalization.
        """
        if not text:
            return ""

        # Remove diacritics
        text = cls.DIACRITIC_REGEX.sub("", text)

        # Basic character normalization
        text = text.translate(cls.TRANSLATION_TABLE)

        return text.strip().lower()

    @classmethod
    def get_similarity_score(
        cls, text1: str, text2: str, method: str = "rapidfuzz"
    ) -> float:
        """
        Calculate similarity score between two texts.
        Returns score between 0 and 100.
        """
        normalized1 = cls.normalize(text1)
        normalized2 = cls.normalize(text2)

        if not normalized1 or not normalized2:
            return 0.0

        if method == "rapidfuzz":
            try:
                from rapidfuzz import fuzz

                return fuzz.ratio(normalized1, normalized2)
            except ImportError:
                pass

        # Fallback to difflib
        from difflib import SequenceMatcher

        return SequenceMatcher(None, normalized1, normalized2).ratio() * 100

    @classmethod
    def fuzzy_extract(
        cls, query: str, choices: list, scorer: str = "ratio", limit: int = 10
    ) -> list:
        """
        Extract top matches from choices using fuzzy matching.
        Returns list of (match, score, index) tuples.
        """
        if not query or not choices:
            return []

        try:
            from rapidfuzz import fuzz, process

            scorer_func = getattr(fuzz, scorer, fuzz.ratio)
            return process.extract(query, choices, scorer=scorer_func, limit=limit)
        except ImportError:
            # Fallback to difflib
            import difflib

            # difflib.get_close_matches returns strings, we need (match, score, index)
            matches = difflib.get_close_matches(query, choices, n=limit, cutoff=0.6)
            results = []
            for match in matches:
                idx = choices.index(match)
                # Calculate ratio for the score
                score = difflib.SequenceMatcher(None, query, match).ratio() * 100
                results.append((match, score, idx))
            return results

    @classmethod
    def is_similar(cls, text1: str, text2: str, threshold: float = 80.0) -> bool:
        """
        Check if two texts are similar based on threshold.
        Default threshold is 80%.
        """
        score = cls.get_similarity_score(text1, text2)
        return score >= threshold

    @classmethod
    def normalize_party_name(cls, name: str) -> str:
        """
        Normalize party name specifically.
        Used for deduplication checks.
        """
        if not name:
            return ""

        # Remove common prefixes/suffixes
        name = re.sub(
            r"^(LLC|L\.L\.C|Inc|Corp|Ltd|GmbH)\s+", "", name, flags=re.IGNORECASE
        )
        name = re.sub(
            r"\s+(LLC|L\.L\.C|Inc|Corp|Ltd|GmbH)$", "", name, flags=re.IGNORECASE
        )

        # Apply standard normalization
        return cls.normalize(name)


# Module-level functions for backward compatibility
def normalize_text(text: str) -> str:
    """Backward-compatible wrapper for NormalizationUtils.normalize()"""
    return NormalizationUtils.normalize(text)


def normalize_party_name(name: str) -> str:
    """Backward-compatible wrapper for NormalizationUtils.normalize_party_name()"""
    return NormalizationUtils.normalize_party_name(name)
