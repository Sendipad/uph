import frappe


def before_uninstall():
    """Called before app uninstall to clean up safely"""
    disable_accounting_dimension()
    remove_custom_fields()


def remove_custom_fields():
    """Remove custom fields specifically added by UPH"""
    # Safe list of fieldnames added by UPH
    uph_fields = [
        "party_master",
        "is_default_for_party_master",
        "party_analytic_accounting",
    ]

    for fieldname in uph_fields:
        # We perform a safer deletion by checking fieldname AND module if possible,
        # or just the specific fieldnames known to be unique to UPH's function
        fields = frappe.get_all(
            "Custom Field", filters={"fieldname": fieldname}, pluck="name"
        )
        for name in fields:
            frappe.delete_doc("Custom Field", name, ignore_missing=True)


def disable_accounting_dimension():
    """Disable Party Analytic Accounting dimension"""
    if frappe.db.exists("Accounting Dimension", "Party Analytic Accounting"):
        dim = frappe.get_doc("Accounting Dimension", "Party Analytic Accounting")
        dim.disabled = 1
        dim.save(ignore_permissions=True)
