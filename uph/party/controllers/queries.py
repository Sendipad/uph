import uph
import frappe
from frappe.query_builder import Criterion, CustomFunction, DocType
from frappe.query_builder.functions import Locate, Coalesce, Count
from frappe.query_builder.custom import ConstantColumn
from frappe.utils import nowdate, unique, add_months
from pypika import Order
from frappe.utils.caching import redis_cache
from frappe import _


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def party_master_link_query(
    doctype, txt, searchfield, page_len, start, filters=None, reference_doctype=None
):
    party_type = filters.get("party_type") if filters else None
    top_parties = []
    document_type = frappe.get_all(
        "Party Master Settings DocType", pluck="document_type"
    )

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
        filters["party_master"] = [party_master]
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
    doctype_rules = frappe.get_doc("Party Master Settings").document_types

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
        party_master (str): The name of the party master.
    Returns:
        list: A list of roles associated with the party master.
    """
    if not party_master:
        return []

    # Check if roles are already cached
    key = uph.make_key("Party Master.roles")
    roles = frappe.cache.hget(key, party_master)
    if not roles:
        roles = _get_roles_for_pm(party_master)
        frappe.cache.hset(key, party_master, roles)
    return roles


@frappe.whitelist()
def get_party_master_parties_db(party_master, all_roles=False, roles=None):
    if not all_roles and not roles and isinstance(party_master, str):
        roles = get_roles_for_pm(party_master)
    if not roles:
        roles = uph.get_party_type_list()

    queries = []
    for r in roles:
        doctype = r[0] if isinstance(r, (tuple, list)) else r

        queries.append(build_fetch_parties_query(doctype, party_master))

    if queries:
        final_query = queries[0]
        for q in queries[1:]:
            final_query = final_query.union_all(q)  # Use union_all for UNION ALL

        final_query = (
            final_query.orderby("party_master")
            .orderby("party_type")
            .orderby("currency", order=frappe.qb.desc)
            .orderby("is_default", order=frappe.qb.desc)
        )

        return final_query.run(as_dict=True)


@redis_cache()
def get_mapped_party_to_party_master_dict():
    on_party_type = uph.get_party_type_list()
    quries = []
    for p in on_party_type:
        doctype = DocType(p)
        quries.append(
            frappe.qb.from_(doctype)
            .select(ConstantColumn(p), doctype.name, doctype.party_master)
            .where(doctype.party_master.isnotnull())
        )
    if quries:
        final_query = quries[0]
        for q in quries[1:]:
            final_query = final_query.union(q)
        data = final_query.run(as_dict=False)
        return {(t[0], t[1]): t[2] for t in data}


def get_mapped_party_to_party_master(on_party_type=None):
    if on_party_type and isinstance(on_party_type, str):
        on_party_type = [on_party_type]

    quries = []
    for p in on_party_type:
        doctype = DocType(p)
        quries.append(
            frappe.qb.from_(doctype)
            .select(doctype.name, doctype.party_master, ConstantColumn(p))
            .where(doctype.party_master.isnotnull())
        )
    if quries:
        final_query = quries[0]
        for q in quries[1:]:
            final_query = final_query.union(q)
        return final_query.run()


def get_unlinked_party(filters, limit=None):
    """
    Returns all parties without a set party master.
    When party_name is provided, orders by most similar party name across party types.
    Otherwise returns all results ordered by party name.
    Supports limiting results per party type when limit parameter is provided.
    """
    if not frappe.db.exists("Party Master Settings"):
        frappe.throw(_("Party Master Settings DocType does not exist!"))

    party_name = filters.get("party_name")
    if not party_name and filters.get("party_master"):
        party_name = frappe.get_doc("Party Master", filters.party_master).party_name

    party_types = filters.get("party_type") or filters.get("roles") or []
    if not party_types:
        party_types = frappe.get_cached_doc("Party Master Settings").party_types
        party_types = [p.party_type for p in party_types]

    queries = []

    for p in party_types:
        if not frappe.db.exists("DocType", p):
            continue

        Doctype = DocType(p)
        voucher_name_fieldname = f"{p.lower()}_name"

        fields = [
            Doctype.name.as_("party"),
            Doctype.party_master,
            ConstantColumn(p).as_("party_type"),
        ]

        meta = frappe.get_meta(p)

        # Get party name field
        if meta.has_field(voucher_name_fieldname):
            fields.append(getattr(Doctype, voucher_name_fieldname).as_("party_name"))
        elif meta.has_field("title"):
            fields.append(Doctype.title.as_("party_name"))
        elif meta.has_field("name"):
            fields.append(Doctype.name.as_("party_name"))
        else:
            fields.append(ConstantColumn("").as_("party_name"))

        # Currency fields
        if meta.has_field("default_currency"):
            fields.append(Doctype.default_currency.as_("currency"))
        elif meta.has_field("salary_currency"):
            fields.append(Doctype.salary_currency.as_("currency"))
        else:
            fields.append(ConstantColumn("").as_("currency"))

        base_condition = (Doctype.party_master.isnull()) | (Doctype.party_master == "")
        if not filters.disabled and meta.has_field("disabled"):
            base_condition = base_condition & (Doctype.disabled == 0)

        query = frappe.qb.from_(Doctype).select(*fields).where(base_condition)

        # Apply limit to each party type query if limit is provided
        if limit:
            query = query.limit(limit)

        queries.append(query)

    if not queries:
        return []

    # Build the final query
    final_query = queries[0]
    for q in queries[1:]:
        final_query = final_query.union_all(q)
    if limit:
        final_query.limit(limit)
    if party_name:
        words = [word.lower() for word in party_name.split() if word]
        if words:
            # Calculate similarity score in Python after getting results
            results = final_query.run(as_dict=True)

            # Add similarity score to each result
            for result in results:
                score = 0
                party_name_lower = (result.get("party_name") or "").lower()
                for word in words:
                    if word in party_name_lower:
                        score += 1
                result["similarity_score"] = score

            # Sort by similarity score (descending) then by party_name
            results.sort(key=lambda x: (-x["similarity_score"], x["party_name"] or ""))
            return results

    # Default ordering by party_name
    return final_query.orderby("party_name").run(as_dict=True)


def build_fetch_parties_query(doctype: str, party_master: str | list = None):
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
            (
                PartyType.is_default_for_party_master.as_("is_default")
                if meta.has_field("is_default_for_party_master")
                else ConstantColumn(0).as_("is_default")
            ),
        )
    elif doctype == "Supplier":
        query = query.select(
            PartyType.name.as_("party"),
            PartyType.supplier_name.as_("party_name"),
            PartyType.default_currency.as_("currency"),
            ConstantColumn(doctype).as_("party_type"),
            PartyType.party_master,
            (
                PartyType.is_default_for_party_master.as_("is_default")
                if meta.has_field("is_default_for_party_master")
                else ConstantColumn(0).as_("is_default")
            ),
        )
    elif doctype == "Employee":
        query = query.select(
            PartyType.name.as_("party"),
            PartyType.employee_name.as_("party_name"),
            PartyType.salary_currency.as_("currency"),
            ConstantColumn(doctype).as_("party_type"),
            PartyType.party_master,
            (
                PartyType.is_default_for_party_master.as_("is_default")
                if meta.has_field("is_default_for_party_master")
                else ConstantColumn(0).as_("is_default")
            ),
        )
    else:
        query = query.select(
            PartyType.name.as_("party"),
            (
                PartyType.title.as_("party_name")
                if meta.has_field("title")
                else ConstantColumn("").as_("party_name")
            ),
            ConstantColumn("").as_("currency"),
            ConstantColumn(doctype).as_("party_type"),
            PartyType.party_master,
            (
                PartyType.is_default_for_party_master.as_("is_default")
                if meta.has_field("is_default_for_party_master")
                else ConstantColumn(0).as_("is_default")
            ),
        )
    if party_master:
        if isinstance(party_master, str):
            query = query.where(PartyType.party_master == party_master)
        elif isinstance(party_master, list):
            query = query.where(PartyType.party_master.isin(party_master))
    else:
        query = query.where(
            PartyType.party_master.isnotnull() & (PartyType.party_master != "")
        )
    return query


@frappe.whitelist()
def get_linked_parties_list(party_master_filters: str | list = None, party_type=None):
    if party_type is None:
        party_type = uph.get_party_type_list()
        # party_type = frappe.get_all("Party Type", pluck="name",order_by="name ASC")
    if isinstance(party_type, str):
        party_type = [party_type]

    queries = []
    for pt in party_type:
        meta = frappe.get_meta(pt)
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
                (
                    PartyType.title.as_("party_name")
                    if meta.has_field("title")
                    else ConstantColumn("").as_("party_name")
                ),
                ConstantColumn("").as_("currency"),
                ConstantColumn(pt).as_("party_type"),
                PartyType.party_master,
            )

        # Apply filtering based on party_master_filters
        if party_master_filters is None:
            q = q.where(
                (PartyType.party_master.isnull()) | (PartyType.party_master == "")
            )
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
                    q = q.where(
                        (PartyType.party_master.isnull())
                        | (PartyType.party_master == "")
                    )

        queries.append(q)

    # Combine queries using UNION if multiple queries exist
    if queries:
        final_query = queries[0]
        for q in queries[1:]:
            final_query = final_query.union(q)

        return final_query.run(as_dict=True)

    return []


@frappe.whitelist()
def query_similar_name_or_number(party_name=None, party_number=None):
    if not party_name and not party_number:
        return {}
    if party_number and not party_name:
        if frappe.db.exists("Party Master", {"party_number": party_number}):
            return {"exact_number": 1}
        else:
            return {}
    result = None
    if party_name and not party_number:
        exact_name = frappe.db.exists("Party Master", {"party_name": party_name})
        if exact_name:
            result = {"exact_name": 1}

        names = party_name.split()
        name = "{0}{1}".format(names[0], " " + names[-1] if len(names) > 1 else "")
        similar = frappe.db.get_list(
            "Party Master",
            filters={"party_name": ["like", f"%{name}%"]},
            pluck="party_name",
            limit=5,
        )
        if similar:
            if result:
                result.update({"similar": similar})
        else:
            result = {"similar": similar}
    return result


def _get_set_cached_pm_list(reference_doctype, value=None):
    key = f"_pm_list-{reference_doctype}"
    if not value:
        return frappe.cache.get_value(key)
    frappe.cache.set_value(key, value, expires_in_sec=60)


def get_fields(doctype, fields=None):
    if fields is None:
        fields = []
    meta = frappe.get_meta(doctype)
    fields.extend(meta.get_search_fields())

    if meta.get("show_title_field_in_link") and meta.get("title_field"):
        fields.insert(1, meta.get("title_field"))

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
    roles = [frappe.get_value("Party Master", party_master, "party_type")]
    PartyMasterRole = DocType("Party Master Role")
    query = (
        frappe.qb.from_(PartyMasterRole)
        .select(PartyMasterRole.party_type_role)
        .where(PartyMasterRole.parent == party_master)
    ).run()
    if query:
        roles.extend(query)
    return roles


@frappe.whitelist()
def test(company):
    return get_counts_of_unposted_or_cancelled_vouchers(
        company, party_master=["132000012", "130100002"]
    )


@frappe.whitelist()
def get_counts_of_unposted_or_cancelled_vouchers(
    company, party_master=None, is_party_gl_effected=0
):
    import json

    if not company:
        return []

    db_type = frappe.db.db_type  # 'mariadb' or 'postgres'

    def quote(name):
        return f'"{name}"' if db_type == "postgres" else f"`{name}`"

    # Safely normalize party_master
    if not party_master:
        party_master = []
    elif isinstance(party_master, (str, int)):
        party_master = [str(party_master)]
    elif isinstance(party_master, str) and party_master.strip().startswith("["):
        try:
            party_master = json.loads(party_master)
        except Exception:
            party_master = [party_master]

    gl_voucher_type = get_party_master_settings_not_single_document_types_as_dict()

    gl_voucher_type_as_parent_child = {
        v["parent_doctype"]: v["document_type"]
        for v in gl_voucher_type.values()
        if v.get("parent_doctype") and v.get("document_type")
    }

    if is_party_gl_effected:
        gl_voucher_type_as_parent_child = {
            v["parent_doctype"]: v["document_type"]
            for v in gl_voucher_type.values()
            if v.get("is_party_gl_effected") == 1
        }

    all_queries = []
    all_values = []

    if party_master:
        placeholder_string = ", ".join(["%s"] * len(party_master))
        party_filter = f"AND party_master IN ({placeholder_string})"
    else:
        party_filter = "AND party_master IS NOT NULL"

    for parent, child in gl_voucher_type_as_parent_child.items():
        is_parent = parent == child
        parent_table = quote(f"tab{parent}")
        child_table = quote(f"tab{child}")

        if is_parent:
            query = f"""
                SELECT
                    party_master,
                    '{parent}' AS doctype,
                    SUM(IF(docstatus = 0, 1, 0)) AS draft_count,
                    SUM(IF(docstatus = 2 AND name NOT IN (
                        SELECT amended_from FROM {parent_table} WHERE amended_from IS NOT NULL
                    ), 1, 0)) AS cancelled_count
                FROM {parent_table}
                WHERE company = %s {party_filter}
                GROUP BY party_master
                HAVING draft_count > 0 OR cancelled_count > 0
            """
            all_queries.append(query)
            all_values.append([company] + party_master)

        else:
            query = f"""
                SELECT
                    child.party_master,
                    '{parent}' AS doctype,
                    SUM(IF(parent.docstatus = 0, 1, 0)) AS draft_count,
                    SUM(IF(parent.docstatus = 2 AND parent.name NOT IN (
                        SELECT amended_from FROM {parent_table} WHERE amended_from IS NOT NULL
                    ), 1, 0)) AS cancelled_count
                FROM {child_table} AS child
                JOIN {parent_table} AS parent ON parent.name = child.parent
                WHERE parent.company = %s {party_filter}
                GROUP BY child.party_master
                HAVING draft_count > 0 OR cancelled_count > 0
            """
            all_queries.append(query)
            all_values.append([company] + party_master)

    union_query = "\nUNION ALL\n".join(all_queries)

    # FIX: prevent empty SQL execution
    if not union_query or not union_query.strip():
        return []

    flattened_values = []
    for vals in all_values:
        flattened_values.extend(vals)

    result = frappe.db.sql(union_query, flattened_values, as_dict=True)
    return result

#starting implementation of party analytic accounting query, it must be improved in future
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_party_analytic_accounting_filtered(doctype, txt, searchfield, start, page_len, filters, reference_doctype=None):
    from frappe.utils import nowdate

    party_master = filters.get("party_master")
    party = filters.get("party")
    company = filters.get("company")
    
    if not party_master:
        return []

    conditions = ["enabled = 1"]
    if party_master:
        conditions.append("party_master = %(party_master)s")
    if txt:
        conditions.append("analytic_name LIKE %(txt)s")
    
    today = nowdate()
    conditions.append("(effective_from IS NULL OR effective_from <= %(today)s)")
    conditions.append("(effective_to IS NULL OR effective_to >= %(today)s)")

    query = f"""
        SELECT name, analytic_name
        FROM `tabParty Analytic Accounting`
        WHERE {" AND ".join(conditions)}
        LIMIT {start}, {page_len}
    """

    values = {
        "party_master": party_master,
        "txt": f"%{txt}%",
        "today": today
    }

    paa_records = frappe.db.sql(query, values, as_dict=True)

    results = []
    for paa in paa_records:
        party_linked = frappe.db.exists({
            "doctype": "Party Analytic Accounting Party",
            "parent": paa.name,
            "parenttype": "Party Analytic Accounting",
            "parentfield": "parties",
            "party": party
        }) if party else True

        company_linked = frappe.db.exists({
            "doctype": "Party Analytic Accounting Allowed Company",
            "parent": paa.name,
            "parenttype": "Party Analytic Accounting",
            "parentfield": "companies",
            "company": company
        }) if company else True

        if party_linked and company_linked:
            # tuple: (value, label, optional description)
            results.append((paa.name, paa.analytic_name, paa.analytic_name))

    return results

@frappe.whitelist()
def make_warning_for_not_submitted_voucher(party_master, as_count=False):
    # Get document type configurations
    gl_voucher_type = get_party_master_settings_not_single_document_types_as_dict()

    # Set of doctypes where GL effect is enabled
    gl_effected_voucher = {
        k.get("parent_doctype")
        for k in gl_voucher_type.values()
        if k.get("is_party_gl_effected") == 1
    }

    # Get all draft and cancelled-but-not-amended documents for the party master
    documents = _get_draft_and_cancelled_not_amended_documents(party_master)

    result = {}

    for d in documents:
        party = d["party_master"]
        doctype = d["doctype"]

        if party not in result:
            result[party] = {"is_party_gl_effected": {}, "rest_voucher": {}}

        group = (
            "is_party_gl_effected" if doctype in gl_effected_voucher else "rest_voucher"
        )

        if as_count:
            result[party][group][doctype] = result[party][group].get(doctype, 0) + 1
        else:
            result[party][group].setdefault(doctype, []).append(d["name"])

    return result


@frappe.whitelist()
def _get_draft_and_cancelled_not_amended_documents(
    party_master, company=None, period=None
):
    documents = get_party_master_settings_not_single_document_types_as_dict()

    document_types = {
        key: doc for key, doc in documents.items() if key == doc.get("document_type")
    }

    queries = []
    params = []

    is_filtering = bool(party_master)
    party_master = (
        [party_master] if isinstance(party_master, str) else party_master or []
    )

    for doctype, meta in document_types.items():
        is_child = doctype != meta.get("parent_doctype")
        parent_doctype = meta.get("parent_doctype")
        table = f"`tab{doctype}`"
        parent_table = f"`tab{parent_doctype}`"
        docname = "name" if not is_child else "parent as name"

        # Amendment filtering
        if not is_child:
            amended_filter = f"""
                AND name NOT IN (
                    SELECT amended_from FROM {table} WHERE amended_from IS NOT NULL
                )
            """
        else:
            amended_filter = f"""
                AND parent NOT IN (
                    SELECT amended_from FROM {parent_table} WHERE amended_from IS NOT NULL
                    )
            """

        # Party filter
        if is_filtering:
            placeholders = ", ".join(["%s"] * len(party_master))
            party_filter = f"AND party_master IN ({placeholders})"
            local_params = party_master
        else:
            party_filter = "AND party_master IS NOT NULL"
            local_params = []

        query = f"""
            SELECT {docname}, docstatus, party_master, '{parent_doctype}' AS doctype
            FROM {table}
            WHERE (
                {("docstatus = 0 OR (docstatus = 2 " + amended_filter + ")")}
            )
            {party_filter}
        """
        queries.append(query)
        params.extend(local_params)

    if not queries:
        return []

    full_query = " UNION ALL ".join(queries) + " ORDER BY party_master, doctype"
    return frappe.db.sql(full_query, params, as_dict=True)


def get_party_master_settings_not_single_document_types_as_dict():
    key = uph.make_key("Party Master Settings.document_types")
    result = frappe.cache.hget(key, "not_single_as_dict")
    if result:
        return result

    result = {}
    document_types = frappe.get_all(
        "Party Master Settings DocType",
        filters={"parent": "Party Master Settings"},
        fields=[
            "document_type",
            "parent_doctype",
            "enabled",
            "document_categories",
            "reqd",
            "is_dynamic_party_type",
            "party_fieldname",
            "party_type",
            "party_master_custom_field",
            "is_party_gl_effected",
        ],
    )

    for d in document_types:
        meta = frappe.get_meta(d.get("parent_doctype"))
        same = d.get("document_type") == d.get("parent_doctype")
        if not meta.issingle:
            result[d["document_type"]] = d
            if not same:
                result[d["parent_doctype"]] = d

    frappe.cache.hset(key, "not_single_as_dict", result)
    return result
