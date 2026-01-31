import uph
import frappe
from frappe.query_builder import Criterion, CustomFunction, DocType
from frappe.query_builder.functions import Locate, Coalesce, Count
from frappe.query_builder.custom import ConstantColumn
from frappe.utils import nowdate, unique, add_months
from pypika import Order
from frappe.utils.caching import redis_cache
from frappe import _

from uph.party.controllers.cache_utils import (
    get_configured_doctypes,
    get_doctypes_functional_fields_mapping_as_dict,
)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def party_master_link_query(
    doctype, txt, searchfield, page_len, start, filters=None, reference_doctype=None
):
    party_type = filters.get("party_type") if filters else None
    top_parties = []
    document_type = list(get_configured_doctypes())

    if reference_doctype and reference_doctype in document_type:
        top_parties = usage_counts_on_reference_doctype(reference_doctype)

    meta = frappe.get_meta(doctype)
    search_fields = meta.get_search_fields() or []
    fields = ["pm.name"] + [f"pm.{f}" for f in search_fields]

    if meta.get("show_title_field_in_link") and meta.get("title_field"):
        fields.insert(1, f'pm.{meta.get("title_field")}')

    fields = unique(fields)
    select_fields = ", ".join(fields)
    conditions = ["pm.docstatus<2 "]
    if not filters.get("is_group"):
        conditions.append("pm.is_group=0 ")

    if not filters.get("disabled"):
        conditions.append("pm.disabled=0")
    where_conditions = " And ".join(conditions)
    params = []
    if party_type:
        params += [party_type, party_type]
    params += [f"%{txt}%", f"%{txt}%", f"%{txt}%", f"%{txt}%"]
    if top_parties:
        params += top_parties  # These are used in FIELD(pm.name, ...)
    params += [15, 0]
    top_case = ""
    if top_parties:
        top_case = (
            "CASE "
            + " ".join([f"WHEN pm.name = %s THEN {i}" for i in range(len(top_parties))])
            + " ELSE 999 END"
        )

    query = frappe.db.multisql(
        {
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
        """,
        },
        params,
    )

    return query


# Deprectated
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_party_master(doctype, txt, searchfield, start, page_len, filters):
    PartyMaster = frappe.qb.DocType("Party Master")
    filters = frappe._dict(filters or {})
    reference_doctype = (
        filters.get("reference_doctype") or filters.get("on_doctype") or None
    )
    meta = frappe.get_meta(doctype)
    PartyMasterRole = DocType("Party Master Role")

    if reference_doctype and not txt:
        result = _get_set_cached_pm_list(reference_doctype)
        if result:
            return result
    qb_filter_and_conditions = [PartyMaster.docstatus < 2]
    qb_filter_or_conditions = []
    ifelse = CustomFunction("IF", ["condition", "then", "else"])

    fields = get_fields(doctype, ["name", "party_name"])

    # Set default filters if not provided
    if "is_group" not in filters:
        qb_filter_and_conditions.append(PartyMaster.is_group == 0)
    if "disabled" not in filters:
        qb_filter_and_conditions.append(PartyMaster.disabled == 0)

    query = frappe.qb.from_(PartyMaster).select(
        *[PartyMaster[field] for field in fields]
    )

    # Process filters
    for key, value in filters.items():
        if key == "party_type":
            query = query.left_join(PartyMasterRole).on(
                PartyMasterRole.parent == PartyMaster.name
            )
            qb_filter_and_conditions.append(
                (PartyMaster.party_type == value)
                | (PartyMasterRole.party_type_role == value)
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
                99999,
            )
        )
    query = query.limit(page_len).offset(start)

    # Execute query
    result = query.run()
    if not txt:
        _get_set_cached_pm_list(reference_doctype, result)

    return result


#
def usage_counts_on_reference_doctype(doctype, cached=True):
    """
    This will return list of Party Master that Most has been set on the Reference Doctype
    This will make Link search on party_master link field filteres and find most used

    """
    meta = frappe.get_meta(doctype)
    if meta.issingle:
        return []
    key = f"UPH:usage_count-{doctype}-{frappe.session.user}"
    result = frappe.cache.get_value(key)
    if result and cached:
        return result
    link_field = "party_master" if meta.has_field("party_master") else None
    if not link_field:
        return
    Ref = DocType(doctype)
    three_months_ago = add_months(nowdate(), -3)

    top_used = (
        frappe.qb.from_(Ref)
        .select(getattr(Ref, link_field))
        .where(
            (Ref.creation >= three_months_ago)
            & (getattr(Ref, link_field).isnotnull())
            & (Ref.docstatus < 2)
            & (Ref.owner == frappe.session.user)
        )
        .groupby(getattr(Ref, link_field))
        .orderby(Count("*"), order=Order.desc)
        .limit(20)
        .run()
    )
    if top_used:
        result = [row[0] for row in top_used] if top_used else []
        frappe.cache.set_value(key, result, expires_in_sec=86400)
    return result or []


def get_leaf_party_master_list_from_any_node(filters):
    if not filters or not filters.get("party_master"):
        return None
    group_party_master = frappe.db.get_all(
        "Party Master", filters={"is_group": 1, "disabled": 0}, pluck="name"
    )
    party_master = []
    parents = set()

    if isinstance(filters.get("party_master"), str):
        filters["party_master"] = [filters.get("party_master")]
    for p in filters.get("party_master"):
        if p not in group_party_master:
            party_master.append(p)
            continue
        parents.add(p)
    if not parents:
        return party_master

    def collect_all_group_children(current_parents):
        found_new = True
        while found_new:
            found_new = False
            child_groups = frappe.db.get_all(
                "Party Master",
                filters={
                    "parent_party_master": ["in", list(current_parents)],
                    "is_group": 1,
                },
                fields=["name"],
            )
            for child in child_groups:
                if child.name not in current_parents:
                    current_parents.add(child.name)
                    found_new = True
        return current_parents

    all_group_names = collect_all_group_children(parents)

    # Now fetch all non-group (leaf) parties under any of the group names collected
    party_master.extend(
        frappe.db.get_all(
            "Party Master",
            filters={
                "parent_party_master": ["in", list(all_group_names)],
                "is_group": 0,
            },
            pluck="name",
        )
    )

    return party_master


@frappe.whitelist()
def get_party_master_parties(party_master, party_type=None, cached=True):

    # Try to get from cache if party_master is a string
    parties = frappe.cache.hget(
        uph.make_key("Party Master.parties"),
        party_master if isinstance(party_master, str) else None,
    )

    if cached and parties:
        # Filter by party_type if specified
        if party_type:
            return [p for p in parties if p.get("party_type") == party_type]
        return parties

    # Fetch from DB if not in cache
    parties = get_party_master_parties_db(party_master, all_roles=True)
    if not parties:
        return []

    # Cache result if party_master is a string
    if isinstance(party_master, str):
        frappe.cache.hset(uph.make_key("Party Master.parties"), party_master, parties)
        if not cached:
            return

    # Filter again if needed
    if party_type:
        return [p for p in parties if p.get("party_type") == party_type]

    return parties


@frappe.whitelist()
def get_all_vouchers_documents_with_null_or_another_party_master(
    doctypes=None, parties=None, party_master=None
):
    # Get unique rules from cache to avoid duplicate processing
    mapping = get_doctypes_functional_fields_mapping_as_dict()
    # We use a dict to deduplicate by unique (parent_doctype, document_type) or just use the values unique id
    # Since mapping can have same object for multiple keys, we explicitly grab unique objects
    # But wait, cache_utils creates new dicts.
    # Let's trust that the mapping contains valid configuration.
    # To get unique list of settings:
    doctype_rules = []
    seen = set()
    for d in mapping.values():
        identifier = (d.get("parent_doctype"), d.get("document_type"))
        if identifier not in seen:
            doctype_rules.append(d)
            seen.add(identifier)

    if not doctypes:
        doctypes = [
            d for d in doctype_rules if not frappe.get_meta(d.parent_doctype).issingle
        ]

    if isinstance(doctypes, str) and not frappe.get_meta(doctypes).issingle:

        doctypes = [
            d
            for d in doctype_rules
            if d.get("document_type") == doctypes or d.get("parent_doctype") == doctypes
        ]

    queries = []
    for d in doctypes:
        doctype = d.get("document_type")
        parent_doctype = d.get("parent_doctype")
        Voucher = DocType(doctype)
        conditions = (
            (Voucher.party_master.isnull())
            if not party_master
            else (Voucher.party_master == party_master)
        )
        if parties:
            parties_list = [p.get("party") for p in parties]
            conditions &= Voucher[d.get("party_fieldname")].isin(parties_list)
        elif not parties:
            conditions &= Voucher[d.get("party_fieldname")].isnotnull()
        select = [
            Voucher.name,
            Voucher.docstatus,
            ConstantColumn(parent_doctype).as_("doctype"),
            Voucher[d.get("party_fieldname")].as_("party"),
            Voucher.party_master,
        ]
        if doctype == parent_doctype:
            select.append(Voucher.name.as_("voucher_no"))
        elif doctype != parent_doctype:
            select.append(Voucher.parent.as_("voucher_no"))

        if d.get("is_dynamic_party_type") == 1:
            select.append(Voucher[d.party_type_fieldname].as_("party_type"))
            queries.append((frappe.qb.from_(Voucher).select(*select).where(conditions)))
            continue
        select.append(Voucher[d.get("party_type")].as_("party_type"))
        queries.append((frappe.qb.from_(Voucher).select(*select).where(conditions)))

    if queries:
        final_query = queries[0]
        for q in queries[1:]:
            final_query = final_query.union_all(q)
        final_query = final_query.orderby("party", "doctype")
        return final_query.run(as_dict=True)


def get_roles_for_pm(party_master):
    """
    Get the roles for a given party master.
    Args:
        party_master (str or doc): The party master or its name.
    """
    if not party_master:
        return []

    if isinstance(party_master, str):
        party_master = frappe.get_cached_doc("Party Master", party_master)

    if not hasattr(party_master, "get"):
        return []

    roles = []
    # Add the primary role
    if getattr(party_master, "party_type", None):
        roles.append(
            {
                "parent": party_master.name,
                "party_type_role": party_master.party_type,
                "is_primary": 1,
            }
        )

    # Add other roles
    for r in party_master.get("roles", []):
        roles.append(
            {
                "parent": party_master.name,
                "party_type_role": r.party_type_role,
                "is_primary": 0,
            }
        )

    return roles


def get_party_master_parties_db(party_master, all_roles=True, roles=None):
    """
    Fetch parties linked to a Party Master from the database.
    If party_master is None or "All", fetches all parties linked to ANY party master.
    """
    fetch_all = party_master in (None, "All", "")

    if not fetch_all and isinstance(party_master, (list, tuple)):
        # Efficiently handle multiple party masters
        pm_roles = []
        seen_roles = set()
        for pm in party_master:
            for r in get_roles_for_pm(pm):
                role_name = r.get("party_type_role")
                if not all_roles and roles and role_name not in roles:
                    continue
                if role_name not in seen_roles:
                    pm_roles.append(role_name)
                    seen_roles.add(role_name)

        if not pm_roles:
            return []

        all_parties = []
        from uph.party.utils import get_party_type_currency_field

        for role_doctype in pm_roles:
            if not frappe.db.exists("DocType", role_doctype):
                continue

            currency_field = get_party_type_currency_field(role_doctype)
            fields = [
                "name as party",
                f"'{role_doctype}' as party_type",
                "party_master",
            ]
            if currency_field and frappe.get_meta(role_doctype).has_field(
                currency_field
            ):
                fields.append(f"{currency_field} as currency")

            filters = {}
            if not fetch_all:
                filters["party_master"] = ["in", party_master]
            else:
                filters["party_master"] = ["is", "set"]

            try:
                found = frappe.get_all(
                    role_doctype,
                    filters=filters,
                    fields=fields,
                )
                all_parties.extend(found)
            except Exception:
                pass
        return all_parties

    # Single party master or Fetch All
    if fetch_all:
        pm_roles = [{"party_type_role": pt} for pt in uph.get_party_type_list()]
    else:
        pm_roles = get_roles_for_pm(party_master)

    if not all_roles and roles:
        if isinstance(roles, str):
            roles = [roles]
        pm_roles = [r for r in pm_roles if r.get("party_type_role") in roles]

    if not pm_roles:
        return []

    parties = []
    from uph.party.utils import get_party_type_currency_field

    for role in pm_roles:
        role_doctype = role.get("party_type_role")
        if not frappe.db.exists("DocType", role_doctype):
            continue

        currency_field = get_party_type_currency_field(role_doctype)
        fields = ["name as party", f"'{role_doctype}' as party_type", "party_master"]
        if currency_field and frappe.get_meta(role_doctype).has_field(currency_field):
            fields.append(f"{currency_field} as currency")

        filters = {}
        if not fetch_all:
            filters["party_master"] = party_master
        else:
            filters["party_master"] = ["is", "set"]

        try:
            found = frappe.get_all(
                role_doctype,
                filters=filters,
                fields=fields,
            )
            for p in found:
                parties.append(p)
        except Exception:
            pass

    return parties


def _get_set_cached_pm_list(doctype, data=None):
    # Legacy function placeholder
    return None


def get_fields(doctype, fields):
    # Helper to get fields if they exist
    meta = frappe.get_meta(doctype)
    return [f for f in fields if meta.has_field(f) or f == "name"]


@frappe.whitelist()
def get_unlinked_party(filters, limit=None):
    if isinstance(filters, str):
        import json

        filters = json.loads(filters)

    # Logic to find parties of given type that have no party_master set
    party_type = filters.get("party_type")
    if not party_type:
        return []

    if isinstance(party_type, str):
        party_type = [party_type]

    results = []
    for pt in party_type:
        data = frappe.get_all(
            pt, filters={"party_master": ["is", "not set"]}, limit=limit or 20
        )
        for d in data:
            d["party_type"] = pt
            results.append(d)
    return results


@frappe.whitelist()
def get_linked_parties_list(party_master_filters=None, party_type=None):
    if not party_master_filters:
        return []

    if isinstance(party_master_filters, str):
        party_master_filters = [party_master_filters]

    results = []
    for pm in party_master_filters:
        res = get_party_master_parties(pm, party_type=party_type)
        if res:
            results.extend(res)
    return results


@frappe.whitelist()
def get_counts_of_unposted_or_cancelled_vouchers(
    company, party_master=None, is_party_gl_effected=1
):
    """
    Get counts of vouchers that are not posted or are cancelled.
    Returns a list of dicts with 'party_master' and other basic info.
    """
    from uph.party.controllers.cache_utils import (
        get_doctypes_functional_fields_mapping_as_dict,
    )

    mapping = get_doctypes_functional_fields_mapping_as_dict()
    results = []

    for dt, map_conf in mapping.items():
        if map_conf.get("document_type") != dt:
            continue

        party_fieldname = map_conf.get("party_fieldname")
        party_type = map_conf.get("party_type")

        filters = {"docstatus": ["in", [0, 2]], "company": company}
        if party_master:
            filters["party_master"] = party_master
        else:
            filters["party_master"] = ["is", "set"]

        fields = [
            "name",
            "doctype",
            "party_master",
            "docstatus",
            f"{party_fieldname} as party",
        ]
        if map_conf.get("is_dynamic_party_type"):
            fields.append(f"{map_conf.get('party_type_fieldname')} as party_type")

        try:
            res = frappe.get_all(dt, filters=filters, fields=fields)
            for r in res:
                if not map_conf.get("is_dynamic_party_type"):
                    r["party_type"] = party_type
                results.append(r)
        except Exception:
            pass

    return results


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_party_analytic_accounting_filtered(
    doctype, txt, searchfield, start, page_len, filters
):
    """
    Filter 'Party Analytic Accounting' by party_master.
    """
    pm = filters.get("party_master")
    if not pm:
        return []

    return frappe.db.get_all(
        "Party Analytic Accounting",
        filters={"party_master": pm, "name": ["like", f"%{txt}%"]},
        as_list=1,
    )


@frappe.whitelist()
def query_similar_name_or_number(party_name=None, party_number=None):
    """
    Check for existing Party Master with same or similar name/number.
    Returns dict with exact matches found.
    """
    from uph.party.utils import normalize_text

    res = {}
    if party_name:
        normalized = normalize_text(party_name)
        # Check exact name (case-insensitive via DB or normalized field)
        exact_name = frappe.db.get_value(
            "Party Master", {"party_name": party_name}, "name"
        )
        if not exact_name:
            exact_name = frappe.db.get_value(
                "Party Master", {"normalized_party_name": normalized}, "name"
            )

        if exact_name:
            res["exact_name"] = exact_name

    if party_number:
        exact_number = frappe.db.get_value(
            "Party Master", {"party_number": party_number}, "name"
        )
        if exact_number:
            res["exact_number"] = exact_number

    return res
