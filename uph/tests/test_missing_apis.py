import frappe
from frappe.tests.utils import FrappeTestCase

from uph.party.doctype.party_master.party_master import get_unset_parties_list


class TestMissingAPIs(FrappeTestCase):
	def setUp(self):
		frappe.db.delete("Party Master")
		frappe.db.delete("Customer")

	def test_get_unset_parties_list(self):
		# Create Root Group
		root = frappe.get_doc(
			{
				"doctype": "Party Master",
				"party_name": "Root Group",
				"is_group": 1,
				"party_type": "Customer",
			}
		).insert(ignore_permissions=True)

		# Create Party Master (role Customer)
		pm = frappe.get_doc(
			{
				"doctype": "Party Master",
				"party_name": "Test Master",
				"party_type": "Customer",
				"parent_party_master": root.name,
				"is_group": 0,
			}
		).insert(ignore_permissions=True)

		# Create Customer without link
		frappe.get_doc({"doctype": "Customer", "customer_name": "Unlinked Customer"}).insert(
			ignore_permissions=True
		)

		# Call API
		results = get_unset_parties_list(
			"Party Master", "", "name", 0, 20, {"party_master": pm.name}, as_dict=True
		)

		# Verify
		# The API returns specific field names (customer_name), not aliased 'party_name'
		found = False
		for r in results:
			if r.get("customer_name") == "Unlinked Customer":
				found = True
				break
		self.assertTrue(found, f"Customer not found in results: {results}")
