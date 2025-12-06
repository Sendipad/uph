import frappe
from frappe.tests.utils import FrappeTestCase
from uph.controllers.queries import get_party_master_parties, get_roles_for_pm, get_linked_parties_list, get_unlinked_party, get_party_master_parties_db

class TestQueries(FrappeTestCase):
    def test_get_party_master_parties(self):
        pm = frappe.get_all("Party Master", filters={"is_group": 0}, limit=1, pluck="name")
        if pm:
            result = get_party_master_parties(pm[0])
            self.assertIsInstance(result, (list, type(None)))

    def test_get_roles_for_pm(self):
        pm = frappe.get_all("Party Master", filters={"is_group": 0}, limit=1, pluck="name")
        if pm:
            result = get_roles_for_pm(pm[0])
            self.assertIsInstance(result, list)

    def test_get_linked_parties_list(self):
        pm = frappe.get_all("Party Master", filters={"is_group": 0}, limit=1, pluck="name")
        if pm:
            result = get_linked_parties_list(pm[0])
            self.assertIsInstance(result, (list, type(None)))

    def test_get_unlinked_party(self):
        # get_unlinked_party expects frappe._dict, not plain dict
        result = get_unlinked_party(frappe._dict({"party_type": ["Customer"]}), limit=5)
        self.assertIsInstance(result, (list, type(None)))

    def test_get_party_master_parties_db(self):
        pm = frappe.get_all("Party Master", filters={"is_group": 0}, limit=1, pluck="name")
        if pm:
            result = get_party_master_parties_db(pm[0])
            self.assertIsInstance(result, list)
