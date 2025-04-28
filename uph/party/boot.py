import frappe 
from frappe.utils.caching import redis_cache


def add_pm_doctypes(bootinfo):
	bootinfo.party_master_on_doctypes_depend_field = get_pm_doctypes()
	#bootinfo.party_master_depends_on_fields=get_party_master_depends_on_fields()
 
@frappe.whitelist()
@redis_cache()
def get_pm_doctypes():
    return frappe.db.sql('Select parent_doctype,document_type,party_fieldname from `tabParty Master Settings DocType` where enabled=1 and parenttype="Party Master Settings"',as_list=1)
	#return frappe.get_all('Party Master Settings DocType', filters={'enabled': 1}, pluck='parent_doctype')

@frappe.whitelist()
def get_party_master_depends_on_fields():
    key='UPH: get_party_master_depends_on_fields'
    party_fields=frappe.cache.get_value(key)
    if party_fields:
        return party_fields
    fields=frappe.db.sql('Select parent_doctype,party_fieldname from `tabParty Master Settings DocType` where enabled=1 and parenttype="Party Master Settings"',as_list=1)
    if fields:
        party_fields={f[0]:f[1] for f in fields}
        frappe.cache.set_value(key,party_fields)
    return party_fields
		
