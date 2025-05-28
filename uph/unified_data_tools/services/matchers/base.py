import frappe


class BaseMatcher:
    def __init__(self, rule, cache=None):
        self.rule = rule
        self.cache = cache or {}

    def compare(self, doc1, doc2):
        raise NotImplementedError

    def normalize(self, val):
        if isinstance(val, str):
            return val.strip().lower()
        return str(val or "").lower()

    def get_value(self, doc):
        try:
            path = self.rule.field_path.split(".")
            value = doc
            for part in path:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return None
            return value
        except Exception as e:
            frappe.log_error(f"Error resolving field {self.rule.field_path}: {e}")
            return None
