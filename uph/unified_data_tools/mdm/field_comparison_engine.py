import frappe
from frappe.query_builder import DocType
from functools import reduce
from operator import or_
from uph.unified_data_tools.utils.field import get_field_options

COMPARISON_FUNCTIONS = {
    "Equals": lambda a, b: a == b,
    "Not Equals": lambda a, b: a != b,
    "Greeter Than": lambda a, b: a > b,
    "Less Than": lambda a, b: a < b,
    "Both Empty": lambda a, b: not a and not b,
    "Only One Set": lambda a, b: bool(a) != bool(b),
    "Both Set": lambda a, b: bool(a) and bool(b),
}


class FieldComparisonEngine:
    def __init__(self, job_or_doc):
        self.job = job_or_doc if hasattr(job_or_doc, "rules") else None
        self.doc_type = getattr(job_or_doc, "document_type", None)

        self.rules = []
        if self.job:
            self.rules = [
                frappe.get_doc("Field Comparison Rule", r.rule)
                for r in self.job.rules
                if frappe.db.get_value("Field Comparison Rule", r.rule, "enabled")
            ]
        else:
            self.rules = [
                frappe.get_doc("Field Comparison Rule", r.name)
                for r in frappe.get_all(
                    "Field Comparison Rule",
                    filters={"document_type": job_or_doc.doctype, "enabled": 1},
                    fields=["name"],
                )
            ]

        self.grouped_rules = self._group_rules()

    def _parse_path(self, path):
        parts = path.split(".")
        return {
            "is_child": len(parts) == 2,
            "child_table": parts[0] if len(parts) == 2 else None,
            "field": parts[-1],
        }

    def _group_rules(self):
        grouped = {"parent": [], "child": {}, "join": {}}
        for rule in self.rules:
            lhs = self._parse_path(rule.fieldname)
            rhs = self._parse_path(rule.with_field)
            if not lhs["is_child"] and not rhs["is_child"]:
                grouped["parent"].append(rule)
            elif (
                lhs["is_child"]
                and rhs["is_child"]
                and lhs["child_table"] == rhs["child_table"]
            ):
                grouped["child"].setdefault(lhs["child_table"], []).append(rule)
            else:
                child_table = lhs["child_table"] or rhs["child_table"]
                grouped["join"].setdefault(child_table, []).append(rule)
        return grouped

    def _get_child_doctype(self, parent_doctype, table_fieldname):
        meta = frappe.get_meta(parent_doctype)
        for field in meta.fields:
            if field.fieldname == table_fieldname and field.fieldtype == "Table":
                return field.options
        return None

    def _build_value_condition(self, lhs, rhs, comp_type):
        if comp_type == "Equals":
            return lhs != rhs
        if comp_type == "Not Equals":
            return lhs == rhs
        if comp_type == "Greeter Than":
            return lhs <= rhs
        if comp_type == "Less Than":
            return lhs >= rhs
        return None

    def _check_rule(self, rule, val1, val2):
        if rule.comparison_type == "Custom Expression":
            try:
                return eval(rule.custom_expression, {}, {"val1": val1, "val2": val2})
            except Exception:
                return True
        fn = COMPARISON_FUNCTIONS.get(rule.comparison_type)
        return fn(val1, val2) if fn else True

    def _format_result(self, docname, rule, row, child_row=None):
        fieldname_1 = self._parse_path(rule.fieldname)["field"]
        fieldname_2 = self._parse_path(rule.with_field)["field"]
        value_1 = row.get(fieldname_1)
        value_2 = row.get(fieldname_2)

        return {
            "document": docname,
            "rule": rule.name,
            "rule_label": rule.get("title") or rule.name,
            "fieldname": fieldname_1,
            "with_field": fieldname_2,
            "value_1": value_1,
            "value_2": value_2,
            "child_row": child_row,
            "result": "Mismatch",
        }

    def _log_data_quality_task(self, result):
        try:
            label_1 = self._get_field_label(result["fieldname"])
            label_2 = self._get_field_label(result["with_field"])
            comparison = result.get("comparison_type", "Comparison")

            note = frappe._(
                "<b>Rule:</b> {rule}<br><b>Violation:</b> {comparison}<br>"
                "<b>{label1}</b>: {val1}<br><b>{label2}</b>: {val2}"
            ).format(
                rule=result["rule_label"],
                comparison=comparison,
                label1=label_1,
                val1=result["value_1"] or "—",
                label2=label_2,
                val2=result["value_2"] or "—",
            )

            frappe.get_doc(
                {
                    "doctype": "Data Quality Task",
                    "reference_type": "Field Comparison Job",
                    "reference_name": self.job.name,
                    "document_type": self.doc_type,
                    "docname_a": result["document"],
                    "docname_b": result.get("child_row"),
                    "score": 0,
                    "resolved": 0,
                    "priority": "Medium",
                    "note": note,
                }
            ).insert(ignore_permissions=True)

        except Exception:
            frappe.log_error(frappe.get_traceback(), "Failed to log Data Quality Task")

    def _build_violation_condition(self, lhs, rhs, comp_type):
        """Build SQL condition for rule violation"""
        if comp_type == "Equals":
            return lhs != rhs
        elif comp_type == "Not Equals":
            return lhs == rhs
        elif comp_type == "Greeter Than":
            return lhs <= rhs
        elif comp_type == "Less Than":
            return lhs >= rhs
        elif comp_type == "Both Empty":
            return lhs.notnull() | rhs.notnull()
        elif comp_type == "Only One Set":
            return (lhs.isnull() & rhs.isnull()) | (lhs.notnull() & rhs.notnull())
        elif comp_type == "Both Set":
            return lhs.isnull() | rhs.isnull()
        return None

    def _get_field_label(self, field_path):
        parsed = self._parse_path(field_path)
        if not parsed["is_child"]:
            return (
                frappe.get_meta(self.doc_type).get_label(parsed["field"])
                or parsed["field"]
            )
        child_doctype = self._get_child_doctype(self.doc_type, parsed["child_table"])
        if not child_doctype:
            return parsed["field"]
        return (
            frappe.get_meta(child_doctype).get_label(parsed["field"]) or parsed["field"]
        )

    def _query_group(self, rules, context):
        parent = DocType(self.doc_type)
        query = frappe.qb.from_(parent)

        # 1) Apply ignore_cancelled_doc filter
        if getattr(self.job, "ignore_cancelled_doc", False):

            query = query.where(parent.docstatus != 2)

        # 2) Apply filters_json filter if any
        if self.job.filters_json:
            try:
                filters = frappe.parse_json(self.job.filters_json)
                for key, val in filters.items():
                    if isinstance(val, list) and len(val) == 2:
                        op, cmp_val = val
                        if op == "!=":
                            query = query.where(parent[key] != cmp_val)
                        elif op == "=":
                            query = query.where(parent[key] == cmp_val)
                        # Add more operators as needed
                    else:
                        query = query.where(parent[key] == val)
            except Exception:
                frappe.log_error(frappe.get_traceback(), "Invalid filters_json")
        table_fieldname = None
        child = None

        if context.startswith("child:") or context.startswith("join:"):
            table_fieldname = context.split(" ")[-1]
            child_doctype = self._get_child_doctype(self.doc_type, table_fieldname)
            if not child_doctype:
                return []
            child = DocType(child_doctype)
            query = query.join(child).on(
                (child.parent == parent.name) & (child.parenttype == self.doc_type)
            )

        # Determine required fields
        select_fields = {parent.name}
        for rule in rules:
            if rule.comparison_type == "Custom Expression":
                continue
            for field_path in [rule.fieldname, rule.with_field]:
                parsed = self._parse_path(field_path)
                table = child if parsed["is_child"] else parent
                select_fields.add(table[parsed["field"]])

        # Apply WHERE clause
        conditions = []
        for rule in rules:
            if rule.comparison_type == "Custom Expression":
                continue
            lhs = self._parse_path(rule.fieldname)
            rhs = self._parse_path(rule.with_field)
            lhs_field = (child if lhs["is_child"] else parent)[lhs["field"]]
            rhs_field = (child if rhs["is_child"] else parent)[rhs["field"]]
            condition = self._build_violation_condition(
                lhs_field, rhs_field, rule.comparison_type
            )
            if condition:
                conditions.append(condition)

        if not conditions:
            return []

        query = query.select(*select_fields).where(reduce(or_, conditions))
        rows = query.run(as_dict=True)
        return self._post_process_batch(rows, rules)

    def _post_process_batch(self, rows, rules):
        results = []
        for row in rows:
            for rule in rules:
                fieldname_1 = self._parse_path(rule.fieldname)["field"]
                fieldname_2 = self._parse_path(rule.with_field)["field"]
                val1 = row.get(fieldname_1)
                val2 = row.get(fieldname_2)

                if not self._check_rule(rule, val1, val2):
                    result = self._handle_rule_violation(
                        docname=row.get("name") or row.get("parent"),
                        rule=rule,
                        row=row,
                        child_row=row.get("name") if "parent" in row else None,
                    )
                    results.append(result)
        return results

    def _handle_rule_violation(self, docname, rule, row, child_row=None):
        # Parse paths
        parsed_1 = self._parse_path(rule.fieldname)
        parsed_2 = self._parse_path(rule.with_field)

        fieldname_1 = parsed_1["field"]
        fieldname_2 = parsed_2["field"]

        value_1 = row.get(fieldname_1)
        value_2 = row.get(fieldname_2)

        result = {
            "document": docname,
            "rule": rule.name,
            "rule_label": rule.get("title") or rule.name,
            "fieldname": fieldname_1,
            "with_field": fieldname_2,
            "value_1": value_1,
            "value_2": value_2,
            "child_row": child_row,
            "result": "Mismatch",
            "comparison_type": rule.comparison_type,
        }

        if self.job:
            try:
                # Use your utils field list for accurate labels
                all_fields = get_field_options(self.doc_type)
                label_1 = next(
                    (f["label"] for f in all_fields if f["value"] == rule.fieldname),
                    rule.fieldname,
                )
                label_2 = next(
                    (f["label"] for f in all_fields if f["value"] == rule.with_field),
                    rule.with_field,
                )

                note = frappe._(
                    "<b>Rule:</b> {rule}<br>"
                    "<b>Violation:</b> {comparison}<br>"
                    "<b>{label1}</b>: {val1}<br><b>{label2}</b>: {val2}"
                ).format(
                    rule=result["rule_label"],
                    comparison=result["comparison_type"],
                    label1=label_1,
                    val1=value_1 or "—",
                    label2=label_2,
                    val2=value_2 or "—",
                )

                frappe.get_doc(
                    {
                        "doctype": "Data Quality Task",
                        "reference_type": "Field Comparison Job",
                        "reference_name": self.job.name,
                        "document_type": self.doc_type,
                        "docname_a": result["document"],
                        "docname_b": result.get("child_row"),
                        "score": 0,
                        "resolved": 0,
                        "priority": rule.priority,
                        "note": note,
                    }
                ).insert(ignore_permissions=True)

            except Exception:
                frappe.log_error(
                    frappe.get_traceback(), "Failed to log Data Quality Task"
                )

        return result

    def run_batch(self):
        results = []
        if self.grouped_rules["parent"]:
            results.extend(
                self._query_group(self.grouped_rules["parent"], context="parent")
            )
        for table, rules in self.grouped_rules["child"].items():
            results.extend(
                self._query_group(rules, context=f"child:{self.doc_type} {table}")
            )
        for table, rules in self.grouped_rules["join"].items():
            results.extend(
                self._query_group(rules, context=f"join:{self.doc_type} {table}")
            )
        return results

    def validate_document(self, doc):
        errors = []
        for rule in self.rules:
            lhs = self._parse_path(rule.fieldname)
            rhs = self._parse_path(rule.with_field)

            if not lhs["is_child"] and not rhs["is_child"]:
                val1 = doc.get(lhs["field"])
                val2 = doc.get(rhs["field"])
                if not self._check_rule(rule, val1, val2):
                    errors.append(
                        self._format_result(
                            doc.name, rule, {"val1": val1, "val2": val2}
                        )
                    )

            elif (
                lhs["is_child"]
                and rhs["is_child"]
                and lhs["child_table"] == rhs["child_table"]
            ):
                for idx, row in enumerate(doc.get(lhs["child_table"]) or [], start=1):
                    val1 = row.get(lhs["field"])
                    val2 = row.get(rhs["field"])
                    if not self._check_rule(rule, val1, val2):
                        errors.append(
                            self._format_result(doc.name, rule, row, child_row=idx)
                        )

            else:
                child_table = lhs["child_table"] or rhs["child_table"]
                for idx, row in enumerate(doc.get(child_table) or [], start=1):
                    if lhs["is_child"]:
                        val1 = row.get(lhs["field"])
                        val2 = doc.get(rhs["field"])
                    else:
                        val1 = doc.get(lhs["field"])
                        val2 = row.get(rhs["field"])
                    if not self._check_rule(rule, val1, val2):
                        errors.append(
                            self._format_result(doc.name, rule, row, child_row=idx)
                        )
        return errors
