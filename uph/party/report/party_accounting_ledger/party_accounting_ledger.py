# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt
import frappe
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
	get_dimension_with_children,
)
from frappe import _, qb, scrub
from frappe.query_builder import Criterion, CustomFunction, DocType
from frappe.query_builder import functions as fn
from frappe.query_builder.custom import ConstantColumn
from frappe.query_builder.functions import Coalesce, Concat, Count, Locate, Sum
from frappe.utils import add_months, nowdate, today, unique

import uph
from uph.party.controllers.queries import (
	get_party_master_parties,
	get_party_master_parties_db,
)


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_set_filters(filters)
	party_master = get_party_master(filters)
	columns = get_columns(filters)
	data = get_data(filters, party_master)
	return columns, data, None, None


def validate_set_filters(filters):
	if not filters.get("company"):
		frappe.throw(_("{0} is mandatory").format(_("Company")))
	if not filters.get("from_date") and not filters.get("to_date"):
		frappe.throw(
			_("{0} and {1} are mandatory").format(frappe.bold(_("From Date")), frappe.bold(_("To Date")))
		)
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))
	filters["company_currency"] = frappe.get_cached_value("Company", filters.company, "default_currency")

	display_options = set(filters.get("display_options", []))

	if "show_err" not in display_options:
		err_journals = frappe.db.get_all(
			"Journal Entry",
			filters={
				"company": filters.get("company"),
				"docstatus": 1,
				"voucher_type": (
					"in",
					["Exchange Rate Revaluation", "Exchange Gain Or Loss"],
				),
			},
			as_list=True,
		)
		if err_journals:
			filters.update({"voucher_no_not_in": [x[0] for x in err_journals]})

	if "show_cr_dr_notes" not in display_options:
		system_generated_cr_dr_journals = frappe.db.get_all(
			"Journal Entry",
			filters={
				"company": filters.get("company"),
				"docstatus": 1,
				"voucher_type": ("in", ["Credit Note", "Debit Note"]),
				"is_system_generated": 1,
			},
			as_list=True,
		)
		if system_generated_cr_dr_journals:
			vouchers_to_ignore = (filters.get("voucher_no_not_in") or []) + [
				x[0] for x in system_generated_cr_dr_journals
			]
			filters.update({"voucher_no_not_in": vouchers_to_ignore})


def get_party_master(filters):
	if not filters or not filters.get("party_master"):
		return None

	if not filters.get("is_group"):
		return (
			[filters["party_master"]] if isinstance(filters["party_master"], str) else filters["party_master"]
		)

	# Start with the selected parent group(s)
	parents = set(
		filters["party_master"] if isinstance(filters["party_master"], list) else [filters["party_master"]]
	)

	def collect_all_group_children(current_parents):
		found_new = True
		while found_new:
			found_new = False
			child_groups = frappe.db.get_all(
				"Party Master",
				filters={
					"parent_party_master": ["in", list(current_parents)],
					"is_group": 1,
				},
				fields=["name"],
			)
			for child in child_groups:
				if child.name not in current_parents:
					current_parents.add(child.name)
					found_new = True
		return current_parents

	all_group_names = collect_all_group_children(parents)

	# Now fetch all non-group (leaf) parties under any of the group names collected
	leaf_parties = frappe.db.get_all(
		"Party Master",
		filters={"parent_party_master": ["in", list(all_group_names)], "is_group": 0},
		pluck="name",
	)

	return leaf_parties


