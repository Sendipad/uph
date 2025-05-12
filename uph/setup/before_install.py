import frappe
from uph.party.doctype.party_master_settings.party_master_settings import (
    setup_initial_document_types,
    setup_party_types_table,
)


def setup():
    setup_initial_document_types()
    setup_party_types_table()


def post_install():
    settings = frappe.get_doc("Party Master Settings")
    settings.flags.document_types_same = False
    settings.sync_update_to_doctype_fields(force_update=True)
    settings.save()
