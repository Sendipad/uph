import frappe
from frappe import qb, scrub
from frappe.desk.reportview import get_filters_cond, get_match_cond
from frappe.query_builder import Criterion, CustomFunction, DocType
from frappe.query_builder.functions import Concat, Locate, Sum, Coalesce, Count
from frappe.utils import nowdate, today, unique, add_months
from pypika import Order
from frappe import _


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_party_master(doctype, txt, searchfield, start, page_len, filters):
    PartyMaster = frappe.qb.DocType("Party Master")
    filters = frappe._dict(filters or {})
    reference_doctype = (
        filters.get("reference_doctype") or filters.get("on_doctype") or None
    )
    meta = frappe.get_meta(doctype)

    qb_filter_and_conditions = [PartyMaster.docstatus < 2]
    qb_filter_or_conditions = []
    ifelse = CustomFunction("IF", ["condition", "then", "else"])

    fields = get_fields(doctype, ["name", "party_name"])

    # Set default filters if not provided
    if "is_group" not in filters:
        qb_filter_and_conditions.append(PartyMaster.is_group == 0)
    if "disabled" not in filters:
        qb_filter_and_conditions.append(PartyMaster.disabled == 0)

    # Process filters
    for key, value in filters.items():
        if key == "party_type":
            qb_filter_and_conditions.append(
                (PartyMaster.party_type == value)
                | (PartyMaster.has_secondary_role_party == 1)
            )
        elif key in [
            "is_group",
            "disabled",
            "doctype",
            "on_doctype",
            "reference_doctype",
        ] or not meta.has_field(key):
            continue
        else:
            qb_filter_and_conditions.append(PartyMaster[key] == value)

    # Build query (excluding usage_count from SELECT)
    query = frappe.qb.from_(PartyMaster).select(
        *[PartyMaster[field] for field in fields]
    )

    # Add usage count subquery directly inside ORDER BY (not selecting it)
    if reference_doctype:
        ReferenceDoc = DocType(reference_doctype)
        three_months_ago = add_months(nowdate(), -3)
        usage_subquery = (
            frappe.qb.from_(ReferenceDoc)
            .select(Count(ReferenceDoc.name))
            .where(ReferenceDoc.party_master == PartyMaster.name)
            .where(ReferenceDoc.creation >= three_months_ago)
        )
        query = query.orderby(Coalesce(usage_subquery, 0), order=Order.desc)

    # Apply search text conditions
    if txt:
        for field in fields:
            qb_filter_or_conditions.append(PartyMaster[field].like(f"%{txt}%"))

    # Combine conditions
    if qb_filter_and_conditions:
        query = query.where(Criterion.all(qb_filter_and_conditions))
    if qb_filter_or_conditions:
        query = query.where(Criterion.any(qb_filter_or_conditions))

    # Order by relevance if txt is provided
    title_field = meta.get("title_field") or "name"
    if txt:
        query = query.orderby(
            ifelse(
                Locate(txt, PartyMaster[title_field]) > 0,
                Locate(txt, PartyMaster[title_field]),
                99999,
            )
        )
    query = query.limit(20)
    query = query.offset(start)
    # Execute query
    result = query.run()

    return result


def get_fields(doctype, fields=None):
    if fields is None:
        fields = []
    meta = frappe.get_meta(doctype)
    fields.extend(meta.get_search_fields())

    if meta.get("show_title_field_in_link") and meta.get("title_field"):
        fields.insert(1, meta.get("title_field"))

    return unique(fields)
