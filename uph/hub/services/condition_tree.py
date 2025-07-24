# filepath: apps/uph/uph/hub/services/condition_tree.py
import frappe
import operator
import json
import re
from frappe import _
from frappe.utils import getdate, now_datetime, cint
from typing import List, Dict, Any, Callable
from rapidfuzz import fuzz, utils
from .cache import (
    get_cached_condition_tree,
    set_cached_condition_tree,
    clear_rule_doc_cache,
)
from rapidfuzz.distance import JaroWinkler

# Operator mapping with null-safe handling
OPERATOR_MAP = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
    "contains": lambda a, b: b in str(a) if a is not None else False,
    "not contains": lambda a, b: b not in str(a) if a is not None else True,
    "is set": lambda a, b: a is not None,
    "is not set": lambda a, b: a is None,
    "in": lambda a, b: a in b if b and hasattr(b, "__contains__") else False,
    "not in": lambda a, b: a not in b if b and hasattr(b, "__contains__") else True,
    "between": lambda a, b: (
        b[0] <= a <= b[1] if isinstance(b, (list, tuple)) and len(b) == 2 else False
    ),
}


class ConditionNode:
    __slots__ = (
        "condition_data",
        "operator",
        "negate",
        "fuzzy_threshold",
        "scorer",
        "custom_scorer",
        "regex_pattern",
        "normalization_profile",
        "normalized_record",
        "comparison_strategy",
        "is_critical",
        "use_in_filter",
        "weight",
        "final_left_path",
        "final_right_path",
    )

    def __init__(self, condition_data: Dict[str, Any]):
        # Store raw condition data for reference
        self.condition_data = condition_data

        # Core properties
        self.operator = condition_data.get("operator")
        self.negate = bool(condition_data.get("negate_condition", False))

        # Fuzzy matching properties
        self.fuzzy_threshold = float(condition_data.get("fuzzy_threshold") or 80)
        self.scorer = condition_data.get("scorer", "token_set_ratio")
        self.custom_scorer = condition_data.get("custom_scorer")

        # Regex properties
        self.regex_pattern = condition_data.get("regex_pattern")

        # Normalization properties
        self.normalization_profile = condition_data.get("normalization_profile")
        self.normalized_record = bool(condition_data.get("normalized_record", False))

        # Comparison strategy
        self.comparison_strategy = condition_data.get(
            "comparison_strategy", "Auto Detect"
        )

        # Special properties
        self.is_critical = bool(condition_data.get("is_critical", False))
        self.use_in_filter = bool(condition_data.get("use_in_filter", False))
        self.weight = float(condition_data.get("weight") or 1.0)

        # Resolved field paths
        self.final_left_path = condition_data.get("final_left_field_path")
        self.final_right_path = condition_data.get("final_right_field_path")

    def evaluate(self, context: Dict) -> bool:
        """Evaluate condition against context with robust error handling"""
        try:
            # Get left-hand value
            left_val = self._resolve_value("left", context)

            # Handle special operators first
            if self.operator == "is set":
                result = left_val is not None
            elif self.operator == "is not set":
                result = left_val is None
            elif self.operator == "fuzzy_match":
                result = self._evaluate_fuzzy(left_val, context)
            elif self.operator == "regex_match":
                result = self._evaluate_regex(left_val, context)
            else:
                # Get right-hand value for other operators
                right_val = self._resolve_value("right", context)

                # Get operator function
                op_func = OPERATOR_MAP.get(self.operator)
                if not op_func:
                    frappe.log_error(
                        title=_("Unknown operator"),
                        message=_("Operator '{0}' not recognized").format(
                            self.operator
                        ),
                    )
                    return False

                # Handle None values for other operators
                if left_val is None:
                    return False

                # Apply comparison strategy
                left_val, right_val = self._apply_comparison_strategy(
                    left_val, right_val
                )

                result = op_func(left_val, right_val)

            # Apply negation and return
            return not result if self.negate else result
        except Exception as e:
            self.log_evaluation_error(e)
            return False

    def _resolve_value(self, side: str, context: Dict) -> Any:
        """Resolve value based on source configuration"""
        source = self.condition_data.get(f"{side}_value_source")
        field_path = self.final_left_path if side == "left" else self.final_right_path

        # Handle normalized records first
        if self.normalized_record and field_path:
            return self._get_normalized_value(context, field_path)

        # Handle different value sources
        if source == "Literal Value":
            return self.condition_data.get(f"{side}_value_literal")

        if source == "Context Variable":
            key = self.condition_data.get(f"{side}_value_context_key")
            return context["variables"].get(key) if key else None

        if source == "Registered Method Result":
            method = self.condition_data.get(f"{side}_value_method")
            params = json.loads(
                self.condition_data.get(f"{side}_method_parameters") or "{}"
            )
            return self._execute_method(method, params, context)

        # Document Field or Specific DocType Field
        if field_path:
            return context["resolve_value"](field_path)

        return None

    def _get_normalized_value(self, context: Dict, field_path: str) -> Any:
        """Get normalized value for a field if available"""
        doc = context["doc"]

        # Try to get from normalization record
        normalized = frappe.db.get_value(
            "Normalization Record",
            {
                "document_type": doc.doctype,
                "docname": doc.name,
                "field_path": field_path,
            },
            "normalized_data",
        )

        return normalized or context["resolve_value"](field_path)

    def _execute_method(self, method_name: str, params: Dict, context: Dict) -> Any:
        """Execute registered method with parameter resolution"""
        if not method_name or not frappe.db.exists("Registered Method", method_name):
            return None

        method_doc = frappe.get_cached_doc("Registered Method", method_name)
        resolved_params = self._resolve_method_params(params, context)

        try:
            return frappe.call(method_doc.method_path, **resolved_params)
        except Exception as e:
            frappe.log_error(
                title=_("Method execution failed"),
                message=_("Method: {0}\nParams: {1}\nError: {2}").format(
                    method_name, str(resolved_params), str(e)
                ),
            )
            return None

    def _resolve_method_params(self, params: Dict, context: Dict) -> Dict:
        """Resolve method parameters with context substitution"""
        resolved = {}

        for key, value in params.items():
            if isinstance(value, str) and value.startswith("ctx:"):
                resolved[key] = context["variables"].get(value[4:])
            else:
                resolved[key] = value

        return resolved

    def _evaluate_fuzzy(self, left_val: Any, context: Dict) -> bool:
        """Handle fuzzy matching with RapidFuzz"""
        # Get right value
        right_val = self._resolve_value("right", context)

        # Skip if values are empty
        if left_val is None or right_val is None:
            return False

        # Convert to strings
        left_str = str(left_val)
        right_str = str(right_val)

        # Apply normalization if specified
        if self.normalization_profile:
            left_str = self._normalize_string(left_str, self.normalization_profile)
            right_str = self._normalize_string(right_str, self.normalization_profile)

        # Get scorer function
        scorer_func = self._get_scorer_function()

        # Calculate similarity score (0-100 scale)
        score = scorer_func(left_str, right_str)

        # Store score in context for debugging
        context.setdefault("fuzzy_scores", {})[self.final_left_path] = score

        # Evaluate based on threshold
        return score >= self.fuzzy_threshold

    def _evaluate_regex(self, left_val: Any, context: Dict) -> bool:
        """Handle regex pattern matching"""
        if not self.regex_pattern or left_val is None:
            return False

        # Convert to string
        text = str(left_val)

        # Apply normalization if specified
        if self.normalization_profile:
            text = self._normalize_string(text, self.normalization_profile)

        try:
            # Compile and match pattern
            pattern = re.compile(self.regex_pattern)
            return bool(pattern.search(text))
        except re.error as e:
            frappe.log_error(
                title=_("Regex pattern error"),
                message=_("Pattern: {0}\nError: {1}").format(
                    self.regex_pattern, str(e)
                ),
            )
            return False

    def _normalize_string(self, value: str, profile_name: str) -> str:
        """Normalize a string using the specified profile"""
        from uph.hub.utils.normalizer import normalizer

        return normalizer(value, profile=profile_name)

    def get_similarity_score(self, value1, value2):
        """Calculate similarity score for deduplication"""
        # Apply normalization if configured
        if self.normalization_profile:
            value1 = self.normalize_value(value1)
            value2 = self.normalize_value(value2)

        return self._calculate_similarity(value1, value2)

    def normalize_value(self, value):
        """Apply normalization to a value"""
        if not value:
            return value

        from uph.hub.utils.normalizer import normalizer

        return normalizer(value, profile=self.normalization_profile)

    def _calculate_similarity(self, value1, value2):
        """Calculate similarity based on configured scorer"""
        scorer_name = self.scorer or "Levenshtein Distance"
        scorer_func = self.SCORERS.get(scorer_name, fuzz.ratio)

        # Convert to strings for comparison
        str1 = str(value1) if value1 is not None else ""
        str2 = str(value2) if value2 is not None else ""

        # Calculate raw score
        raw_score = scorer_func(str1, str2)

        # Normalize to 0-1 range
        if scorer_name == "Exact Match":
            return raw_score / 100
        elif scorer_name in ["Jaro-Winkler"]:
            return raw_score  # Already 0-1
        else:
            return raw_score / 100

    # Add SCORERS class attribute
    SCORERS = {
        "Levenshtein Distance": fuzz.ratio,
        "Jaro-Winkler": JaroWinkler.similarity,
        "Token Set Ratio": fuzz.token_set_ratio,
        "Partial Ratio": fuzz.partial_ratio,
        "Token Sort Ratio": fuzz.token_sort_ratio,
        "Exact Match": lambda s1, s2: 100 if s1 == s2 else 0,
    }

    def _get_scorer_function(self) -> Callable[[str, str], float]:
        """Get the appropriate scorer function"""
        # Custom scorer takes precedence
        if self.custom_scorer:
            return self._get_custom_scorer(self.custom_scorer)

        # Built-in scorers
        return {
            "Levenshtein Distance": fuzz.ratio,
            "Jaro-Winkler": JaroWinkler.similarity,
            "Token Set Ratio": fuzz.token_set_ratio,
            "Partial Ratio": fuzz.partial_ratio,
            "Token Sort Ratio": fuzz.token_sort_ratio,
            "Soundex": self._soundex_scorer,
            "Metaphone": self._metaphone_scorer,
            "Double Metaphone": self._double_metaphone_scorer,
        }.get(self.scorer, fuzz.token_set_ratio)

    def _get_custom_scorer(self, method_name: str) -> Callable[[str, str], float]:
        """Get custom scorer from registered method"""

        def scorer(a: str, b: str) -> float:
            return frappe.call(
                "uph.hub.utils.scorer.execute_scorer_method",
                method=method_name,
                a=a,
                b=b,
            )

        return scorer

    def _soundex_scorer(self, a: str, b: str) -> float:
        """Soundex similarity scorer"""
        soundex_a = utils.default_process(a) if a else ""
        soundex_b = utils.default_process(b) if b else ""
        return 100.0 if soundex_a == soundex_b else 0.0

    def _metaphone_scorer(self, a: str, b: str) -> float:
        """Metaphone similarity scorer"""
        meta_a = utils.default_process(a) if a else ""
        meta_b = utils.default_process(b) if b else ""
        return 100.0 if meta_a == meta_b else 0.0

    def _double_metaphone_scorer(self, a: str, b: str) -> float:
        """Double Metaphone similarity scorer"""
        dmeta_a = utils.default_process(a) if a else ""
        dmeta_b = utils.default_process(b) if b else ""
        return 100.0 if dmeta_a == dmeta_b else 0.0

    def _apply_comparison_strategy(self, left_val: Any, right_val: Any) -> tuple:
        """Apply comparison strategy to values"""
        strategy = self.comparison_strategy

        if strategy == "Auto Detect":
            # Attempt to convert to numbers if possible
            try:
                return float(left_val), float(right_val)
            except (ValueError, TypeError):
                try:
                    # Try date parsing
                    return getdate(left_val), getdate(right_val)
                except Exception:
                    return str(left_val), str(right_val)

        if strategy == "Numeric":
            try:
                return float(left_val), float(right_val)
            except (ValueError, TypeError):
                return 0.0, 0.0

        if strategy == "Date":
            # Convert to datetime objects
            try:
                return getdate(left_val), getdate(right_val)
            except Exception:
                return now_datetime(), now_datetime()

        if strategy == "Boolean":
            # Convert to boolean
            return bool(cint(left_val)), bool(cint(right_val))

        # Default to string comparison
        return str(left_val), str(right_val)

    def log_evaluation_error(self, error: Exception):
        """Log evaluation error with context"""
        frappe.log_error(
            title=_("Condition evaluation failed"),
            message=_(
                "Condition: {0}\n"
                "Operator: {1}\n"
                "Left Path: {2}\n"
                "Right Path: {3}\n"
                "Error: {4}"
            ).format(
                self.condition_data.get("name", "Unknown"),
                self.operator,
                self.final_left_path or "",
                self.final_right_path or "",
                str(error),
            ),
        )

    def get_required_fields(self) -> List[str]:
        """Get all field paths required for this condition"""
        fields = []

        # Left field
        if self.condition_data.get("left_value_source") in (
            "Document Field",
            "Specific DocType Field",
        ):
            if path := self.final_left_path:
                fields.append(path)

        # Right field
        if self.condition_data.get("right_value_source") in (
            "Document Field",
            "Specific DocType Field",
        ):
            if path := self.final_right_path:
                fields.append(path)

        return fields


