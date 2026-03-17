import frappe
from frappe.tests.utils import FrappeTestCase

from uph.party.boot import get_pm_doctypes


class TestBootFunctions(FrappeTestCase):
	def test_get_pm_doctypes(self):
		result = get_pm_doctypes()
		self.assertIsInstance(result, (list, tuple))
		if result:
			self.assertEqual(len(result[0]), 3)  # Each item has 3 elements
