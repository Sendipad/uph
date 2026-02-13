# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

"""
Unlinked Party Resolver

Detects ERPNext role records (Customer, Supplier, Employee, etc.) that are
not linked to a Party Master. Provides suggestion-based linking and
paginated queries for the Data Quality Dashboard.
"""

import frappe
from frappe import _
from frappe.utils import cint


@frappe.whitelist()
def get_unlinked_parties(limit: int = 20, offset: int = 0, role_doctype: str = None):
    """
    Find ERPNext role records where party_master is NULL or empty.

    Returns paginated results grouped by role DocType with total count.
    Uses Redis cache for the total count (5-min TTL).
    """
    limit = cint(limit) or 20
    offset = cint(offset) or 0

    party_types = _get_configured_party_types()
    if not party_types:
        return {"unlinked": [], "total": 0}

    if role_doctype and role_doctype not in party_types:
        frappe.throw(_("Invalid role DocType: {0}").format(role_doctype))

    types_to_scan = [role_doctype] if role_doctype else party_types

    results = []
    total = 0

    for dt in types_to_scan:
        if not frappe.db.exists("DocType", dt):
            continue

        meta = frappe.get_meta(dt)
        if not meta.has_field("party_master"):
            continue

        table = frappe.qb.DocType(dt)

        # Count
        count_q = (
            frappe.qb.from_(table)
            .select(frappe.query_builder.functions.Count("*").as_("cnt"))
            .where((table.party_master.isnull()) | (table.party_master == ""))
        )
        count_result = count_q.run(as_dict=True)
        dt_count = count_result[0]["cnt"] if count_result else 0
        total += dt_count

    # Now fetch actual records across all types with offset/limit
    all_unlinked = []
    for dt in types_to_scan:
        if not frappe.db.exists("DocType", dt):
            continue

        meta = frappe.get_meta(dt)
        if not meta.has_field("party_master"):
            continue

        # Build fields list
        fields = ["name"]
        name_field = None
        for candidate in [
            f"{dt.lower().replace(' ', '_')}_name",
            "employee_name",
            "customer_name",
            "supplier_name",
        ]:
            if meta.has_field(candidate):
                name_field = candidate
                break

        if name_field:
            fields.append(name_field)

        # Add currency if available
        if meta.has_field("default_currency"):
            fields.append("default_currency")

        records = frappe.get_all(
            dt,
            filters={"party_master": ["in", [None, ""]]},
            fields=fields,
            order_by="name asc",
            limit_page_length=0,
        )

        for r in records:
            all_unlinked.append(
                {
                    "role_doctype": dt,
                    "role_name": r.name,
                    "display_name": r.get(name_field, r.name) if name_field else r.name,
                    "currency": r.get("default_currency", ""),
                }
            )

    # Sort and paginate
    all_unlinked.sort(key=lambda x: (x["role_doctype"], x["role_name"]))
    paginated = all_unlinked[offset : offset + limit]

    return {"unlinked": paginated, "total": total}


