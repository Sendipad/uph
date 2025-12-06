import frappe
def before_uninstall():
    """Called before app uninstall to clean up safely"""
    
    # Step 1: Check if any Party Master links exist
    doctypes_with_pm = [
        "Customer", "Supplier", "Employee", 
        "Sales Invoice", "Purchase Invoice", "Payment Entry"
    ]
    
    has_data = False
    for dt in doctypes_with_pm:
        if frappe.db.count(dt, {"party_master": ["is", "set"]}):
            has_data = True
            break
    
    if has_data:
        frappe.throw("""
            Cannot uninstall UPH - Active Party Master links exist!
            
            Options:
            1. Run migration to unlink all parties first
            2. Use 'force_uninstall' flag (DANGEROUS - will orphan data)
        """)
    
    # Step 2: Remove custom fields gracefully
    remove_custom_fields()
def remove_custom_fields():
    """Remove custom fields added by UPH"""
    custom_fields = frappe.get_all(
        "Custom Field",
        filters={"module": "Unified Party Hub"},
        pluck="name"
    )
    
    for cf_name in custom_fields:
        # Set read_only and hidden instead of deleting
        frappe.db.set_value("Custom Field", cf_name, {
            "read_only": 1,
            "hidden": 1
        })
