from .base import BaseMatcher

# from frappe import _


class ChildTableMatcher(BaseMatcher):
    def compare(self, doc1, doc2):
        table_field, child_field = self.rule.field_path.split(".", 1)

        items1 = self._get_child_values(doc1, table_field, child_field)
        items2 = self._get_child_values(doc2, table_field, child_field)

        if not items1 or not items2:
            return 0

        if self.rule.match_strategy == "Any Item":
            return self._match_any(items1, items2)
        elif self.rule.match_strategy == "All Items":
            return self._match_all(items1, items2)
        else:  # Exact Sequence
            return self._match_exact(items1, items2)

    def _get_child_values(self, doc, table_field, child_field):
        if isinstance(doc, dict):
            return [item.get(child_field) for item in doc.get(table_field, [])]
        return [item.get(child_field) for item in doc.get(table_field) or []]

    def _match_any(self, items1, items2):
        set1 = set(items1)
        set2 = set(items2)
        common = set1 & set2
        return (len(common) / max(len(set1), 1)) * 100

    def _match_all(self, items1, items2):
        return 100 if set(items1) == set(items2) else 0

    def _match_exact(self, items1, items2):
        return 100 if items1 == items2 else 0