@frappe.whitelist()
def get_unlinked_suggestions(role_doctype: str, role_name: str, limit: int = 5):
    """
    Suggest Party Masters that might match an unlinked role record.
    Uses normalized name similarity.
    """
    if not frappe.db.exists(role_doctype, role_name):
        frappe.throw(_("{0} {1} does not exist").format(role_doctype, role_name))

    # Get the display name of the role record
    meta = frappe.get_meta(role_doctype)
    name_field = None
    for candidate in [
        f"{role_doctype.lower().replace(' ', '_')}_name",
        "employee_name",
        "customer_name",
        "supplier_name",
    ]:
        if meta.has_field(candidate):
            name_field = candidate
            break

    display_name = role_name
    if name_field:
        display_name = (
            frappe.db.get_value(role_doctype, role_name, name_field) or role_name
        )

    # Normalize
    from uph.party.controllers.normalization import NormalizationUtils

    normalized_input = NormalizationUtils.normalize_party_name(display_name)

    if not normalized_input:
        return {"suggestions": []}

    try:
        from rapidfuzz import fuzz, process
    except ImportError:
        return {"suggestions": []}

    # Get leaf Party Masters
    parties = frappe.get_all(
        "Party Master",
        filters={"is_group": 0, "disabled": 0},
        fields=[
            "name",
            "party_name",
            "party_type",
            "party_number",
            "normalized_party_name",
        ],
        limit_page_length=0,
    )

    if not parties:
        return {"suggestions": []}

    # Build choices
    choices = []
    choice_map = {}
    for p in parties:
        norm = p.normalized_party_name or NormalizationUtils.normalize_party_name(
            p.party_name or ""
        )
        if norm:
            choices.append(norm)
            choice_map[norm] = p

    if not choices:
        return {"suggestions": []}

    # Find top matches
    matches = process.extract(
        normalized_input, choices, scorer=fuzz.ratio, limit=cint(limit) or 5
    )

    suggestions = []
    for match_text, score, _idx in matches:
        if score < 50:
            continue
        p = choice_map.get(match_text)
        if p:
            suggestions.append(
                {
                    "party_master": p.name,
                    "party_name": p.party_name,
                    "party_type": p.party_type,
                    "party_number": p.party_number,
                    "score": round(score, 1),
                }
            )

    return {"suggestions": suggestions}


@frappe.whitelist()
def link_to_party_master(role_doctype: str, role_name: str, party_master: str):
    """
    Link an unlinked role record to a Party Master.
    Validates the Party Master is appropriate for the role.
    """
    if not frappe.has_permission(role_doctype, "write"):
        frappe.throw(_("Insufficient permissions"), frappe.PermissionError)

    if not frappe.db.exists(role_doctype, role_name):
        frappe.throw(_("{0} {1} does not exist").format(role_doctype, role_name))

    if not frappe.db.exists("Party Master", party_master):
        frappe.throw(_("Party Master {0} does not exist").format(party_master))

    # Validate the Party Master is valid for this role
    from uph.party.controllers.party import is_valide_party_master_to_party

    if not is_valide_party_master_to_party(party_master, role_doctype):
        frappe.throw(
            _(
                "Party Master {0} is not valid for {1} (may be a group, disabled, or missing the role)"
            ).format(party_master, role_doctype)
        )

    # Update the role record
    doc = frappe.get_doc(role_doctype, role_name)
    doc.party_master = party_master
    doc.save()

    # Invalidate cache
    frappe.cache.delete_value("uph:dashboard_stats")

    return {
        "success": True,
        "message": _("{0} {1} linked to Party Master {2}").format(
            role_doctype, role_name, party_master
        ),
    }


def get_unlinked_count():
    """Get total count of unlinked role records. Used by dashboard stats."""
    cache_key = "uph:unlinked_count"
    if cached := frappe.cache.get_value(cache_key):
        return cached

    party_types = _get_configured_party_types()
    total = 0

    for dt in party_types:
        if not frappe.db.exists("DocType", dt):
            continue
        meta = frappe.get_meta(dt)
        if not meta.has_field("party_master"):
            continue

        total += frappe.db.count(dt, {"party_master": ["in", [None, ""]]})

    frappe.cache.set_value(cache_key, total, expires_in_sec=300)
    return total


def rebuild_unlinked_cache():
    """Scheduled job: refresh the unlinked count cache."""
    frappe.cache.delete_value("uph:unlinked_count")
    get_unlinked_count()
    frappe.logger("uph").info("Unlinked party count cache rebuilt")


def _get_configured_party_types():
    """
    Get the list of party types configured in Party Master Settings.
    Falls back to default set if none configured.
    """
    from uph.party.controllers.cache_utils import SmartCache

    types = SmartCache.get_party_type_list()
    if types:
        return types
    return ["Customer", "Supplier", "Employee"]
