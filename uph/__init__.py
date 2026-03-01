import frappe
from uph.party.controllers.queries import (
    get_linked_parties_list,
    get_leaf_party_master_list_from_any_node,
)
from uph.party.controllers.cache_utils import SmartCache

__version__ = "3.3.0"


# ----------------------------------------------------------------------------
# Specific Accessors (Redirect to SmartCache)
# ----------------------------------------------------------------------------


def get_party_type_list():
    return SmartCache.get_party_type_list()


def get_cached_party_master_parties(party_master, party_type=None):
    parties = SmartCache.get_party_master_parties(party_master)
    if party_type:
        return [p for p in parties if p.get("party_type") == party_type]
    return parties or []


def update_cached_party_master_parties(party_master):
    SmartCache.update_party_master_parties(party_master)


def update_cached_party_to_pm_data(
    party_type, party, new_party_master=None, old_party_master=None
):
    SmartCache.update_party_to_pm_data(
        party_type, party, new_party_master, old_party_master
    )


def get_pm_parties_key():
    return SmartCache.make_key("PartyMaster", "List_Parties")


def get_party_to_pm_key(party_type):
    return SmartCache.make_key("PartyToPartyMaster", party_type)


def get_cached_party_to_pm_map(party_type, party):
    return SmartCache.get_party_to_pm_map(party_type, party)
