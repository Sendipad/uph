"""
Cache utilities for UPH
Provides centralized caching for Party Master Settings configuration
"""

import frappe
from frappe.utils.caching import redis_cache

# Cache key constants
CACHE_KEY_CONFIGURED_DOCTYPES = "uph:configured_doctypes"
CACHE_KEY_PARTY_TYPES = "uph:configured_party_types"
CACHE_KEY_PM_DOCTYPES = "uph:pm_doctypes_list"
CACHE_KEY_DEPENDS_ON = "uph:depends_on_fields"
CACHE_KEY_FUNCTIONAL_MAPPING = "uph:functional_mapping"
CACHE_TTL = 3600  # 1 hour

# Dashboard cache keys
DASHBOARD_STATS_KEYS = [
	"uph:stats:duplicate_open",
	"uph:stats:duplicate_ignored",
	"uph:stats:duplicate_resolved",
	"uph:stats:unlinked_open",
	"uph:stats:policy_draft",
	"uph:stats:policy_cancelled",
	"uph:stats:policy_mismatch",
	"uph:stats:total_parties",
	"uph:stats:total_groups",
	"uph:stats:incomplete_count",
	"uph:stats:last_updated",
]


class SmartCache:
	"""
	Centralized Smart Cache System for UPH.
	Combines Local Cache (Request Scope) and Redis Cache (Shared Scope).
	"""

	@staticmethod
	def make_key(namespace, identifier):
		return f"UPH:{namespace}|{identifier}"

	@staticmethod
	def get_cached_value(key, generator=None, ttl=CACHE_TTL):
		"""
		Get value from cache (local -> redis -> generator)
		"""
		# 1. Check Local Cache (Request Scope)
		if hasattr(frappe.local, "uph_cache") and key in frappe.local.uph_cache:
			return frappe.local.uph_cache[key]

		# 2. Check Redis Cache
		val = frappe.cache.get_value(key)
		if val is not None:
			# Populate Local Cache
			SmartCache._set_local(key, val)
			return val

		# 3. Generate if missing
		if generator:
			val = generator()
			if val is not None:
				frappe.cache.set_value(key, val, expires_in_sec=ttl)
				SmartCache._set_local(key, val)
			return val

		return None

	@staticmethod
	def set_cached_value(key, value, ttl=CACHE_TTL):
		frappe.cache.set_value(key, value, expires_in_sec=ttl)
		SmartCache._set_local(key, value)

	@staticmethod
	def delete_cached_value(key):
		frappe.cache.delete_value(key)
		if hasattr(frappe.local, "uph_cache") and key in frappe.local.uph_cache:
			del frappe.local.uph_cache[key]

	@staticmethod
	def _set_local(key, value):
		if not hasattr(frappe.local, "uph_cache"):
			frappe.local.uph_cache = {}
		frappe.local.uph_cache[key] = value

	@staticmethod
	def hget(key, field, generator=None):
		# Redis Hash Get
		val = frappe.cache.hget(key, field)
		return val

	@staticmethod
	def hset(key, field, value):
		frappe.cache.hset(key, field, value)

	# --- Specialized Accessors ---

	@classmethod
	def get_party_type_list(cls):
		key = "uph_PartyTypeListName"

		def generator():
			return frappe.db.get_all("Party Type", pluck="name", order_by="name asc")

		return cls.get_cached_value(key, generator)

	@classmethod
	def get_party_master_parties(cls, party_master):
		"""Get linked parties for a Party Master"""
		key = cls.make_key("PartyMaster", "List_Parties")

		# We use hash here for potentially large number of PMs
		val = cls.hget(key, party_master)
		if val:
			return val

		# Generator logic inline for Hash context
		from uph.party.controllers.queries import get_party_master_parties_db

		val = get_party_master_parties_db(party_master)
		if val:
			cls.hset(key, party_master, val)
		return val

	@classmethod
	def update_party_master_parties(cls, party_master):
		if isinstance(party_master, str):
			party_master = [party_master]

		key = cls.make_key("PartyMaster", "List_Parties")
		from uph.party.controllers.queries import get_party_master_parties_db

		for pm in party_master:
			val = get_party_master_parties_db(pm)
			if val:
				cls.hset(key, pm, val)

	@classmethod
	def invalidate_party_master_parties(cls, party_master):
		"""Invalidate the cached parties list for a Party Master (Lazy Invalidation)"""
		if isinstance(party_master, str):
			party_master = [party_master]

		key = cls.make_key("PartyMaster", "List_Parties")
		for pm in party_master:
			frappe.cache.hdel(key, pm)

	@classmethod
	def get_party_to_pm_map(cls, party_type, party_name):
		key = cls.make_key("PartyToPartyMaster", party_type)
		val = cls.hget(key, party_name)
		if val:
			return None if val == "None" else val

		val = frappe.db.get_value(party_type, party_name, "party_master")
		if val:
			cls.hset(key, party_name, val)
		return val

	@classmethod
	def update_party_to_pm_data(cls, party_type, party, new_pm=None, old_pm=None):
		if old_pm == new_pm:
			return

		# Update Party Mapping
		key_map = cls.make_key("PartyToPartyMaster", party_type)
		val_to_set = new_pm if new_pm else "None"
		cls.hset(key_map, party, val_to_set)

		# Update Lists
		key_list = cls.make_key("PartyMaster", "List_Parties")

		# Remove from old
		if old_pm:
			old_list = cls.hget(key_list, old_pm)
			if old_list:
				old_list = [
					p for p in old_list if not (p.get("name") == party and p.get("party_type") == party_type)
				]
				cls.hset(key_list, old_pm, old_list)

		# Add to new (Refresh whole list to be safe and sorted)
		if new_pm:
			from uph.party.controllers.queries import get_party_master_parties_db

			new_list = get_party_master_parties_db(new_pm)
			cls.hset(key_list, new_pm, new_list)