class ConditionGroup:
    __slots__ = ("operator", "children", "negate")

    def __init__(self, operator: str = "AND", negate: bool = False):
        self.operator = operator
        self.children = []  # ConditionNodes or ConditionGroups
        self.negate = negate

    def evaluate(self, context: Dict) -> bool:
        """Evaluate condition group with short-circuit logic"""
        if not self.children:
            return True

        result = False
        if self.operator == "AND":
            result = True
            for child in self.children:
                if not child.evaluate(context):
                    result = False
                    break
        else:  # OR
            result = False
            for child in self.children:
                if child.evaluate(context):
                    result = True
                    break

        return not result if self.negate else result

    def get_required_fields(self) -> List[str]:
        """Get all field paths required for this group"""
        fields = []
        for child in self.children:
            if hasattr(child, "get_required_fields"):
                fields.extend(child.get_required_fields())
        return list(set(fields))


class ConditionTreeBuilder:
    # Keep in-memory cache for current process
    _in_memory_cache = frappe._dict()

    @classmethod
    def build(cls, rule_name: str) -> ConditionGroup:
        """Build condition tree with multi-layer caching"""
        # 1. Check in-memory cache
        if rule_name in cls._in_memory_cache:
            return cls._in_memory_cache[rule_name]

        # 2. Check Redis cache
        cached_tree = get_cached_condition_tree(rule_name)
        if cached_tree:
            cls._in_memory_cache[rule_name] = cached_tree
            return cached_tree

        # 3. Build new tree if not in cache
        try:
            conditions = cls._get_conditions(rule_name)
            tree = cls._build_tree(conditions)

            # Cache in Redis and memory
            set_cached_condition_tree(rule_name, tree)
            cls._in_memory_cache[rule_name] = tree

            return tree
        except Exception as e:
            frappe.log_error(
                title=_("Condition tree build failed"),
                message=_("Rule: {0}\nError: {1}").format(rule_name, str(e)),
            )
            # Return empty group that always evaluates to True
            return ConditionGroup()

    @classmethod
    def _get_conditions(cls, rule_name: str) -> List[Dict]:
        """Get conditions with optimized query"""
        return frappe.get_all(
            "Rule Condition",
            filters={"parent": rule_name},
            fields=["*"],
            order_by="idx",
        )

    @classmethod
    def _build_tree(cls, conditions: List[Dict]) -> ConditionGroup:
        """Construct condition tree hierarchy with proper grouping"""
        root = ConditionGroup(operator="AND")
        current_group = root
        stack = []
        last_node = None

        for cond in conditions:
            grouping_type = cond.get("grouping_type")
            logical_operator = cond.get("logical_operator", "AND")

            # Handle grouping operators
            if grouping_type == "Start Group (AND)":
                new_group = ConditionGroup(
                    operator="AND", negate=bool(cond.get("negate_condition", False))
                )
                current_group.children.append(new_group)
                stack.append((current_group, last_node))
                current_group = new_group
                last_node = None
                continue

            elif grouping_type == "Start Group (OR)":
                new_group = ConditionGroup(
                    operator="OR", negate=bool(cond.get("negate_condition", False))
                )
                current_group.children.append(new_group)
                stack.append((current_group, last_node))
                current_group = new_group
                last_node = None
                continue

            elif grouping_type == "End Group":
                if stack:
                    current_group, last_node = stack.pop()
                continue

            # Handle regular condition
            node = ConditionNode(cond)

            # Handle logical operators between conditions
            if logical_operator == "OR" and last_node is not None:
                # Create OR wrapper group
                or_group = ConditionGroup(operator="OR")
                or_group.children.append(last_node)
                or_group.children.append(node)

                # Replace last node with OR group
                current_group.children[-1] = or_group
                last_node = or_group
            else:
                # Add directly to current group
                current_group.children.append(node)
                last_node = node

        return root

    @classmethod
    def clear_cache(cls, rule_name: str = None):
        """Clear cache for specific rule or entire cache"""
        # Clear in-memory cache
        if rule_name:
            if rule_name in cls._in_memory_cache:
                del cls._in_memory_cache[rule_name]
        else:
            cls._in_memory_cache = frappe._dict()

        # Clear Redis cache
        clear_rule_doc_cache(rule_name)


