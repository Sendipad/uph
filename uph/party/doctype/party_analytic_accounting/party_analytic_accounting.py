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
		from uph.party.doctype.party_analytic_accounting_party.party_analytic_accounting_party import PartyAnalyticAccountingParty

		allow_or_restrict: DF.Literal["Allow", "Restrict"]
		analytic_name: DF.Data
		companies: DF.Table[PartyAnalyticAccountingAllowedCompany]
		effective_from: DF.Date | None
		effective_to: DF.Date | None
		enabled: DF.Check
		is_default: DF.Check
		parties: DF.Table[PartyAnalyticAccountingParty]
		party_master: DF.Link
		status: DF.Literal["Active", "Inactive", "Archived"]
		title: DF.Data | None
		type: DF.Literal["Site", "Business Unit", "Branch", "Territory", "Cost Center", "Factory / Plant"]
	# end: auto-generated types


	def before_insert(self):
		self.set_title_field()

	def before_save(self):
		self.set_title_field()

	def set_title_field(self):
		if self.analytic_name and self.party_master:
			self.title = f"{self.analytic_name} - {self.party_master}"
	def before_delete(self):
			self.ensure_no_gl_links()

	def validate(self):
		"""Ensure all child table entries have the same party_master as the parent."""
		if not self.party_master:
			frappe.throw(_("Parent Party Master is not set."))

		for row in self.parties or []:
			if not row.party or not row.party_type:
				frappe.throw(
					_("Child party {0} does not have party or party type set.")
					.format(row.idx)
				)
			party = frappe.get_doc(row.party_type, row.party)

			if party.party_master  != self.party_master:
				frappe.throw(
					_("Child party {0} does not match parent Party Master {1}")
					.format(row.party, self.party_master)
				)

	def ensure_no_gl_links(self):
		count = frappe.db.count(
			"GL Entry",
			filters={"party_analytic_accounting": self.name}
		)

		if count > 0:
			frappe.throw(
				_("Cannot delete because this Party Analytic Accounting is used in {0} GL Entry records.")
				.format(count),
				title=_("Delete Not Allowed")
			)