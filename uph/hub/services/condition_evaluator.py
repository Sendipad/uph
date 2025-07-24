from .condition_tree import ConditionTreeBuilder


class ConditionEvaluator:
    __slots__ = ("tree", "required_fields")

    def __init__(self, rule_name: str):
        self.tree = ConditionTreeBuilder.build(rule_name)
        self.required_fields = self.tree.get_required_fields()

    def evaluate(self, context: dict) -> bool:
        """Evaluate the full condition tree with a given context"""
        return self.tree.evaluate(context)

    def get_required_fields(self) -> list:
        return self.required_fields
