import frappe
from uph.party.controllers.cache_utils import get_pm_doctypes
from uph.party.controllers.cache_utils import get_party_master_depends_on_fields


def add_pm_doctypes(bootinfo):
    bootinfo.party_master_on_doctypes_depend_field = get_pm_doctypes()
    # bootinfo.party_master_depends_on_fields=get_party_master_depends_on_fields()
