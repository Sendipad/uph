"""
Cache utilities for UPH
Provides centralized caching for Party Master Settings configuration
"""

import frappe
from frappe.utils.caching import redis_cache

# Cache key constants
CACHE_KEY_CONFIGURED_DOCTYPES = "uph:configured_doctypes"
CACHE_KEY_PARTY_TYPES = "uph:configured_party_types"
CACHE_KEY_PM_DOCTYPES = "uph:pm_doctypes_list"
CACHE_KEY_DEPENDS_ON = "uph:depends_on_fields"
CACHE_KEY_FUNCTIONAL_MAPPING = "uph:functional_mapping"
CACHE_TTL = 3600  # 1 hour


def clear_all_caches():
    """
    Clear all UPH settings caches.
    Should be called when Party Master Settings is updated.
    """
    cache = frappe.cache()

    # 1. Clear Settings-based caches
    keys = [
        CACHE_KEY_CONFIGURED_DOCTYPES,
        CACHE_KEY_PARTY_TYPES,
        CACHE_KEY_PM_DOCTYPES,
        CACHE_KEY_DEPENDS_ON,
        CACHE_KEY_FUNCTIONAL_MAPPING,
        "uph_PartyTypeListName",  # From uph.__init__
    ]
    for key in keys:
        cache.delete_value(key)

    # 2. Clear Hash Maps (Pattern based deletion or known keys)
    # Ideally we should use delete_keys if we had a pattern, but here we explicitly clear known hash maps
    from uph import UPH_cached_key_map

    for key_name, hash_key in UPH_cached_key_map.items():
        cache.delete_value(hash_key)

    # 3. Clear Document Cache
    frappe.clear_document_cache("Party Master Settings", "Party Master Settings")


def get_configured_doctypes():
    """
    Get the set of document types configured in Party Master Settings.
    Uses Redis cache with 1-hour TTL for performance.
    """
    cache = frappe.cache()
    cached_value = cache.get_value(CACHE_KEY_CONFIGURED_DOCTYPES)
    if cached_value is not None:
        return set(cached_value) if cached_value else set()

    try:
        settings = frappe.get_cached_doc(
            "Party Master Settings", "Party Master Settings"
        )
        doctypes = {d.document_type for d in settings.document_types if d.document_type}
        cache.set_value(
            CACHE_KEY_CONFIGURED_DOCTYPES, list(doctypes), expires_in_sec=CACHE_TTL
        )
        return doctypes
    except Exception as e:
        frappe.log_error(
            f"Error fetching configured doctypes: {str(e)}", "UPH Cache Error"
        )
        return set()


def get_configured_party_types():
    """Get the set of party types configured in Party Master Settings."""
    cache = frappe.cache()
    cached_value = cache.get_value(CACHE_KEY_PARTY_TYPES)
    if cached_value is not None:
        return set(cached_value) if cached_value else set()

    try:
        settings = frappe.get_cached_doc(
            "Party Master Settings", "Party Master Settings"
        )
        party_types = {d.party_type for d in settings.party_types if d.party_type}
        cache.set_value(
            CACHE_KEY_PARTY_TYPES, list(party_types), expires_in_sec=CACHE_TTL
        )
        return party_types
    except Exception as e:
        frappe.log_error(
            f"Error fetching configured party types: {str(e)}", "UPH Cache Error"
        )
        return set()


def is_configured_doctype(doctype):
    """Fast check if a doctype is configured."""
    return doctype in get_configured_doctypes()


def is_configured_party_type(party_type):
    """Fast check if a party type is configured."""
    return party_type in get_configured_party_types()


# ============================================================================
# Logic Moved from party.py and boot.py
# ============================================================================


def get_pm_doctypes():
    """
    Returns list of enabled Party Master Settings DocTypes.
    Previously in uph/party/boot.py
    """
    cache = frappe.cache()
    cached_value = cache.get_value(CACHE_KEY_PM_DOCTYPES)
    if cached_value is not None:
        return cached_value

    data = frappe.get_all(
        "Party Master Settings DocType",
        filters={"enabled": 1, "parenttype": "Party Master Settings"},
        fields=["parent_doctype", "document_type", "party_fieldname"],
        as_list=True,
    )
    cache.set_value(CACHE_KEY_PM_DOCTYPES, data, expires_in_sec=CACHE_TTL)
    return data


def get_party_master_depends_on_fields():
    """
    Returns dict mapping doctypes to party fieldnames.
    Previously in uph/party/boot.py
    """
    cache = frappe.cache()
    cached_value = cache.get_value(CACHE_KEY_DEPENDS_ON)
    if cached_value is not None:
        return cached_value

    fields = frappe.get_all(
        "Party Master Settings DocType",
        filters={"enabled": 1, "parenttype": "Party Master Settings"},
        fields=["parent_doctype", "party_fieldname"],
        as_list=True,
    )

    result = {f[0]: f[1] for f in fields} if fields else {}
    cache.set_value(CACHE_KEY_DEPENDS_ON, result, expires_in_sec=CACHE_TTL)
    return result


def get_doctypes_functional_fields_mapping_as_dict():
    """
    Returns mapping of doctypes to their Party Master Settings.
    Previously in uph/controllers/party.py
    """
    cache = frappe.cache()
    cached_value = cache.get_value(CACHE_KEY_FUNCTIONAL_MAPPING)
    if cached_value is not None:
        return cached_value

    doctypes = frappe.db.get_all(
        "Party Master Settings DocType",
        filters={"parenttype": "Party Master Settings"},
        fields=[
            "document_type",
            "parent_doctype",
            "is_dynamic_party_type",
            "reqd",
            "party_fieldname",
            "party_type_fieldname",
            "party_type",
        ],
    )
    docs = {}
    for d in doctypes:
        doctype = d.get("parent_doctype")
        document_type = d.get("document_type")

        # We need to check metadata, might be slow so caching is essential
        try:
            meta = frappe.get_meta(doctype)
            if not meta.issingle:
                docs.update({doctype: d})
                if doctype != document_type:
                    docs.update({document_type: d})
        except Exception:
            # If doctype keeps failing (e.g. deleted), skip it
            pass

    cache.set_value(CACHE_KEY_FUNCTIONAL_MAPPING, docs, expires_in_sec=CACHE_TTL)
    return docs
