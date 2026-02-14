import frappe
from uph.party.controllers.cache_utils import get_pm_doctypes
from uph.party.controllers.cache_utils import get_party_master_depends_on_fields


def add_pm_doctypes(bootinfo):
    bootinfo.party_master_on_doctypes_depend_field = get_pm_doctypes()
    # bootinfo.party_master_depends_on_fields=get_party_master_depends_on_fields()

    # Setup Wizard Check
    try:
        setup_finished = frappe.db.get_single_value(
            "Party Master Settings", "setup_finished"
        )
        bootinfo.uph_setup_needed = not setup_finished
        # print(f"DEBUG: Setup Finished: {setup_finished}, Flag: {bootinfo.uph_setup_needed}")
    except Exception as e:
        # print(f"DEBUG: Boot Error: {e}")
        bootinfo.uph_setup_needed = False
