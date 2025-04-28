import json
from collections import OrderedDict, defaultdict
import uph
import frappe
from frappe import qb, scrub
from frappe.desk.reportview import get_filters_cond, get_match_cond
from frappe.query_builder import Criterion, CustomFunction,DocType
from frappe.query_builder.functions import Concat, Locate, Sum,Coalesce, Count
from frappe.query_builder.custom import ConstantColumn
from frappe.utils import nowdate, today, unique, add_months
from pypika import Order
from frappe import _
from frappe.utils.caching import redis_cache





@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def party_master_link_query(doctype, txt, searchfield, page_len, start, filters=None, reference_doctype=None):
    party_type = filters.get("party_type") if filters else None
    top_parties = []
    document_type = frappe.get_all('Party Master Settings DocType', pluck='document_type')

    if reference_doctype and reference_doctype in document_type:
        top_parties = usage_counts_on_reference_doctype(reference_doctype)

    meta = frappe.get_meta(doctype)
    search_fields = meta.get_search_fields() or []
    fields = ['pm.name'] + [f'pm.{f}' for f in search_fields]

    if meta.get("show_title_field_in_link") and meta.get("title_field"):
        fields.insert(1, f'pm.{meta.get("title_field")}')

    fields = unique(fields)  
    select_fields = ", ".join(fields)
    conditions=['pm.docstatus<2 ']
    if not filters.get('is_group'):
        conditions.append('pm.is_group=0 ')
        
    if not filters.get('disabled'):
        conditions.append('pm.disabled=0')
    where_conditions=' And '.join(conditions)
    params = []
    if party_type:
        params += [party_type, party_type]
    params += [f"%{txt}%", f"%{txt}%", f"%{txt}%",f"%{txt}%"]
    mariadb=''
    if top_parties:
        params += top_parties  # These are used in FIELD(pm.name, ...)
    params += [15, 0]
    top_case = ""
    if top_parties:
        top_case = "CASE " + " ".join([
            f"WHEN pm.name = %s THEN {i}" for i in range(len(top_parties))
        ]) + " ELSE 999 END"

    query = frappe.db.multisql({
       "mariadb": f"""
            SELECT
                {select_fields}
            FROM
                `tabParty Master` pm
            LEFT JOIN
                `tabParty Master Role` pr ON pr.parent = pm.name
            WHERE
                {where_conditions}
                {"AND (pm.party_type = %s OR pr.party_type_role = %s)" if party_type else ""}
                AND (
                    pm.party_name LIKE %s OR
                    pm.name LIKE %s OR
                    pm.mobile_no LIKE %s OR
                    pm.party_details LIKE %s
                )
            GROUP BY pm.name
            ORDER BY
                {"FIELD(pm.name, " + ', '.join(['%s'] * len(top_parties)) + ") DESC," if top_parties else ""}
                pm.party_name ASC
            LIMIT %s OFFSET %s
        """,

        "postgres": f"""
            SELECT
                {select_fields}
            FROM
                "tabParty Master" pm
            LEFT JOIN
                "tabParty Master Role" pr ON pr.parent = pm.name
            WHERE             {where_conditions}
                {"AND (pm.party_type = %s OR pr.party_type_role = %s)" if party_type else ""}
                AND (
                    pm.party_name ILIKE %s OR
                    pm.party_number ILIKE %s OR
                    pm.mobile_no ILIKE %s OR
                    pm.party_details ILIKE %s
                )
            GROUP BY pm.name
            ORDER BY
                {top_case + "," if top_case else ""}
                pm.party_name ASC
            LIMIT %s OFFSET %s
        """
    }, params)

    return query
  