def clear_all_caches():
	"""
	Clear all UPH settings caches.
	Should be called when Party Master Settings is updated.
	"""
	cache = frappe.cache()

	# 1. Clear Settings-based caches
	keys = [
		CACHE_KEY_CONFIGURED_DOCTYPES,
		CACHE_KEY_PARTY_TYPES,
		CACHE_KEY_PM_DOCTYPES,
		CACHE_KEY_DEPENDS_ON,
		CACHE_KEY_FUNCTIONAL_MAPPING,
		"uph_PartyTypeListName",
	]
	for key in keys:
		cache.delete_value(key)
		SmartCache.delete_cached_value(key)

	# 2. Clear Hash Maps
	# We reconstruct keys to clear them
	keys_to_clear = [
		SmartCache.make_key("PartyMaster", "List_Parties"),
		# We cannot iterate known Party Types easily here to clear PartyToPartyMaster|{Type}
		# But we can try common ones or pattern delete if supported (redis usually supports patterns but frappe wrapper might vary)
	]

	# Try clearing common party types maps
	try:
		party_types = frappe.get_all("Party Type", pluck="name")
		for pt in party_types:
			keys_to_clear.append(SmartCache.make_key("PartyToPartyMaster", pt))
	except Exception:
		pass

	for key in keys_to_clear:
		cache.delete_value(key)

	# 3. Clear Document Cache
	frappe.clear_document_cache("Party Master Settings", "Party Master Settings")


def invalidate_dashboard_stats():
	"""
	Clear dashboard-related cache keys to avoid stale cards.
	"""
	for key in DASHBOARD_STATS_KEYS:
		frappe.cache.delete_value(key)

	# Related aggregates used by dashboard/list endpoints
	frappe.cache.delete_value("uph:unlinked_count")
	frappe.cache.delete_value("uph:unlinked_tx_count")
	frappe.cache.delete_value("uph:health_counts")


def get_configured_doctypes():
	def generator():
		if not frappe.db.exists("DocType", "Party Master Settings"):
			return set()
		settings = frappe.get_cached_doc("Party Master Settings", "Party Master Settings")
		if not settings:
			return set()
		return {d.document_type for d in settings.document_types if d.document_type and d.enabled}

	val = SmartCache.get_cached_value(CACHE_KEY_CONFIGURED_DOCTYPES, generator)
	return set(val) if val else set()


def get_configured_party_types():
	def generator():
		if not frappe.db.exists("DocType", "Party Master Settings"):
			return set()
		settings = frappe.get_cached_doc("Party Master Settings", "Party Master Settings")
		if not settings:
			return set()
		return {d.party_type for d in settings.party_types if d.party_type}

	val = SmartCache.get_cached_value(CACHE_KEY_PARTY_TYPES, generator)
	return set(val) if val else set()


def is_configured_doctype(doctype):
	return doctype in get_configured_doctypes()


def is_configured_party_type(party_type):
	return party_type in get_configured_party_types()


def get_pm_doctypes():
	def generator():
		return frappe.get_all(
			"Party Master Settings DocType",
			filters={"enabled": 1, "parenttype": "Party Master Settings"},
			fields=["parent_doctype", "document_type", "party_fieldname"],
			as_list=True,
		)

	return SmartCache.get_cached_value(CACHE_KEY_PM_DOCTYPES, generator)


def get_party_master_depends_on_fields():
	def generator():
		fields = frappe.get_all(
			"Party Master Settings DocType",
			filters={"enabled": 1, "parenttype": "Party Master Settings"},
			fields=["parent_doctype", "party_fieldname"],
			as_list=True,
		)
		return {f[0]: f[1] for f in fields} if fields else {}

	return SmartCache.get_cached_value(CACHE_KEY_DEPENDS_ON, generator)


def get_doctypes_functional_fields_mapping_as_dict():
	def generator():
		doctypes = frappe.db.get_all(
			"Party Master Settings DocType",
			filters={"parenttype": "Party Master Settings", "enabled": 1},
			fields=[
				"document_type",
				"parent_doctype",
				"is_dynamic_party_type",
				"reqd",
				"party_fieldname",
				"party_type_fieldname",
				"party_type",
			],
		)
		docs = {}
		for d in doctypes:
			try:
				# Minimal metadata check
				doctype = d.get("parent_doctype")
				document_type = d.get("document_type")
				if frappe.db.exists("DocType", doctype):  # Lighter check than get_meta for stability
					docs.update({doctype: d})
					if doctype != document_type:
						docs.update({document_type: d})
			except Exception:
				pass
		return docs

	return SmartCache.get_cached_value(CACHE_KEY_FUNCTIONAL_MAPPING, generator)
