import frappe
from frappe.tests.utils import FrappeTestCase


class TestAPIEndpoints(FrappeTestCase):
	def test_get_totals_number_unlinked_parties(self):
		from uph.party.doctype.party_master.party_master import (
			get_totals_number_unlinked_parties,
		)

		result = get_totals_number_unlinked_parties()
		self.assertIsInstance(result, dict)

	def test_get_party_master_balances(self):
		from uph.party.doctype.party_master.party_master import (
			get_party_master_balances,
		)

		# Enable show_party_balance temporarily
		initial_value = frappe.get_single_value("Accounts Settings", "show_party_balance")
		frappe.db.set_single_value("Accounts Settings", "show_party_balance", 1)

		try:
			company = frappe.get_all("Company", limit=1, pluck="name")
			if company:
				result = get_party_master_balances(company[0])
				self.assertIsInstance(result, list)
		finally:
			frappe.db.set_single_value("Accounts Settings", "show_party_balance", initial_value)

	def test_check_similar_party_name(self):
		from uph.party.doctype.party_master.party_master import check_similar_party_name

		self.assertIsInstance(check_similar_party_name("Test"), list)

	def test_get_children(self):
		from uph.party.doctype.party_master.party_master import get_children

		self.assertIsInstance(get_children("Party Master"), list)

	def test_get_parents(self):
		from uph.party.doctype.party_master.party_master import get_parents

		pm = frappe.get_all("Party Master", limit=1, pluck="name")
		if pm:
			self.assertIsInstance(get_parents("Party Master", pm[0]), list)

	def test_get_party_master_details_with_parties(self):
		from uph.party.controllers.party import get_party_master_details_with_parties

		pm = frappe.get_all("Party Master", filters={"is_group": 0}, limit=1, pluck="name")
		if pm:
			result = get_party_master_details_with_parties(pm[0])
			self.assertIn("party_master", result)
