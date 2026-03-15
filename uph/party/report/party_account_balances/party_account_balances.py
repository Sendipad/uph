# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt
from collections import Counter, defaultdict
from copy import copy

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.query_builder import functions as fn
from frappe.utils import add_days, flt, getdate

from uph.party.controllers.queries import (
	get_leaf_party_master_list_from_any_node,
	get_party_master_parties_db,
)


def execute(filters=None):
	filters = frappe._dict(filters or {})
	filters["company_currency"] = (
		frappe.get_cached_value("Company", filters.company, "default_currency") or None
	)
	build_filters(filters)
	data, fields = get_data(filters)
	data = apply_view_mode(data, filters)
	columns = get_columns(fields, filters)
	return columns, data


def build_filters(filters):
	if filters.party_master:
		filters["party_master"] = get_leaf_party_master_list_from_any_node(filters)
	# When party_master is empty/None, get_party_master_parties_db(None)
	# fetches all parties linked to any Party Master.
	filters["parties"] = get_party_master_parties_db(filters.party_master or None)


def get_data(filters):
	data = []

	arrange_balances = filters.arrange_balances
	columns = None if arrange_balances != "Horizontal" else []
	parties = filters.parties or []
	GL = DocType("GL Entry")
	where_conditions = (GL.company == filters.get("company")) & (GL.is_cancelled == 0)

	if parties:
		in_parties = [p.get("party") for p in parties]
		where_conditions &= GL.party.isin(in_parties)
	elif not parties:
		where_conditions &= GL.party.isnotnull()
	fields = [
		GL.party,
		GL.party_type,
		GL.account_currency.as_("currency"),
		((fn.Sum(GL.debit_in_account_currency) - fn.Sum(GL.credit_in_account_currency)).as_("balance")),
		fn.Max(GL.posting_date).as_("posting_date"),
	]
	if filters.in_company_currency:
		fields.append((fn.Sum(GL.debit) - fn.Sum(GL.credit)).as_("balance_in_cc"))
	balances = (
		frappe.qb.from_(GL)
		.select(
			*fields,
		)
		.where(where_conditions)
		.groupby(GL.party, GL.party_type)
	).run(as_dict=True)
	if balances and not filters.show_zero_balance:
		balances = [b for b in balances if b.get("balance", 0) != 0]
	if arrange_balances == "Horizontal" and balances:
		currency_list = [b.get("currency") for b in balances if b.get("currency")]
		currency_freq = Counter(currency_list)
		columns = [currency for currency, _ in currency_freq.most_common()]
	party_entries = {(entry.get("party_type"), entry.get("party")): entry for entry in balances}
	pm_entries = defaultdict(list)
	for p in parties:
		key = (p.get("party_type"), p.get("party"))

		if key in party_entries:
			pm_entries[(p.get("party_master"), p.get("party_type"))].append(party_entries.get(key))

	party_master_details = get_party_master_informations_as_dict(filters)

	for (pm, party_type), entries in pm_entries.items():
		pm_detail = party_master_details.get(pm)
		if not pm_detail:
			continue
		if arrange_balances != "Horizontal":
			for e in entries:
				e.update(pm_detail)
				data.append(e)
		elif arrange_balances == "Horizontal":
			pm_dict = copy(pm_detail)
			pm_dict["party_type"] = party_type
			posting_date = []
			balance_in_cc = 0
			for e in entries:
				currency = e.get("currency")
				pm_dict[currency] = e.get("balance")
				if filters.in_company_currency:
					balance_in_cc += e.get("balance_in_cc")
				if e.get("posting_date"):
					posting_date.append("{0} : {1}".format(_(currency), e.get("posting_date")))
			pm_dict["posting_date"] = ", ".join(posting_date)
			if filters.in_company_currency:
				pm_dict["balance_in_cc"] = balance_in_cc
			data.append(pm_dict)

	return data, columns


