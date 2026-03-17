import frappe
from frappe.tests.utils import FrappeTestCase

from uph.party.controllers.party import sync_party_name_from_party_master


class TestPartyNaming(FrappeTestCase):
	def setUp(self):
		# Enable naming sync
		settings = frappe.get_doc("Party Master Settings")
		settings.sync_erp_party_naming = 1
		settings.role_prefix_mode = "Prefix for All Role"
		settings.save()
		frappe.clear_cache(doctype="Party Master Settings")

		# Setup multi-party rule for Customer
		rule = frappe.db.get_value("Party Master Settings Party Type", {"party_type": "Customer"}, "name")
		if rule:
			doc_rule = frappe.get_doc("Party Master Settings Party Type", rule)
			doc_rule.allowed = 1
			doc_rule.rule_fieldname = "default_currency"
			doc_rule.save()

	def test_suffix_naming_rule_new_doc(self):
		# Create a Party Master
		pm = frappe.get_doc(
			{
				"doctype": "Party Master",
				"party_name": "Test Master Suffix",
				"party_number": "PM-999",
				"party_type": "Customer",
			}
		).insert(ignore_permissions=True)

		# Create a Customer linked to this PM (not yet inserted)
		customer = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": "Test Customer Suffix",
				"party_master": pm.name,
				"default_currency": "USD",
			}
		)

		# Sync naming
		sync_party_name_from_party_master(customer)

		# Expected: Cu-PM-999-USD
		# Prefix is 'Cu-' (2 chars + -)
		# Suffix is '-USD'
		self.assertEqual(customer.name, "Cu-PM-999-USD")

	def tearDown(self):
		frappe.db.rollback()