def get_data(filters, party_master):
	data = []
	party_type = filters.get("party_type", [])
	if not party_type or "All" in party_type:
		filters["party_type"] = uph.get_party_type_list()
	partylist = get_party_master_parties_db(party_master, all_roles=False, roles=filters.party_type)
	filters.party = [x.party for x in partylist]
	dimension = ["cost_center", "project", *get_accounting_dimensions(as_list=True)]

	opening, entries = query_gl(filters, dimension)
	opening_map = {
		(row.get("party"), row.get("party_type")): row for row in opening if row.get("type") == "Opening"
	}
	current_totals = {
		(row.get("party"), row.get("party_type")): row for row in opening if row.get("type") == "Current"
	}
	# Group entries by party
	party_entries = {}
	for entry in entries:
		party_entries.setdefault((entry.get("party"), entry.get("party_type")), []).append(entry)

	group_by_vn = True if filters.get("group_by") == "Group by Voucher (Consolidated)" else False
	hide_equal = (
		True
		if filters.get("display_options") and "Hide Equals Voucher" in filters.get("display_options")
		else False
	)

	def prepare_entries(key, party_master, balance, balance_in_cc, party_name):
		entries = party_entries.get(key, [])
		if not entries:
			return balance, balance_in_cc

		last_vn = None
		last_index = -1

		for entry in entries:
			debit = entry.get("debit") or 0
			credit = entry.get("credit") or 0
			debit_in_cc = entry.get("debit_in_cc") or 0
			credit_in_cc = entry.get("credit_in_cc") or 0

			if group_by_vn:
				current_vn = entry.get("voucher_no")

				if current_vn == last_vn:
					row = data[last_index]
					row["debit"] += debit
					row["credit"] += credit
					row["balance"] += debit - credit
					balance = row.get("balance", 0)

					if filters.get("in_company_currency"):
						row["debit_in_cc"] += debit_in_cc
						row["credit_in_cc"] += credit_in_cc
						row["balance_in_cc"] += debit_in_cc - credit_in_cc
						balance_in_cc = row.get("balance_in_cc")
					# After merging, check if debit == credit
					if hide_equal and row["debit"] == row["credit"]:
						data.pop(last_index)
						last_index -= 1
						last_vn = None
					continue

				else:
					balance += debit - credit
					balance_in_cc += debit_in_cc - credit_in_cc

					new_row = {
						**entry,
						"balance": balance,
						"balance_in_cc": balance_in_cc,
						"party_master": party_master,
						"party_name": party_name,
					}
					data.append(new_row)
					last_vn = current_vn
					last_index = len(data) - 1

			else:
				balance += debit - credit
				balance_in_cc += debit_in_cc - credit_in_cc

				new_row = {
					**entry,
					"balance": balance,
					"balance_in_cc": balance_in_cc,
					"party_master": party_master,
					"party_name": party_name,
				}

				if hide_equal and new_row["debit"] == new_row["credit"]:
					continue

				data.append(new_row)

		return balance, balance_in_cc

		# If not group_by_vn
		for entry in party_entries.get(key, []):
			debit = entry.get("debit") or 0
			credit = entry.get("credit") or 0
			debit_in_cc = entry.get("debit_in_cc") or 0
			credit_in_cc = entry.get("credit_in_cc") or 0

			balance += debit - credit
			balance_in_cc += debit_in_cc - credit_in_cc

			entry.update(
				{
					"balance": balance,
					"balance_in_cc": balance_in_cc,
					"party_master": party_master,
					"party_name": party_name,
				}
			)
			data.append(entry)

		return balance, balance_in_cc

	# Final data processing
	for party in partylist:
		key = (party.get("party"), party.get("party_type"))
		open_row = opening_map.get(key, {})
		open_balance = open_row.get("balance", 0) or 0
		balance_in_cc = open_row.get("balance_in_cc", 0) or 0
		if open_balance != 0 or (filters.get("in_company_currency") and balance_in_cc != 0):
			row = {**open_row}
			row.update(
				{
					"debit" if open_balance > 0 else "credit": abs(open_balance),
					**party,
					"remarks": _("Opening Balance"),
					"is_opening": 1,
				}
			)
			data.append(row)
		total_balance, _total_balance_in_cc = prepare_entries(
			key,
			party.get("party_master"),
			balance=open_balance,
			balance_in_cc=balance_in_cc,
			party_name=party.get("party_name"),
		)

		totals = current_totals.get(key)
		if totals:
			data.append(
				{
					"debit": totals.get("total_debit", 0),
					"credit": totals.get("total_credit", 0),
					**party,
					"remarks": _("Current Period Totals"),
					"current_balance": (totals.get("debit", 0) - totals.get("credit", 0)),
					"balance": total_balance,
					"opening": open_balance,
				}
			)
		if total_balance:
			data.extend(
				[
					{
						**party,
						"credit" if total_balance < 0 else "debit": abs(total_balance),
						# "debit_in_cc" if total_balance_in_cc>0 else "credit_in_cc":abs(total_balance_in_cc),
						"remarks": _("Closing (Opening + Total)"),
						"bold": 1,
					},
					{},
				]
			)
	return data


