import frappe
from frappe.utils.caching import redis_cache


def add_pm_doctypes(bootinfo):
    bootinfo.party_master_on_doctypes_depend_field = get_pm_doctypes()
    # bootinfo.party_master_depends_on_fields=get_party_master_depends_on_fields()


@frappe.whitelist()
@redis_cache()
def get_pm_doctypes():
    """
    SECURE: Using Frappe ORM instead of raw SQL.
    Returns list of enabled Party Master Settings DocTypes.
    """
    return frappe.get_all(
        "Party Master Settings DocType",
        filters={"enabled": 1, "parenttype": "Party Master Settings"},
        fields=["parent_doctype", "document_type", "party_fieldname"],
        as_list=True
    )


# return frappe.get_all('Party Master Settings DocType', filters={'enabled': 1}, pluck='parent_doctype')


@frappe.whitelist()
def get_party_master_depends_on_fields():
    """
    SECURE: Using Frappe ORM instead of raw SQL.
    Returns dict mapping doctypes to party fieldnames.
    """
    key = "UPH: get_party_master_depends_on_fields"
    
    if cached := frappe.cache.get_value(key):
        return cached
    
    fields = frappe.get_all(
        "Party Master Settings DocType",
        filters={"enabled": 1, "parenttype": "Party Master Settings"},
        fields=["parent_doctype", "party_fieldname"],
        as_list=True
    )
    
    if fields:
        party_fields = {f[0]: f[1] for f in fields}
        frappe.cache.set_value(key, party_fields, expires_in_sec=3600)
        return party_fields
    
    return {}
