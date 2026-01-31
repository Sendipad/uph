import frappe
from frappe import _
from uph.party.doctype.party_master_settings.party_master_settings import (
    setup_initial_document_types,
    setup_party_types_table,
)
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    make_dimension_in_accounting_doctypes,
)


def full_setup():
    """Run full setup for fresh install or substantial updates"""
    run_pending_setup()


def setup():
    """Legacy setup alias"""
    full_setup()


def on_migrate():
    """Run after migrate"""
    run_pending_setup()


def after_install():
    """Run at install time"""
    post_install()


def run_pending_setup():
    """Run new setup safely for existing sites"""
    setup_initial_document_types()
    setup_party_types_table()
    create_party_master_tree()
    create_party_analytic_accounting_dimension()


def post_install():
    """Run post-install configuration"""
    settings = frappe.get_doc("Party Master Settings")
    settings.flags.document_types_same = False
    if hasattr(settings, "sync_update_to_doctype_fields"):
        settings.sync_update_to_doctype_fields(force_update=True)
    settings.save()

    run_pending_setup()