def query_gl(filters, dimension):
	import pypika.terms

	dimension = ["cost_center", "project", *get_accounting_dimensions(as_list=True)]
	GL = DocType("GL Entry")
	display_options = set(filters.get("display_options") or [])
	conditions = GL.company == filters.get("company")
	frappe.get_cached_value("Company", filters.get("company"), "default_currency")
	from_date = filters.get("from_date")
	period_condition = GL.posting_date.between(from_date, filters.get("to_date"))

	def get_totals_opening_and_current():
		total_fields = [
			GL.party_type,
			GL.party,
			fn.Sum(GL.debit_in_account_currency).as_("total_debit"),
			fn.Sum(GL.credit_in_account_currency).as_("total_credit"),
			(fn.Sum(GL.debit_in_account_currency) - fn.Sum(GL.credit_in_account_currency)).as_("balance"),
			GL.account_currency.as_("currency"),
		]
		if filters.get("in_company_currency"):
			total_fields.extend(
				[
					fn.Sum(GL.debit).as_("debit_in_cc"),
					fn.Sum(GL.credit).as_("credit_in_cc"),
					(fn.Sum(GL.debit) - fn.Sum(GL.credit)).as_("balance_in_cc"),
				]
			)
		opening = (
			frappe.qb.from_(GL)
			.select(*total_fields, ConstantColumn("Opening").as_("type"))
			.where((conditions) & (GL.posting_date < from_date))
			.groupby(GL.party, GL.party_type)
			.having(fn.Sum(GL.debit_in_account_currency) - fn.Sum(GL.credit_in_account_currency) != 0)
		)
		between_period = (
			frappe.qb.from_(GL)
			.select(*total_fields, ConstantColumn("Current").as_("type"))
			.where((conditions) & (period_condition))
			.groupby(GL.party, GL.party_type)
			.having(fn.Sum(GL.debit_in_account_currency) - fn.Sum(GL.credit_in_account_currency) != 0)
		)
		final_query = opening.union(between_period)
		return final_query.run(as_dict=True)

	if filters.party:
		conditions &= GL.party.isin(filters.get("party"))
	conditions &= GL.party_type.isin(filters.get("party_type"))

	if "show_cancelled_entries" not in display_options:
		conditions &= GL.is_cancelled == 0
	if filters.get("voucher_no_not_in"):
		conditions &= ~GL.voucher_no.isin(filters.get("voucher_no_not_in"))

	if filters.get("account"):
		conditions &= GL.account.isin(filters.get("account"))
	for df in dimension:
		if filters.get(df):
			conditions &= GL[df].isin(filters.get(df))

	total_query = get_totals_opening_and_current()
	fields = [
		GL.name.as_("entry"),
		GL.debit_in_account_currency.as_("debit"),
		GL.credit_in_account_currency.as_("credit"),
		GL.posting_date,
		GL.account,
		GL.remarks,
		GL.account_currency.as_("currency"),
		GL.party_type,
		GL.party,
		GL.voucher_type,
		GL.voucher_subtype,
		GL.voucher_no,
		GL.against_voucher_type,
		GL.against_voucher,
		GL.against,
		GL.is_opening,
		*dimension,
	]
	if filters.get("in_company_currency"):
		fields.extend([GL.debit.as_("debit_in_cc"), GL.credit.as_("credit_in_cc")])
	if "add_values_in_transaction_currency" in display_options:
		fields.extend(
			[
				GL.debit_in_transaction_currency,
				GL.credit_in_transaction_currency,
				GL.transaction_currency,
			]
		)

	gl_query = frappe.qb.from_(GL).select(*fields).where((conditions) & (period_condition))
	if filters.get("group_by") == "Group by Voucher (Consolidated)":
		gl_query.groupby(GL.party_type, GL.party, GL.voucher_type, GL.voucher_no)
	gl_query = gl_query.orderby("party_type", "party", "posting_date", "voucher_no", "creation")

	return total_query, gl_query.run(as_dict=True)


