# Copyright (c) 2024, Abdo Ruzaqi and Contributors
# See license.txt
import frappe
from frappe.tests.utils import FrappeTestCase
from uph.party.doctype.party_master.party_master import get_parties,check_similar_party_name
from frappe.utils.caching import redis_cache

class TestPartyMaster(FrappeTestCase):
	pass

def test_get_parties():
    party_master='131000004'
    return get_parties(party_master,fromdb=True)

def test_cached_parties():
    cache=frappe.cache()
    key='pm_parties_131000004'
    if cache.get_value(key):
        return cache.get_value(key)
    return test_get_parties()

def test_check_similar_party_name():
    pn='علي احم'
    return check_similar_party_name(pn)

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_query(doctype, txt, searchfield, start, page_len, filters):
    from frappe.query_builder import DocType, Order, Case
    from frappe.query_builder.functions import Coalesce
    from frappe.query_builder.functions import Concat, Locate, Sum
    #from frappe.query_builder import and_, or_

    PartyMaster = DocType("Party Master")
    PartyMasterRole = DocType("Party Master Role")
    reference_doctype = filters.get("reference_doctype") or filters.get("on_doctype")
    meta = frappe.get_meta(doctype)
    if not  reference_doctype and on_doctype:
        reference_doctype=on_doctype
    result=None
    meta = frappe.get_meta(doctype)
    fields = ["name"]
    if (not txt or txt == '') and reference_doctype:
        result=get_set_cached_pm_list(reference_doctype)
        if result:
            return result
    # Get search fields
    search_fields = meta.get_search_fields()
    if meta.get("show_title_field_in_link") and meta.get("title_field"):
        title_field = meta.get("title_field")
        if title_field not in search_fields:
            search_fields.insert(1, title_field)
        fields.append(title_field)
    fields.extend(search_fields)
    fields = list(set(fields))  # Ensure unique fields

    # Base condition: Exclude deleted documents
    combined_conditions = and_(
        PartyMaster.docstatus < 2,
        PartyMaster.disabled == 0,
        PartyMaster.is_group == 0
    )

    # Party Type Filtering using LEFT JOIN Subquery
    party_type = filters.get("party_type") if isinstance(filters, dict) else None
    on_doctype = filters.get("on_doctype") if isinstance(filters, dict) else None

    if not party_type and on_doctype:
        party_type = get_party_type_from_doctype(on_doctype)

     # Party Type Filtering
    if party_type:
        role_subquery = (
            frappe.qb.from_(PartyMasterRole)
            .select(PartyMasterRole.parent)
            .where(PartyMasterRole.party_type_role == party_type)
            .where(PartyMasterRole.parent == PartyMaster.name)
        )
        combined_conditions = combined_conditions & (
            (PartyMaster.party_type == party_type) | 
            Exists(role_subquery)
        )

    # Handle Filters (Supports both Dict and List of Lists)
    if isinstance(filters, dict):
        for key, value in filters.items():
            if key not in ["party_type", "on_doctype", "reference_doctype"] and meta.has_field(key):
                combined_conditions = combined_conditions & (PartyMaster[key] == value)

    elif isinstance(filters, list):
        for f in filters:
            if len(f) != 3:
                continue  # Ignore malformed filters

            field, operator, value = f
            if not meta.has_field(field):
                continue  # Ignore invalid fields

            if operator.lower() in ["=", "!=", ">", "<", ">=", "<="]:
                conditions.append(getattr(PartyMaster[field], operator)(value))
            elif operator.lower() == "like":
                conditions.append(PartyMaster[field].like(f"%{value}%"))
            elif operator.lower() == "in" and isinstance(value, (list, tuple)):
                conditions.append(PartyMaster[field].isin(value))
            elif operator.lower() == "between" and isinstance(value, (list, tuple)) and len(value) == 2:
                conditions.append((PartyMaster[field] >= value[0]) & (PartyMaster[field] <= value[1]))

    # Search Condition
    search_conditions = [
        PartyMaster[field].like(f"%{txt}%") for field in search_fields
    ]
    if search_conditions and txt:
        combined_conditions = combined_conditions & or_(*search_conditions)
    # **Usage Count Subquery (Only If reference_doctype is Provided)**
    usage_count_field = None
    if reference_doctype:
        ReferenceDoc = DocType(reference_doctype)
        three_months_ago = add_months(nowdate(), -3)

        usage_subquery = (
            frappe.qb.from_(ReferenceDoc)
            .select(Count(ReferenceDoc.name))
            .where(ReferenceDoc.party_master == PartyMaster.name)
            .where(ReferenceDoc.creation >= three_months_ago)
        )

        usage_count_field = Coalesce(usage_subquery, 0).as_("usage_count")

    # [Previous code remains the same until order_by section]

    # Corrected order_by configuration
    order_by = []

    # Add usage count ordering if exists
    if usage_count_field:
        order_by.append((usage_count_field, Order.desc))

    # Add case statements
    order_by.extend([
        Case().when(Locate(txt, PartyMaster.name) > 0, Locate(txt, PartyMaster.name)).else_(99999),
        Case().when(Locate(txt, PartyMaster.party_name) > 0, Locate(txt, PartyMaster.party_name)).else_(99999)
    ])

    # Add regular fields with proper tuple syntax
    order_by.extend([
        (PartyMaster.idx, Order.desc),
        (PartyMaster.name, Order.asc),
        (PartyMaster.party_name, Order.asc)
    ])

    # Filter out None values
    order_by = [o for o in order_by if o is not None]

    # Build final query
    select_fields = fields.copy()
    if usage_count_field:
        select_fields.append(usage_count_field)
    query = (
        frappe.qb.from_(PartyMaster)
        .select(*select_fields)
        .where(combined_conditions)  # Pass single combined condition
        .orderby(*order_by)
        .limit(page_len)
        .offset(start)
        )

    result = query.run(as_dict=True)
    if (not txt or txt == '') and filters.get('reference_doctype'):
        get_set_cached_pm_list(reference_doctype,action='set',value=result)
    return result
