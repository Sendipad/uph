# filepath: apps/uph/uph/hub/utils/scorer.py
import frappe
from frappe import _


@frappe.whitelist()
def execute_scorer_method(method: str, a: str, b: str) -> float:
    """Execute custom scorer method"""
    if not method or not frappe.db.exists("Registered Method", method):
        frappe.throw(_("Scorer method not found: {0}").format(method))

    try:
        return frappe.call(
            "uph.hub.services.registered_method.execute_method",
            method_name=method,
            params={"a": a, "b": b},
        )
    except Exception as e:
        frappe.log_error(
            title=_("Scorer method failed"),
            message=_("Method: {0}\nA: {1}\nB: {2}\nError: {3}").format(
                method, a, b, str(e)
            ),
        )
        return 0.0


@frappe.whitelist()
def get_scorer_options() -> list[str]:
    """Get available scorer options for UI"""
    return [
        "Levenshtein Distance",
        "Jaro-Winkler",
        "Token Set Ratio",
        "Partial Ratio",
        "Token Sort Ratio",
        "Soundex",
        "Metaphone",
        "Double Metaphone",
    ]
