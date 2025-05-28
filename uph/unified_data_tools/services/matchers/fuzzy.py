from rapidfuzz import fuzz
from .base import BaseMatcher


class FuzzyMatcher(BaseMatcher):
    def compare(self, doc1, doc2):
        val1 = self.get_value(doc1)
        val2 = self.get_value(doc2)
        val1 = self.normalize(val1)
        val2 = self.normalize(val2)
        return fuzz.token_set_ratio(val1, val2)