# Deprectated 
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_party_master(doctype, txt, searchfield, start, page_len, filters):
    PartyMaster = frappe.qb.DocType("Party Master")
    filters = frappe._dict(filters or {})
    reference_doctype = filters.get("reference_doctype") or filters.get("on_doctype") or None
    meta = frappe.get_meta(doctype)
    PartyMasterRole = DocType("Party Master Role")

    if reference_doctype and not txt:
       result=_get_set_cached_pm_list(reference_doctype)
       if result:
           return result
    qb_filter_and_conditions = [PartyMaster.docstatus < 2]
    qb_filter_or_conditions = []
    ifelse = CustomFunction("IF", ["condition", "then", "else"])
    
    
    fields = get_fields(doctype,  ['name', 'party_name'])
    
    # Set default filters if not provided
    if 'is_group' not in filters:
        qb_filter_and_conditions.append(PartyMaster.is_group == 0)
    if 'disabled' not in filters:
        qb_filter_and_conditions.append(PartyMaster.disabled == 0)
    
    query = frappe.qb.from_(PartyMaster).select(*[PartyMaster[field] for field in fields])

    # Process filters
    for key, value in filters.items():
        if key == 'party_type':
                query = query.left_join(PartyMasterRole).on(
                    PartyMasterRole.parent == PartyMaster.name)
                qb_filter_and_conditions.append(
                    (PartyMaster.party_type == value) | 
                    (PartyMasterRole.party_type_role == value)
                )
        elif key in ['is_group', 'disabled', 'doctype', 'on_doctype', 'reference_doctype'] or not meta.has_field(key):
            continue
        else:
            qb_filter_and_conditions.append(PartyMaster[key] == value)
    
    # Build query (excluding usage_count from SELECT)
    
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
        for field in meta.get_search_fields():
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
                99999
            )
        )
    query = query.limit(page_len).offset(start)

    # Execute query
    result = query.run()
    if not txt:
        _get_set_cached_pm_list(reference_doctype,result)
    
    return result
#
def usage_counts_on_reference_doctype(doctype,cached=True):
    """ 
    This will return list of Party Master that Most has been set on the Reference Doctype
    This will make Link search on party_master link field filteres and find most used
    
    """
    meta=frappe.get_meta(doctype)
    if meta.issingle:
        return []
    key=f'UPH:usage_count-{doctype}-{frappe.session.user}'
    result=frappe.cache.get_value(key)
    if result and cached:
        return result
    link_field='party_master' if meta.has_field('party_master') else None
    if not link_field:
        return
    Ref = DocType(doctype)
    three_months_ago = add_months(nowdate(), -3)

    top_used = frappe.qb.from_(Ref).select(getattr(Ref, link_field))\
                .where(
                    (Ref.creation >= three_months_ago) &
                    (getattr(Ref, link_field).isnotnull()) &
                    (Ref.docstatus < 2)&
                    (Ref.owner == frappe.session.user)
                )\
                .groupby(getattr(Ref, link_field))\
                .orderby(Count("*"), order=Order.desc)\
                .limit(20).run()
    if top_used:
       result = [row[0] for row in top_used] if top_used else []
       frappe.cache.set_value(key, result, expires_in_sec=86400)
    return result or []
@frappe.whitelist()
def get_party_master_parties(party_master, party_type=None,cached=True):
    
    # Try to get from cache if party_master is a string
    parties = frappe.cache.hget(uph.make_key("Party Master.parties"),party_master if isinstance(party_master, str) else None)

    if cached and parties:
        # Filter by party_type if specified
        if party_type:
            return [p for p in parties if p.get('party_type') == party_type]
        return parties

    # Fetch from DB if not in cache
    parties = get_party_master_parties_db(party_master, all_roles=True)
    if not parties:
        return []

    # Cache result if party_master is a string
    if isinstance(party_master, str):
        frappe.cache.hset(uph.make_key("Party Master.parties"),party_master,parties)
        if not cached:
            return

    # Filter again if needed
    if party_type:
        return [p for p in parties if p.get('party_type') == party_type]

    return parties
 

def get_roles_for_pm(party_master):
    """
    Get the roles for a given party master.
    Args:
        party_master (str): The name of the party master.
    Returns:
        list: A list of roles associated with the party master.
    """
    if not party_master:
        return []
    
    # Check if roles are already cached
    key = uph.get_cached_key('roles')
    roles = frappe.cache.get_value(key, party_master)
    if not roles:
        roles=_get_roles_for_pm(party_master)
        uph.update_cached('roles',party_master,roles)
    return roles
@frappe.whitelist()
def get_party_master_parties_db(party_master, all_roles=False, roles=None):
    if not all_roles and not roles and isinstance(party_master, str):
        roles = get_roles_for_pm(party_master)
    if not roles:
        roles = uph.get_party_type_list()

    queries = []
    for r in roles:
        queries.append(build_fetch_parties_query(r, party_master))

    if queries:
        final_query = queries[0]
        for q in queries[1:]:
            final_query = final_query.union(q)

        final_query = (
            final_query
            .orderby("party_master")
            .orderby("party_type")
            .orderby("currency",order=frappe.qb.desc)
            .orderby("is_default", order=frappe.qb.desc)
        )

        return final_query.run(as_dict=True)
   