def apply_view_mode(data, filters):
	"""Apply view mode sorting/filtering after the base data is computed."""
	view_mode = filters.get("view_mode") or "Party Number"

	if view_mode == "Party Number":
		data.sort(key=lambda d: (d.get("party_master") or ""))
		return data

	if view_mode == "Zero Balance Accounts":
		return _filter_zero_balance(data, filters)

	if view_mode in ("Active Accounts", "Dormant Accounts"):
		return _sort_by_activity(data, filters, view_mode)

	if view_mode == "High Debit Balance":
		return _sort_by_debit_balance(data, filters)

	return data


def _filter_zero_balance(data, filters):
	"""Return only rows where all balance values are zero."""
	arrange_balances = filters.get("arrange_balances")

	if arrange_balances == "Horizontal":
		# In horizontal mode, check all currency columns
		result = []
		for row in data:
			has_nonzero = False
			for key, val in row.items():
				if key in (
					"party_type",
					"party_master",
					"party_name",
					"posting_date",
					"status",
					"mobile_no",
					"territory",
					"party_type_group",
					"party_details",
					"currency",
				):
					continue
				if isinstance(val, (int, float)) and flt(val) != 0:
					has_nonzero = True
					break
			if not has_nonzero:
				result.append(row)
		return result
	else:
		return [row for row in data if flt(row.get("balance", 0)) == 0]


def _get_active_parties(filters):
	"""Get set of parties that have transactions after from_date."""
	from_date = filters.get("from_date")
	if not from_date:
		from_date = add_days(frappe.utils.today(), -365)

	GL = DocType("GL Entry")
	conditions = (
		(GL.company == filters.get("company"))
		& (GL.is_cancelled == 0)
		& (GL.posting_date >= getdate(from_date))
	)

	parties = filters.get("parties") or []
	if parties:
		in_parties = [p.get("party") for p in parties]
		conditions &= GL.party.isin(in_parties)

	active = (frappe.qb.from_(GL).select(GL.party).where(conditions).groupby(GL.party)).run(pluck="party")

	return set(active or [])


def _get_parties_for_row(row):
	"""Extract the party identifiers from a data row for activity matching."""
	# In sequential mode, row has 'party' directly
	if row.get("party"):
		return {row["party"]}
	# In horizontal mode, we match by party_master
	return set()


def _sort_by_activity(data, filters, view_mode):
	"""Sort data by activity status. Active first (or Dormant first)."""
	active_parties = _get_active_parties(filters)
	is_active_mode = view_mode == "Active Accounts"

	# Build a mapping from party_master -> has_active_party
	# using the parties list from filters
	parties = filters.get("parties") or []
	pm_active_map = defaultdict(bool)
	for p in parties:
		if p.get("party") in active_parties:
			pm_active_map[p.get("party_master")] = True

	def sort_key(row):
		party = row.get("party")
		pm = row.get("party_master")

		# Check if this specific party (or its PM) is active
		is_active = (party and party in active_parties) or pm_active_map.get(pm, False)

		if is_active_mode:
			# Active first (0), then inactive (1)
			return (0 if is_active else 1, pm or "")
		else:
			# Dormant first (0), then active (1)
			return (1 if is_active else 0, pm or "")

	data.sort(key=sort_key)

	if is_active_mode:
		# Filter to only active accounts when in Active mode
		# Dormant accounts appear at the bottom
		pass  # All rows included, just sorted
	else:
		# Dormant mode: all rows included, dormant first
		pass

	return data