def query_gls(filters):
	dimension = ["cost_center", "project", *get_accounting_dimensions(as_list=True)]
	display_options = set(filters.get("display_options") or [])
	company = filters.get("company")
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	filters.get("company_currency")
	party_type = filters.get("party_type")
	party = filters.get("party")
	voucher_no_not_in = filters.get("voucher_no_not_in")
	in_company_currency = filters.get("in_company_currency")

	# Constructing the SELECT fields part
	fields = [
		"gl.name AS entry",
		"gl.posting_date",
		"gl.account",
		"gl.remarks",
		"gl.account_currency AS currency",
		"gl.party_type",
		"gl.party",
		"gl.voucher_type",
		"gl.voucher_subtype",
		"gl.voucher_no",
		"gl.against_voucher_type",
		"gl.against_voucher",
		"gl.against",
		"gl.is_opening",
		"gl.creation",
	]

	# Dimension Fields
	dimension_fields = ["gl.{}".format(df) for df in dimension]
	fields.extend(dimension_fields)

	conditions = ["gl.company = '{}'".format(company)]

	# Apply additional filters for dimensions
	if party:
		formatted_party = ",".join(
			[("'{}'".format(str(v).replace("'", "''")) if isinstance(v, str) else str(v)) for v in party]
		)
		conditions.append("gl.party IN ({})".format(formatted_party))

	if party_type:
		formatted_party_type = ",".join(
			[("'{}'".format(str(v).replace("'", "''")) if isinstance(v, str) else str(v)) for v in party_type]
		)
		conditions.append("gl.party_type IN ({})".format(formatted_party_type))

	# Opening fields (balance calculations)
	opening_fields = [
		"SUM(gl.debit_in_account_currency - gl.credit_in_account_currency) AS balance",
		"SUM(gl.debit - gl.credit) AS balance_in_cc",
		"gl.party_type",
		"gl.party",
		"gl.account",
		"gl.account_currency AS currency",
	]

	gl_entries_fields = [
		*fields,
		"gl.debit_in_account_currency AS debit",
		"gl.credit_in_account_currency AS credit",
	]

	if "show_cancelled_entries" not in display_options:
		conditions.append("gl.is_cancelled = 0")

	if voucher_no_not_in:
		formatted_voucher_no_not_in = ",".join(
			[
				("'{}'".format(str(v).replace("'", "''")) if isinstance(v, str) else str(v))
				for v in voucher_no_not_in
			]
		)
		conditions.append("gl.voucher_no NOT IN ({})".format(formatted_voucher_no_not_in))

	if "add_values_in_transaction_currency" in display_options:
		gl_entries_fields.extend(
			[
				"gl.debit_in_transaction_currency",
				"gl.credit_in_transaction_currency",
				"gl.transaction_currency",
			]
		)

	if in_company_currency:
		gl_entries_fields.extend(["gl.debit AS debit_in_cc", "gl.credit AS credit_in_cc"])

	# Define the query for MariaDB - Opening Query
	mariadb_opening_query = """
        SELECT {0}
        FROM `tabGL Entry` gl
        WHERE {1}
        AND gl.posting_date < '{2}'
        GROUP BY gl.party_type, gl.party;
    """.format(", ".join(opening_fields), " AND ".join(conditions), from_date)

	# Define the query for MariaDB - GL Entries Query
	mariadb_gl_entries_query = """
        SELECT {0}
        FROM `tabGL Entry` gl
        WHERE {1}
        AND gl.posting_date BETWEEN '{2}' AND '{3}'
        ORDER BY gl.party_type, gl.party, gl.posting_date, gl.creation;
    """.format(", ".join(gl_entries_fields), " AND ".join(conditions), from_date, to_date)

	# Define the query for PostgreSQL - Opening Query
	postgres_opening_query = """
        SELECT {0}
        FROM "tabGL Entry" gl
        WHERE {1}
        AND gl.posting_date < '{2}'
        GROUP BY gl.party_type, gl.party;
    """.format(", ".join(opening_fields), " AND ".join(conditions), from_date)

	# Define the query for PostgreSQL - GL Entries Query
	postgres_gl_entries_query = """
        SELECT {0}
        FROM "tabGL Entry" gl
        WHERE {1}
        AND gl.posting_date BETWEEN '{2}' AND '{3}'
        ORDER BY gl.party_type, gl.party, gl.posting_date, gl.creation;
    """.format(", ".join(gl_entries_fields), " AND ".join(conditions), from_date, to_date)

	# Execute queries separately using frappe.db.multisql
	opening_query = frappe.db.multisql(
		{"mariadb": mariadb_opening_query, "postgres": postgres_opening_query},
		as_dict=True,
	)

	gl_entries_query = frappe.db.multisql(
		{"mariadb": mariadb_gl_entries_query, "postgres": postgres_gl_entries_query},
		as_dict=True,
	)

	# Run the queries and return results

	return opening_query, gl_entries_query


