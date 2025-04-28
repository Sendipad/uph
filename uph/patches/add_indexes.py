import frappe

def execute():
    # Index for Customer
    frappe.db.sql("ALTER TABLE `tabCustomer` ADD INDEX idx_party_master_currency (party_master, default_currency)")
    
    # Index for Supplier
    frappe.db.sql("ALTER TABLE `tabSupplier` ADD INDEX idx_party_master_currency (party_master, default_currency)")

    frappe.db.sql("ALTER TABLE `tabEmployee` ADD INDEX idx_party_master_currency (party_master, salary_currency)")