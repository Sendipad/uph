import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field
from frappe.utils import cstr
from frappe import _
from uph.party.utils import get_transactional_doctype_list_to_add_pm,get_party_field_in_doctype
from uph.party.doctype.party_master_settings.party_master_settings import setup_initial_document_type,setup_party_master_mapping_fields
def after_install():
    setup_initial_document_type()
    setup_party_master_mapping_fields()
    
def post_install():
    settings = frappe.get_doc('Party Master Settings')
    settings.flags.document_types_same=False
    settings.sync_update_to_doctype_fields(force_update=True)
    settings.save()