class ConditionEvaluator:
    __slots__ = ("tree", "required_fields")

    def __init__(self, rule_name: str):
        self.tree = ConditionTreeBuilder.build(rule_name)
        self.required_fields = self.tree.get_required_fields()

    def evaluate(self, context: Dict) -> bool:
        """Evaluate conditions against context"""
        return self.tree.evaluate(context)

    def get_required_fields(self) -> List[str]:
        """Get all field paths required for evaluation"""
        return self.required_fields


@frappe.whitelist()
def test_condition(rule_name: str, doctype: str, docname: str):
    """API for testing condition evaluation"""
    from .context_builder import build_context

    # Check permission
    if not frappe.has_permission("Rule", "read", rule_name):
        frappe.throw(
            _("You don't have permission to access this rule"), frappe.PermissionError
        )

    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw(
            _("You don't have permission to access this document"),
            frappe.PermissionError,
        )

    doc = frappe.get_doc(doctype, docname)
    rule = frappe.get_doc("Rule", rule_name)

    context = build_context(doc, rule)
    evaluator = ConditionEvaluator(rule_name)
    result = evaluator.evaluate(context)

    return {
        "result": result,
        "required_fields": evaluator.get_required_fields(),
        "resolved_values": {
            field: context["resolve_value"](field)
            for field in evaluator.get_required_fields()
        },
    }
