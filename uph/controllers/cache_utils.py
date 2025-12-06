"""
Cache utilities for UPH
Provides centralized caching for Party Master Settings configuration
"""
import frappe

# Cache key constants
CACHE_KEY_CONFIGURED_DOCTYPES = "uph:configured_doctypes"
CACHE_KEY_PARTY_TYPES = "uph:configured_party_types"
CACHE_TTL = 3600  # 1 hour


def get_configured_doctypes():
    """
    Get the set of document types configured in Party Master Settings.
    Uses Redis cache with 1-hour TTL for performance.
    
    Returns:
        set: Set of document type names that have party_master field configured
    """
    cache = frappe.cache()
    
    # Try to get from cache first
    cached_value = cache.get_value(CACHE_KEY_CONFIGURED_DOCTYPES)
    if cached_value is not None:
        return set(cached_value) if cached_value else set()
    
    # Cache miss - fetch from database
    try:
        settings = frappe.get_cached_doc("Party Master Settings", "Party Master Settings")
        # Get all document types from settings
        doctypes = {d.document_type for d in settings.document_types if d.document_type}
        
        # Store in cache as list (sets aren't JSON serializable)
        cache.set_value(CACHE_KEY_CONFIGURED_DOCTYPES, list(doctypes), expires_in_sec=CACHE_TTL)
        
        return doctypes
    except Exception as e:
        frappe.log_error(f"Error fetching configured doctypes: {str(e)}", "UPH Cache Error")
        return set()


def get_configured_party_types():
    """
    Get the set of party types configured in Party Master Settings.
    Uses Redis cache with 1-hour TTL for performance.
    
    Returns:
        set: Set of party type names (Customer, Supplier, Employee, etc.)
    """
    cache = frappe.cache()
    
    # Try to get from cache first
    cached_value = cache.get_value(CACHE_KEY_PARTY_TYPES)
    if cached_value is not None:
        return set(cached_value) if cached_value else set()
    
    # Cache miss - fetch from database
    try:
        settings = frappe.get_cached_doc("Party Master Settings", "Party Master Settings")
        # Get all party types from settings
        party_types = {d.party_type for d in settings.party_types if d.party_type}
        
        # Store in cache as list
        cache.set_value(CACHE_KEY_PARTY_TYPES, list(party_types), expires_in_sec=CACHE_TTL)
        
        return party_types
    except Exception as e:
        frappe.log_error(f"Error fetching configured party types: {str(e)}", "UPH Cache Error")
        return set()


def clear_settings_cache():
    """
    Clear all UPH settings caches.
    Should be called when Party Master Settings is updated.
    """
    cache = frappe.cache()
    cache.delete_value(CACHE_KEY_CONFIGURED_DOCTYPES)
    cache.delete_value(CACHE_KEY_PARTY_TYPES)
    
    # Also clear the frappe.get_cached_doc cache for Party Master Settings
    frappe.clear_document_cache("Party Master Settings", "Party Master Settings")


def is_configured_doctype(doctype):
    """
    Fast check if a doctype is configured in Party Master Settings.
    Uses cached set for O(1) lookup.
    
    Args:
        doctype (str): DocType name to check
        
    Returns:
        bool: True if doctype is configured for party_master validation
    """
    return doctype in get_configured_doctypes()


def is_configured_party_type(party_type):
    """
    Fast check if a party type is configured in Party Master Settings.
    Uses cached set for O(1) lookup.
    
    Args:
        party_type (str): Party Type name to check
        
    Returns:
        bool: True if party type is configured
    """
    return party_type in get_configured_party_types()
