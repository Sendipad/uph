import frappe
from uph.party.controllers.queries import get_linked_parties_list
from uph.party.controllers.queries import get_leaf_party_master_list_from_any_node

__version__ = "2.2.2"


UPH_cached_key_map = {
    # Hash Key to get linked_parties list for Party Master Ordered by primary role and is_default
    "parties": "UPH_hash:PartyMaster|List_Parties",  # Hash Key to get linked_parties list for Party Master Ordered by primary role and is_default Ordered by primary role and is_default
    "get_parties": "UPH_hash:PartyMaster|List_Parties",  # Hash Key to get linked_parties list for Party Master Ordered by primary role and is_default
    "get_party_master_parties": "UPH_hash:PartyMaster|List_Parties",  # Hash Key to get linked_parties list for Party Master Ordered by primary role and is_default
    # Hash key to store each Party Master and its Role as List
    "Party Master Role": "UPH_hash:PartyMaster|Roles List",
    "get_party_master_roles": "UPH_hash:PartyMaster|Roles List",
    "get_pm_roles": "UPH_hash:PartyMaster|Roles List",
    "party_master.roles": "UPH_hash:PartyMaster|Roles List",
    "roles": "UPH_hash:PartyMaster|Roles List",
    # get List of each Party Type with Unset Party Master As hash field is Party type
    # field will be the party type like customer or return the whole list for all party Types
    "get_unset_party_master_parties_list": "UPH_hash: All Unset Parties",
    "unseted_parties": "UPH_hash: All Unset Parties",
    # For list of all party mapped to party master It's hash with key the party Type doctype
    "get_party_to_pm_list": "UPH_hash:PartiesToPartyMaster",
    "get_parties_to_pm_list": "UPH_hash:PartiesToPartyMaster",
    "get_all_parties_to_pm_map": "UPH_hash:PartiesToPartyMaster",
    "functional_document_as_dict": "UPH:functional_doctypes",
    "document_type": "UPH:functional_doctypes",  # require field key
}


def make_key(name: str):
    """
    Get the cached key for the given key from Redis.
    Args:
        key (str): The key to get the cached key for.
    Returns:
        str: The cached key.
    """
    return f"UPH:{name}"


def get_cached_key(key: str):
    """
    Get the cached key for the given key from Redis.
    Args:
        key (str): The key to get the cached key for.
    Returns:
        str: The cached key.
    """
    if not UPH_cached_key_map.get(key):
        raise ValueError(f"Invalid key: {key}")
    return UPH_cached_key_map[key]


def get_cached(*args):
    """
    Get the cached value for the given key from Redis.
    Args:
        *args: The key to get the cached value for.
    Returns:
        The cached value.
    """
    key = args[0]
    if len(args) > 1:
        field = args[1]
        return frappe.cache.hget(UPH_cached_key_map[key], field)
    return frappe.cache.hget(UPH_cached_key_map[key])


def update_cached(hash, field, value):
    """
    Set the cached value for the given hash key with fieldin Redis.
    Args:
        *args[0]: The Hash key to set the cached value for.
        args[1]: The field to set the cached value for.
        args[2]: The value to set the cached value to.
    Returns:
        None
    """

    if not value:
        return
    key = UPH_cached_key_map[hash]
    # if key =="UPH_hash:PartyMaster|List_Parties":
    # frappe.cache.hdel("UPH_hash:PartiesToPartyMaster")
    # frappe.cache.hdel("UPH_hash:All Unset Parties")

    frappe.cache.hset(key, field, value)
    #    frappe.cache.hset(UPH_cached_key_map[key], field, None)


def delete_cached(key):
    frappe.cache.hdel(UPH_cached_key_map[key])


def get_party_type_list():
    """
    Get the list of party types from the Party Type doctype.
    if it's in local cache return otherwise search_redis .
    Returns:
        list: A list of party type names.
    """

    key = "uph_PartyTypeListName"

    def generator():
        party_type = frappe.cache.get_value(key)
        if party_type:
            return party_type
        party_type = frappe.db.get_all("Party Type", pluck="name", order_by="name asc")
        frappe.cache.set_value(key, party_type)
        return party_type

    return frappe.local_cache(key, "list", generator, regenerate_if_none=True)


def get_cached_party_master_parties(party_master, party_type=None):
    """
    Get the list of party that Linked to a Party master
    Returns:
        list: A list of dict with party name as name,party_name,party_type,default_currency with its party_master.
    """
    key = get_pm_parties_key()
    parties = frappe.cache.hget(key, party_master)
    if parties:
        if party_type:
            return [p for p in parties if p.get("party_type") == party_type] or []
        return parties
    parties = get_linked_parties_list(party_master)
    if parties:
        frappe.cache.hset(key, party_master, parties)
        if party_type:
            return [p for p in parties if p.get("party_type") == party_type] or []
        return parties


def update_cached_party_master_parties(party_master):
    if isinstance(party_master, str):
        party_master = [party_master]
    key = get_pm_parties_key()
    for p in party_master:
        parties = get_linked_parties_list(party_master)
        if parties:
            frappe.cache.hset(key, p, parties)


def update_cached_party_to_pm_data(
    party_type, party, new_party_master=None, old_party_master=None
):
    if old_party_master == new_party_master:
        return
    pm_parties_key = get_pm_parties_key()
    party_to_pm = get_party_to_pm_key(party_type)
    if old_party_master and (
        parties := frappe.cache.hget(pm_parties_key, old_party_master)
    ):
        parties = [
            p
            for p in parties
            if not (p.get("name") == party and p.get("party_type") == party_type)
        ]
        frappe.cache.hset(pm_parties_key, old_party_master, parties)
    party_master = new_party_master if new_party_master else "None"
    frappe.cache.hset(party_to_pm, party, party_master)
    if new_party_master:
        parties = get_linked_parties_list(new_party_master)
        frappe.cache.hset(pm_parties_key, new_party_master, parties)


def get_pm_parties_key():
    return "PartyMaster|List_Parties"


def get_party_to_pm_key(party_type):
    return f"PartyToPartyMaster | {party_type}"


def get_cached_party_to_pm_map(party_type, party):
    key = get_party_to_pm_key(party_type)
    party_master = frappe.cache.hget(key, party)
    if party_master:
        return None if party_master == "None" else party_master
    party_master = frappe.db.get_value(party_type, party, "party_master")
    if party_master:
        frappe.cache.hset(key, party, party_master)
    return party_master
