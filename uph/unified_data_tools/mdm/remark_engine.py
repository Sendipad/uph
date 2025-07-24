"""
def generate_remark(doc, method=None):
    if not method:
        return

    # Get rules for this specific doctype and method
    rule_names = (
        get_document_type_run_validate_events(document_type=doc.doctype, method=method)
        or []
    )

    if not rule_names:
        return

    context_parent = {"doc": doc.as_dict()}

    for rule_name in rule_names:
        rule_doc = frappe.get_cached_doc("Auto Text Generator Rule", rule_name)

        if not rule_doc.template or not rule_doc.template.strip():
            continue

        if rule_doc.on_child:
            if "." not in rule_doc.remark_fieldname:
                continue  # invalid field path

            table_field, child_field = rule_doc.remark_fieldname.split(".", 1)
            child_rows = doc.get(table_field, [])

            # updated = False

            for row in child_rows:
                context = {"doc": row.as_dict(), "parent": doc.as_dict()}
                if evaluate_filters(rule_doc.conditions, row):
                    try:
                        remark = frappe.render_template(
                            rule_doc.template, context
                        ).strip()
                        if remark:
                            row.set(child_field, remark)
                            # row.flags.dirty = True  # <--- ✅ this is key
                            frappe.msgprint(
                                _("{0} Has been Set to {1} at row {2}").format(
                                    remark, row.name, row.idx
                                ),
                                alert=1,
                            )

                            # updated = True
                    except Exception as e:
                        frappe.log_error(f"Render error (child): {e}", "Remark Rule")

            # if updated:
            # Optional, forces Frappe to detect change
            # doc.set(table_field, child_rows)

        else:
            if evaluate_filters(rule_doc.conditions, doc):
                try:
                    remark = frappe.render_template(
                        rule_doc.template, context_parent
                    ).strip()
                    if remark:
                        doc.set(rule_doc.remark_fieldname, remark)
                        frappe.msgprint(
                            _("{0} Has been Set to {1}").format(remark, doc.name),
                            alert=1,
                        )
                        continue
                except Exception as e:
                    frappe.log_error(f"Render error (parent): {e}", "Remark Rule")
    return doc


def evaluate_filters(conditions, doc_context):
    for cond in conditions:
        field_parts = cond.fieldname.split(".", 1)
        if len(field_parts) == 2:
            field = field_parts[1]  # field in child row
        else:
            field = cond.fieldname

        value = doc_context.get(field)
        if not match_condition(value, cond.condition, cond.value):
            return False
    return True


def match_condition(field_value, operator, condition_value):
    if operator == "==":
        return field_value == condition_value
    elif operator == "!=":
        return field_value != condition_value
    elif operator == ">":
        return field_value > condition_value
    elif operator == "<":
        return field_value < condition_value
    elif operator == ">=":
        return field_value >= condition_value
    elif operator == "<=":
        return field_value <= condition_value
    elif operator == "in":
        try:
            values = frappe.parse_json(condition_value)
            return field_value in values
        except Exception:
            return False
    elif operator == "not in":
        try:
            values = frappe.parse_json(condition_value)
            return field_value not in values
        except Exception:
            return False
    elif operator == "is set":
        return field_value is not None and field_value != ""
    elif operator == "not set":
        return field_value is None or field_value == ""
    else:
        # Unknown operator, fail safe
        return False


@frappe.whitelist()
def generate_remarks_for_save_doc(doctype, docname, rule):
    doc = frappe.get_doc(doctype, docname)
    rule_doc = frappe.get_cached_doc("Auto Text Generator Rule", rule)
    context_parent = {"doc": doc.as_dict()}

    if not rule_doc.template or not rule_doc.template.strip():
        return

    if rule_doc.on_child:
        if "." not in rule_doc.remark_fieldname:
            return
        table_field, child_field = rule_doc.remark_fieldname.split(".", 1)
        child_rows = doc.get(table_field, [])

        updated = False  # track if any child was updated

        for row in child_rows:
            context = {"doc": row.as_dict(), "parent": doc.as_dict()}
            if evaluate_filters(rule_doc.conditions, row):
                try:
                    remark = frappe.render_template(rule_doc.template, context).strip()
                    if remark:
                        row.set(child_field, remark)
                        updated = True
                except Exception as e:
                    frappe.log_error(f"Render error (child): {e}", "Remark Rule")

        if updated:
            doc.save()
            return "Child remarks set"

    else:
        if evaluate_filters(rule_doc.conditions, doc):
            try:
                remark = frappe.render_template(
                    rule_doc.template, context_parent
                ).strip()
                if remark:
                    doc.set(rule_doc.remark_fieldname, remark)
                    doc.save()
                    return remark
            except Exception as e:
                frappe.log_error(f"Render error (parent): {e}", "Remark Rule")
"""
