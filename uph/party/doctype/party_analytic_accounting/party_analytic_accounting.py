# Copyright (c) 2024, Abdo Ruzaqi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class PartyAnalyticAccounting(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from uph.party.doctype.party_analytic_accounting_allowed_company.party_analytic_accounting_allowed_company import PartyAnalyticAccountingAllowedCompany

		allowed_companies: DF.Table[PartyAnalyticAccountingAllowedCompany]
		analytic_name: DF.Data
		apply_to_all_companies: DF.Check
		apply_to_all_parties: DF.Check
		effective_from: DF.Date | None
		effective_to: DF.Date | None
		enabled: DF.Check
		is_default: DF.Check
		party_master: DF.Link
		status: DF.Literal["Active", "Inactive", "Archived"]
		title: DF.Data | None
		type: DF.Literal["Site", "Business Unit", "Branch", "Territory", "Cost Center", "Factory / Plant"]
	# end: auto-generated types
	pass
