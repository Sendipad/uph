import frappe
def before_uninstall():
    """Called before app uninstall to clean up safely"""
    disable_accounting_dimension()
    remove_custom_fields()

def remove_custom_fields():
    """Remove custom fields added by UPH"""
    fields_to_remove = frappe.get_all("Custom Field", filters={"fieldname": "party_master", "options": "Party Master", "fieldtype": "Link"}, pluck="name")
    fields_to_remove += frappe.get_all("Custom Field", filters={"fieldname": "is_default_for_party_master"}, pluck="name")
    fields_to_remove += frappe.get_all("Custom Field", filters={"fieldname": "party_analytic_accounting", "options": "Party Analytic Accounting", "fieldtype": "Link"}, pluck="name")
    
    for field_name in fields_to_remove:
        frappe.delete_doc("Custom Field", field_name, ignore_missing=True)
        
    # Also attempt to delete by module if any remain with different names but in our module
    module_fields = frappe.get_all("Custom Field", filters={"module": "party"}, pluck="name")
    for field_name in module_fields:
        frappe.delete_doc("Custom Field", field_name, ignore_missing=True)

def disable_accounting_dimension():
    """Disable Party Analytic Accounting dimension"""
    if frappe.db.exists("Accounting Dimension", "Party Analytic Accounting"):
        dim=frappe.get_doc("Accounting Dimension", "Party Analytic Accounting")
        dim.disabled=1
        dim.save(ignore_permissions=True)

