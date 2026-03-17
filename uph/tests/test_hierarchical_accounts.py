import frappe
from frappe.tests.utils import FrappeTestCase

from uph.party.controllers.party import get_party_details


class TestHierarchicalAccounts(FrappeTestCase):
	def setUp(self):
		self.company = "_Test Company"
		self.currency_usd = "USD"
		self.currency_sar = "SAR"

		# Reload Settings to avoid cached state
		self.settings = frappe.get_doc("Party Master Settings")
		self.settings.override_party_details_api = 1
		self.settings.enforce_strict_currency = 0
		self.settings.save(ignore_permissions=True)
		frappe.clear_cache(doctype="Party Master Settings")

		# Setup Hierarchy
		self.root_pm = frappe.get_doc(
			{
				"doctype": "Party Master",
				"party_name": "Test Acc Root",
				"is_group": 1,
				"party_type": "Customer",
			}
		).insert(ignore_permissions=True)

		self.parent_pm = frappe.get_doc(
			{
				"doctype": "Party Master",
				"party_name": "Test Acc Parent",
				"is_group": 1,
				"parent_party_master": self.root_pm.name,
				"party_type": "Customer",
			}
		).insert(ignore_permissions=True)

		self.child_pm = frappe.get_doc(
			{
				"doctype": "Party Master",
				"party_name": "Test Acc Child",
				"is_group": 0,
				"parent_party_master": self.parent_pm.name,
				"party_type": "Customer",
			}
		).insert(ignore_permissions=True)

		# Create a Customer
		self.customer = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": f"Test Acc Customer {frappe.generate_hash(length=4)}",
				"party_master": self.child_pm.name,
			}
		).insert(ignore_permissions=True)

		# Setup Accounts
		self.root_acc = self.create_account("Test Acc Root Account", "Receivable", is_group=1, currency="")
		self.parent_acc_usd = self.create_account(
			"Test Acc Parent USD", "Receivable", currency=self.currency_usd
		)
		self.child_acc_sar = self.create_account(
			"Test Acc Child SAR", "Receivable", currency=self.currency_sar
		)

	def create_account(self, name, account_type, is_group=0, currency=None):
		full_name = f"{name} - _TC"
		if frappe.db.exists("Account", full_name):
			frappe.delete_doc("Account", full_name, force=1)

		acc_dict = {
			"doctype": "Account",
			"account_name": name,
			"parent_account": "Temporary Accounts - _TC",
			"is_group": is_group,
			"company": self.company,
			"account_type": account_type,
		}
		if currency is not None:
			acc_dict["account_currency"] = currency
		else:
			acc_dict["account_currency"] = "SAR"

		acc = frappe.get_doc(acc_dict).insert(ignore_permissions=True)
		return acc

	def tearDown(self):
		frappe.db.rollback()

	def test_direct_leaf_account_match(self):
		self.child_pm.reload()
		self.child_pm.append(
			"accounts",
			{
				"company": self.company,
				"currency": self.currency_usd,
				"account": self.parent_acc_usd.name,
			},
		)
		self.child_pm.save(ignore_permissions=True)

		details = get_party_details(
			party=self.customer.name,
			party_type="Customer",
			company=self.company,
			currency=self.currency_usd,
		)
		self.assertEqual(details.get("debit_to"), self.parent_acc_usd.name)

	def test_hierarchical_fallback_to_parent(self):
		self.parent_pm.reload()
		self.parent_pm.append(
			"accounts",
			{
				"company": self.company,
				"currency": self.currency_usd,
				"account": self.parent_acc_usd.name,
			},
		)
		self.parent_pm.save(ignore_permissions=True)

		details = get_party_details(
			party=self.customer.name,
			party_type="Customer",
			company=self.company,
			currency=self.currency_usd,
		)
		self.assertEqual(details.get("debit_to"), self.parent_acc_usd.name)

	def test_group_account_expansion(self):
		self.root_pm.reload()
		self.root_pm.append("accounts", {"company": self.company, "account": self.root_acc.name})
		self.root_pm.save(ignore_permissions=True)

		# Create a leaf under Root Account for USD
		usd_leaf = self.create_account("Test Root USD Leaf", "Receivable", currency=self.currency_usd)
		usd_leaf.parent_account = self.root_acc.name
		usd_leaf.save(ignore_permissions=True)

		# Ensure root_pm.accounts[0].currency is empty for generic match
		self.root_pm.reload()
		self.root_pm.accounts[0].currency = None
		self.root_pm.save(ignore_permissions=True)

		frappe.clear_cache(doctype="Account")

		details = get_party_details(
			party=self.customer.name,
			party_type="Customer",
			company=self.company,
			currency=self.currency_usd,
		)
		self.assertEqual(details.get("debit_to"), usd_leaf.name)

	def test_strict_currency_enforcement(self):
		self.parent_pm.reload()
		self.parent_pm.append(
			"accounts",
			{
				"company": self.company,
				"currency": self.currency_sar,
				"account": self.child_acc_sar.name,
			},
		)
		self.parent_pm.save(ignore_permissions=True)

		# Enable Strict
		self.settings.reload()
		self.settings.enforce_strict_currency = 1
		self.settings.save(ignore_permissions=True)

		details = get_party_details(
			party=self.customer.name,
			party_type="Customer",
			company=self.company,
			currency=self.currency_usd,
		)
		self.assertNotEqual(details.get("debit_to"), self.child_acc_sar.name)