def _sort_by_debit_balance(data, filters):
	"""Sort by debit balance in company currency, descending.
	Optionally filter by debit_threshold."""
	company_currency = filters.get("company_currency")
	to_date = filters.get("to_date") or frappe.utils.today()
	debit_threshold = flt(filters.get("debit_threshold"))

	# Cache exchange rates to avoid repeated lookups
	exchange_rate_cache = {}

	def get_rate(currency):
		if not currency or currency == company_currency:
			return 1.0
		if currency not in exchange_rate_cache:
			try:
				from erpnext.setup.utils import get_exchange_rate

				rate = get_exchange_rate(currency, company_currency, to_date) or 1.0
			except Exception:
				rate = 1.0
			exchange_rate_cache[currency] = rate
		return exchange_rate_cache[currency]

	for row in data:
		# Compute debit balance in company currency
		if row.get("balance_in_cc") is not None:
			row["_sort_balance_cc"] = flt(row["balance_in_cc"])
		elif row.get("balance") is not None:
			currency = row.get("currency") or company_currency
			rate = get_rate(currency)
			row["_sort_balance_cc"] = flt(row["balance"]) * rate
		else:
			# Horizontal mode — sum all currency columns converted to company currency
			total = 0.0
			for key, val in row.items():
				if isinstance(val, (int, float)) and key not in (
					"balance_in_cc",
					"_sort_balance_cc",
				):
					# key is likely a currency code
					if key in (
						"party_type",
						"party_master",
						"party_name",
						"posting_date",
						"status",
						"mobile_no",
						"territory",
						"party_type_group",
						"party_details",
					):
						continue
					rate = get_rate(key)
					total += flt(val) * rate
			row["_sort_balance_cc"] = total

	# Filter by threshold if set (only positive/debit balances above threshold)
	if debit_threshold > 0:
		data = [row for row in data if flt(row.get("_sort_balance_cc", 0)) >= debit_threshold]

	# Sort descending by debit balance (positive = debit)
	data.sort(key=lambda d: flt(d.get("_sort_balance_cc", 0)), reverse=True)

	# Clean up temporary field
	for row in data:
		row.pop("_sort_balance_cc", None)

	return data


def get_party_master_informations_as_dict(filters):
	PM = DocType("Party Master")
	where_cond = PM.is_group == 0
	if filters.get("party_master"):
		where_cond &= PM.name.isin(filters.get("party_master"))

	party_master = (
		frappe.qb.from_(PM)
		.select(
			PM.name.as_("party_master"),
			PM.party_name,
			PM.status,
			PM.mobile_no,
			PM.territory,
			PM.party_type_group,
			PM.party_details,
		)
		.where(where_cond)
	).run(as_dict=True)
	return {pm.get("party_master"): pm for pm in party_master}


def get_columns(fields, filters):
	columns = [
		{"fieldname": "party_type", "label": _("Party Type"), "fieldtytpe": "Data"},
		{
			"fieldname": "party_master",
			"fieldtype": "Link",
			"options": "Party Master",
			"label": _("Party Master"),
		},
		{
			"fieldname": "party_name",
			"fieldtype": "Data",
			"label": _("Party Name"),
			"width": 200,
		},
	]
	if fields:
		for df in fields:
			columns.append(
				{
					"fieldname": df,
					"label": _("Balance ({0})").format(_(df)),
					"fieldtype": "Currency",
					"options": df,
				}
			)
	elif not fields:
		columns.extend(
			[
				{
					"fieldname": "balance",
					"label": _("Balance"),
					"fieldtype": "Currency",
					"options": "currency",
				},
				{
					"fieldname": "currency",
					"label": _("Currency"),
					"fieldtype": "Link",
					"options": "Currency",
				},
			]
		)

	if filters.in_company_currency:
		company_currency = filters.company_currency
		columns.append(
			{
				"fieldname": "balance_in_cc",
				"label": _("Balance ({0})").format(_(company_currency)),
				"fieldtype": "Currency",
				"options": company_currency,
			}
		)
	return [
		*columns,
		{"fieldname": "mobile_no", "fieldtype": "Data", "label": _("Mobile No")},
		{"fieldname": "posting_date", "fieldtype": "Data", "label": _("Latest Posting Date")},
		{"fieldname": "status", "fieldtype": "Data", "label": _("Status")},
		{"fieldname": "territory", "fieldtype": "Data", "label": _("Territory")},
		{"fieldname": "party_type_group", "fieldtype": "Data", "label": _("Party Type Group")},
		{"fieldname": "party_details", "fieldtype": "Text Editor", "label": _("Party Details")},
	]