@redis_cache()
def get_mapped_party_to_party_master_dict():
    on_party_type=uph.get_party_type_list()
    quries=[]
    for p in on_party_type:
        doctype=DocType(p)
        quries.append(frappe.qb.from_(doctype)
                      .select(ConstantColumn(p),doctype.name,doctype.party_master)
                      .where(doctype.party_master.isnotnull())
                      )
    if quries:
        final_query=quries[0]
        for q in quries[1:]:
            final_query=final_query.union(q)
        data=final_query.run(as_dict=False)
        return { (t[0], t[1]): t[2] for t in data }
        

def get_mapped_party_to_party_master(on_party_type=None):
    if on_party_type and isinstance(on_party_type,str):
        on_party_type=[on_party_type]
    if not on_party_type:
        on_party_type=uph.get_party_type_list()
    quries=[]
    for p in on_party_type:
        doctype=DocType(p)
        quries.append(frappe.qb.from_(doctype).select(doctype.name,doctype.party_master,ConstantColumn(p)).where(doctype.party_master.isnotnull()))
    if quries:
        final_query=quries[0]
        for q in quries[1:]:
            final_query=final_query.union(q)
        return final_query.run()
    
def build_fetch_parties_query(doctype:str, party_master:str|list=None):
    PartyType = DocType(doctype)
    query = frappe.qb.from_(PartyType)
    meta = frappe.get_meta(doctype)

    if doctype == "Customer":
        query = query.select(
            PartyType.name.as_("party"),
            PartyType.customer_name.as_("party_name"),
            PartyType.default_currency.as_("currency"),
            ConstantColumn(doctype).as_("party_type"),
            PartyType.party_master,
            PartyType.is_default_for_party_master.as_("is_default") if meta.has_field("is_default_for_party_master") else ConstantColumn(0).as_("is_default"),
        )
    elif doctype == "Supplier":
        query = query.select(
            PartyType.name.as_("party"),
            PartyType.supplier_name.as_("party_name"),
            PartyType.default_currency.as_("currency"),
            ConstantColumn(doctype).as_("party_type"),
            PartyType.party_master,
            PartyType.is_default_for_party_master.as_("is_default") if meta.has_field("is_default_for_party_master") else ConstantColumn(0).as_("is_default"),
        )
    elif doctype == "Employee":
        query = query.select(
            PartyType.name.as_("party"),
            PartyType.employee_name.as_("party_name"),
            PartyType.salary_currency.as_("currency"),
            ConstantColumn(doctype).as_("party_type"),
            PartyType.party_master,
            PartyType.is_default_for_party_master.as_("is_default") if meta.has_field("is_default_for_party_master") else ConstantColumn(0).as_("is_default"),
        )
    else:
        query = query.select(
            PartyType.name.as_("party"),
            PartyType.title.as_("party_name") if meta.has_field("title") else ConstantColumn("").as_("party_name"),
            ConstantColumn("").as_("currency"),
            ConstantColumn(doctype).as_("party_type"),
            PartyType.party_master,
            PartyType.is_default_for_party_master.as_("is_default") if meta.has_field("is_default_for_party_master") else ConstantColumn(0).as_("is_default"),
        )
    if party_master:
        if isinstance(party_master, str):
            query = query.where(PartyType.party_master == party_master)
        elif isinstance(party_master, list):
            query = query.where(PartyType.party_master.isin(party_master))
    else:
        query = query.where(PartyType.party_master.isnotnull()&(PartyType.party_master != ""))
    return query

