import frappe
from frappe import _
from uph.party.doctype.party_master_settings.party_master_settings import (
    setup_initial_document_types,
    setup_party_types_table,
)


def setup():
    setup_initial_document_types()
    setup_party_types_table()
    create_party_master_tree()


def post_install():
    settings = frappe.get_doc("Party Master Settings")
    settings.flags.document_types_same = False
    settings.sync_update_to_doctype_fields(force_update=True)
    settings.save()


def create_party_master_tree():
    tree_node = frappe.get_all("Party Master")
    if tree_node or len(tree_node) > 0:
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
    supplier = create_node(
        _("Supplier"), "2100", parent=creditor.name, ptype="Supplier"
    )
    create_node(_("Foreign Supplier"), "2110", parent=supplier.name, ptype="Supplier")
    create_node(_("Local Supplier"), "2120", parent=supplier.name, ptype="Supplier")
