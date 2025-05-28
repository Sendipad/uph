from .base import BaseMatcher


class ExactMatcher(BaseMatcher):
    def compare(self, doc1, doc2):
        val1 = self.get_value(doc1)
        val2 = self.get_value(doc2)
        val1 = self.normalize(val1)
        val2 = self.normalize(val2)
        return 100 if val1 == val2 else 0