@frappe.whitelist()
def get_linked_parties_list(party_master_filters: str | list = None, party_type=None):
    if party_type is None:
        party_type=uph.get_party_type_list()
        #party_type = frappe.get_all("Party Type", pluck="name",order_by="name ASC")
    if isinstance(party_type, str):
        party_type = [party_type]

    queries = []
    for pt in party_type:
        meta=frappe.get_meta(pt)
        if not meta.has_field("party_master"):
            continue  # Skip if 'party_master' field does not exist

        PartyType = DocType(pt)
        q = frappe.qb.from_(PartyType)
        # Selecting relevant fields based on Party Type
        if pt == "Customer":
            q = q.select(
                PartyType.name,
                PartyType.customer_name.as_("party_name"),
                PartyType.default_currency.as_("currency"),
                ConstantColumn(pt).as_("party_type"),
                PartyType.party_master,
            )
        elif pt == "Supplier":
            q = q.select(
                PartyType.name,
                PartyType.supplier_name.as_("party_name"),
                PartyType.default_currency.as_("currency"),
                ConstantColumn(pt).as_("party_type"),
                PartyType.party_master,
            )
        elif pt == "Employee":
            q = q.select(
                PartyType.name,
                PartyType.employee_name.as_("party_name"),
                PartyType.salary_currency.as_("currency"),
                ConstantColumn(pt).as_("party_type"),
                PartyType.party_master,
            )
        else:
            q = q.select(
                PartyType.name,
                PartyType.title.as_("party_name") if meta.has_field("title") else ConstantColumn("").as_("party_name"),
                ConstantColumn("").as_("currency"),
                ConstantColumn(pt).as_("party_type"),
                PartyType.party_master,
            )

        # Apply filtering based on party_master_filters
        if party_master_filters is None:
            q = q.where((PartyType.party_master.isnull()) | (PartyType.party_master == ""))
        elif isinstance(party_master_filters, str):
            q = q.where(PartyType.party_master == party_master_filters)
        elif isinstance(party_master_filters, list):
            if len(party_master_filters) == 1:
                q = q.where(PartyType.party_master.isin(party_master_filters))
            elif len(party_master_filters) > 1:
                filter_type, values = party_master_filters[0], party_master_filters[1]

                if isinstance(values, list):
                    if filter_type == "not in":
                        q = q.where(PartyType.party_master.notin(values))
                    elif filter_type == "in":
                        q = q.where(PartyType.party_master.isin(values))
                elif filter_type == "is" and values == "not set":
                    q = q.where((PartyType.party_master.isnull()) | (PartyType.party_master == ""))

        queries.append(q)

    # Combine queries using UNION if multiple queries exist
    if queries:
        final_query = queries[0]
        for q in queries[1:]:
            final_query = final_query.union(q)

        return final_query.run(as_dict=True)

    return []

@frappe.whitelist()
def query_similar_name_or_number(party_name=None,party_number=None):
    if not party_name and not party_number:
        return {}
    if party_number and not party_name:
        if frappe.db.exists('Party Master',{'party_number':party_number}):
            return {'exact_number':1}
        else:
            return {}
    result=None
    if party_name and not party_number:
        exact_name=frappe.db.exists('Party Master',{'party_name':party_name})
        if exact_name:
            result={'exact_name':1}
        
        names=party_name.split()
        name="{0}{1}".format(names[0]," " +names[-1] if len(names)>1 else "")
        similar=frappe.db.get_list('Party Master',filters={'party_name':['like',f'%{name}%']},pluck='party_name',limit=5)
        if similar :
            if result:
                result.update({'similar':similar})
        else:
            result={'similar':similar}
    return result
        
    
def _get_set_cached_pm_list(reference_doctype,value=None):
    key=f"_pm_list-{reference_doctype}"
    if not value:
        return frappe.cache.get_value(key)
    frappe.cache.set_value(key,value,expires_in_sec=60)
    

def get_fields(doctype, fields=None):
	if fields is None:
		fields = []
	meta = frappe.get_meta(doctype)
	fields.extend(meta.get_search_fields())

	if meta.get("show_title_field_in_link")  and meta.get("title_field"):
		fields.insert(1,  meta.get("title_field"))

	return unique(fields)



def _get_roles_for_pm(party_master):
    """
    Fetch roles for a given party master.
    Args:
        party_master (str): The name of the party master.
    Returns:
        list: A list of roles associated with the party master.
    """
    if not party_master:
        return []
    roles=[frappe.get_value('Party Master',party_master,'party_type')]
    PartyMasterRole = DocType("Party Master Role")
    query = (
        frappe.qb.from_(PartyMasterRole)
        .select(PartyMasterRole.party_type_role)
        .where(PartyMasterRole.parent == party_master)
    ).run()
    if query:
        roles.extend(query)
    return roles
