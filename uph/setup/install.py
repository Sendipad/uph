import frappe
from frappe import _
from uph.party.doctype.party_master_settings.party_master_settings import (
    setup_initial_document_types,
    setup_party_types_table,
)
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import make_dimension_in_accounting_doctypes

def full_setup():
    run_pending_setup()


def setup():
    setup_initial_document_types()
    setup_party_types_table()

def on_migrate():
    """Run after migrate"""
    run_pending_setup()


def run_pending_setup():
    """Run new setup safely for existing sites"""
    setup_initial_document_types()
    setup_party_types_table()
    create_party_master_tree()
    create_party_analytic_accounting_dimension()
def post_install():
    """Run at install time"""
    settings = frappe.get_doc("Party Master Settings")
    settings.flags.document_types_same = False
    if hasattr(settings, "sync_update_to_doctype_fields"):
        settings.sync_update_to_doctype_fields(force_update=True)
    settings.save()
    
    run_pending_setup()

def create_party_master_tree():
    tree_node = frappe.get_all("Party Master")
    if tree_node:
        return

    def create_node(name, number, is_group=1, parent=None, ptype=None):
        return frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": name,
                "party_number": number,
                "is_group": is_group,
                "parent_party_master": parent,
                "party_type": ptype,
            }
        ).insert(ignore_permissions=True)

    debitor = create_node(_("Debitor"), "1000")
    customer = create_node(_("Customer"), "1300", parent=debitor.name, ptype="Customer")
    create_node(_("Foreign Customer"), "1310", parent=customer.name, ptype="Customer")
    create_node(_("Local Customer"), "1320", parent=customer.name, ptype="Customer")

    creditor = create_node(_("Creditor"), "2000")
    supplier = create_node(_("Supplier"), "2100", parent=creditor.name, ptype="Supplier")
    create_node(_("Foreign Supplier"), "2110", parent=supplier.name, ptype="Supplier")
    create_node(_("Local Supplier"), "2120", parent=supplier.name, ptype="Supplier")


def create_party_analytic_accounting_dimension():
    if frappe.db.exists("Accounting Dimension", "Party Analytic Accounting"):
        doc = frappe.get_doc("Accounting Dimension", "Party Analytic Accounting")
        doc.disabled = 0
        doc.save()
        make_dimension_in_accounting_doctypes(doc)
    else:
        doc = frappe.get_doc({
            "doctype": "Accounting Dimension",
            "name": "Party Analytic Accounting",
            "document_type": "Party Analytic Accounting",
            "label": "Party Analytic Accounting",
            "fieldname": "party_analytic_accounting",
            "disabled": 0
        })
        doc.insert(ignore_permissions=True)
    
  
        
def full_setup():
    setup_initial_document_types()
    setup_party_types_table()
    create_party_master_tree()
    create_party_analytic_accounting_dimension()