def get_columns(filters):
	company_currency = filters.get("company_currency", "YER")
	columns = [
		{
			"label": "GL Entry",
			"fieldname": "gl_entry",
			"hidden": 1,
		},
		{
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 120,
		},
		{
			"label": _("Voucher No"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 150,
		},
		{
			"label": _("Voucher Subtype"),
			"fieldname": "voucher_subtype",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": _("Remarks"),
			"fieldname": "remarks",
			"fieldtype": "Data",
			"align": "right",
			"width": 200,
		},
		{
			"label": _("Currency"),
			"fieldname": "currency",
			"fieldtype": "Data",
			"width": 50,
			"hidden": 0,
		},
		{
			"label": _("Debit"),
			"fieldname": "debit",
			"fieldtype": "Float",
			"width": 110,
			"precision": 2,
		},
		{
			"label": _("Credit"),
			"fieldname": "credit",
			"fieldtype": "Float",
			"width": 110,
			"precision": 2,
		},
		{
			"label": _("The Balance"),
			"fieldname": "balance",
			"fieldtype": "Currency",
			"width": 130,
			"options": "currency",
		},
		{
			"label": _("Party Name"),
			"fieldname": "party_name",
			"fieldtype": "Data",
		},
		{
			"label": _("Party Master"),
			"fieldname": "party_master",
			"fieldtype": "Link",
			"options": "Party Master",
			# "Party Profile" is used in the column definition for the "Account No"
			# field. This indicates that the "Account No" field is linked to the "Party
			# Profile" document in the system.
			"align": "left",
			"width": 100,
		},
		{
			"label": _("Party Type"),
			"fieldname": "party_type",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": _("Party"),
			"fieldname": "party",
			"fieldtype": "Dynamic Link",
			"options": "party_type",
			# "Party Profile" is used in the column definition for the "Account No"
			# field. This indicates that the "Account No" field is linked to the "Party
			# Profile" document in the system.
			"align": "left",
			"width": 100,
		},
		{
			"label": _("Voucher Type"),
			"fieldname": "voucher_type",
			"fieldtype": "Data",
			"width": 100,
		},
	]
	if filters.get("include_dimensions"):
		columns.append(
			{
				"label": _("Cost Center"),
				"options": "Cost Center",
				"fieldname": "cost_center",
				"width": 100,
			}
		)
		for dim in get_accounting_dimensions(as_list=False):
			columns.append(
				{
					"label": _(dim.label),
					"options": dim.label,
					"fieldname": dim.fieldname,
					"width": 100,
				}
			)
		columns.append(
			{
				"label": _("Project"),
				"options": "Project",
				"fieldname": "project",
				"width": 100,
			}
		)
	if filters.get("in_company_currency"):
		columns[9:9] = [
			{
				"label": _("Debit ({0})").format(company_currency),
				"fieldname": "debit_in_cc",
				"fieldtype": "Float",
				"width": 110,
				"precision": 2,
			},
			{
				"label": _("Credit ({0})").format(company_currency),
				"fieldname": "credit_in_cc",
				"fieldtype": "Float",
				"width": 110,
				"precision": 2,
			},
			{
				"label": _("Balance ({0})").format(company_currency),
				"fieldname": "balance_in_cc",
				"fieldtype": "Currency",
				"width": 130,
				"options": "company_currency",
			},
		]

	return columns
