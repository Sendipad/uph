import frappe
from frappe import _

from frappe.utils import flt
from frappe.utils.data import cint


def build_context(doc, rule, event_type=None):
    return {
        "doc": doc,
        "rule": rule,
        "event": event_type,
        "now": frappe.utils.now_datetime,
        "user": frappe.session.user,
        "session": frappe.session.data,
        "flags": frappe.flags,
        "resolve_value": lambda path: resolve_field_value(doc, path),
        "get_doc": frappe.get_doc,
        "get_value": frappe.db.get_value,
        "log_info": lambda msg: frappe.log(_(msg)),
        "log_error": lambda msg: frappe.log_error(_(msg)),
        "throw": lambda msg: frappe.throw(_(msg)),
        "variables": {},
    }


def resolve_field_value(doc, path):

    if "(" in path and ")" in path:
        return resolve_aggregate(doc, path)

    parts = path.split(".")
    value = doc

    for i, part in enumerate(parts):
        if part == "*":
            remaining = ".".join(parts[i + 1 :])
            result = []
            for child in value:
                res = resolve_field_value(child, remaining)
                if isinstance(res, list):
                    result.extend(res)
                else:
                    result.append(res)
            return result

        if isinstance(value, list):
            if part.isdigit():
                idx = cint(part)
                if 0 <= idx < len(value):
                    value = value[idx]
                else:
                    return None
            else:
                return [get_row_value(row, part) for row in value]

        if hasattr(value, part):
            value = getattr(value, part)
        elif isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None

    return value


def resolve_aggregate(doc, path):

    if "(" not in path or not path.endswith(")"):
        return 0

    func, field_path = path.split("(", 1)
    field_path = field_path.rstrip(")").strip()
    func = func.strip().upper()

    values = resolve_field_value(doc, field_path)
    if not isinstance(values, list):
        values = [values]

    numeric_values = []
    for v in values:
        try:
            numeric_values.append(flt(v))
        except Exception:
            continue

    if func == "COUNT":
        return len(values)

    if not numeric_values:
        return 0

    func_map = {
        "SUM": lambda x: sum(x),
        "AVG": lambda x: sum(x) / len(x),
        "MAX": lambda x: max(x),
        "MIN": lambda x: min(x),
    }

    return func_map.get(func, lambda x: 0)(numeric_values)


def get_row_value(row, fieldname):
    if isinstance(row, dict) and fieldname in row:
        return row[fieldname]
    elif hasattr(row, fieldname):
        return getattr(row, fieldname)
    return None
