import frappe
from frappe.tests.utils import FrappeTestCase
from uph.party.controllers.queries import (
    party_master_link_query,
    get_roles_for_pm,
    get_party_master_parties_db,
    get_party_master_parties,
    get_leaf_party_master_list_from_any_node,
    usage_counts_on_reference_doctype,
    get_all_vouchers_documents_with_null_or_another_party_master,
    query_similar_name_or_number,
)
from uph.tests.setup_mixin import AccountsTestMixin


class TestQueries(FrappeTestCase, AccountsTestMixin):
    def setUp(self):
        self.create_company()
        self.create_party_master()

    def test_get_party_master_parties(self):
        pm = frappe.get_all(
            "Party Master", filters={"is_group": 0}, limit=1, pluck="name"
        )
        if pm:
            result = get_party_master_parties(pm[0])
            self.assertIsInstance(result, list)

    def test_get_roles_for_pm(self):
        pm = frappe.get_all(
            "Party Master", filters={"is_group": 0}, limit=1, pluck="name"
        )
        if pm:
            result = get_roles_for_pm(pm[0])
            self.assertIsInstance(result, list)

    def test_get_party_master_parties_db(self):
        pm = frappe.get_all(
            "Party Master", filters={"is_group": 0}, limit=1, pluck="name"
        )
        if pm:
            result = get_party_master_parties_db(pm[0])
            self.assertIsInstance(result, list)

    def test_get_party_master_parties_db_with_roles(self):
        pm = frappe.get_all(
            "Party Master",
            filters={"is_group": 0, "party_type": "Customer"},
            limit=1,
            pluck="name",
        )
        if pm:
            # Test with matching role
            result = get_party_master_parties_db(
                pm[0], all_roles=False, roles=["Customer"]
            )
            self.assertIsInstance(result, list)
            # Test with non-matching role
            result_empty = get_party_master_parties_db(
                pm[0], all_roles=False, roles=["Supplier"]
            )
            self.assertEqual(len(result_empty), 0)

    def test_get_leaf_party_master_list(self):
        # Create a group and leaf for testing hierarchy
        group_pm = frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": "_Test Group PM",
                "is_group": 1,
                "party_type": "Customer",
            }
        ).insert(ignore_permissions=True)

        leaf_pm = frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": "_Test Leaf PM",
                "is_group": 0,
                "parent_party_master": group_pm.name,
                "party_type": "Customer",
            }
        ).insert(ignore_permissions=True)

        result = get_leaf_party_master_list_from_any_node(
            {"party_master": [group_pm.name]}
        )
        self.assertIn(leaf_pm.name, result)

    def test_party_master_link_query(self):
        # Create a party master
        pm_name = "_Test PM Link Query"
        frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": pm_name,
                "is_group": 0,
                "party_type": "Customer",
            }
        ).insert(ignore_permissions=True)

        # Test the query
        result = party_master_link_query(
            "Party Master",
            pm_name,
            "party_name",
            20,
            0,
            filters={"party_type": "Customer"},
        )
        self.assertTrue(len(result) > 0)
        names = [r[0] for r in result]
        self.assertIn(
            frappe.db.get_value("Party Master", {"party_name": pm_name}, "name"), names
        )

    def test_get_party_master_parties_db_multi(self):
        # Test with a list of party masters
        pm1 = frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": "PM 1",
                "is_group": 0,
                "party_type": "Customer",
            }
        ).insert(ignore_permissions=True)
        pm2 = frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": "PM 2",
                "is_group": 0,
                "party_type": "Customer",
            }
        ).insert(ignore_permissions=True)

        create_customer(pm1.name + " Cust", party_master=pm1.name)
        create_customer(pm2.name + " Cust", party_master=pm2.name)

        result = get_party_master_parties_db([pm1.name, pm2.name])
        self.assertEqual(len(result), 2)
        pms = [r.get("party_master") for r in result]
        self.assertIn(pm1.name, pms)
        self.assertIn(pm2.name, pms)

    def test_get_party_master(self):
        from uph.party.controllers.queries import get_party_master

        result = get_party_master("Party Master", "", "name", 0, 20, {"is_group": 0})
        self.assertIsInstance(list(result), list)

    def test_get_unlinked_party(self):
        from uph.party.controllers.queries import get_unlinked_party

        # Create a customer without party_master - but since party_master is mandatory, we need to set it temporarily
        cust_name = "_Test Unlinked Customer"
        if not frappe.db.exists("Customer", cust_name):
            cust = frappe.get_doc(
                {
                    "doctype": "Customer",
                    "customer_name": cust_name,
                    "party_master": self.party_master,
                }
            )
            cust.insert(ignore_permissions=True)

        # Now unset the party_master to test the unlinked function
        frappe.db.set_value("Customer", cust_name, "party_master", None)

        result = get_unlinked_party({"party_type": "Customer"})
        names = [r.get("name") for r in result]
        self.assertIn(cust_name, names)

    def test_get_counts_of_unposted_or_cancelled_vouchers(self):
        from uph.party.controllers.queries import (
            get_counts_of_unposted_or_cancelled_vouchers,
        )

        # Ensure there's a draft Sales Invoice
        if not frappe.db.exists("Company", "_Test Company"):
            # Create minimal company
            frappe.get_doc(
                {
                    "doctype": "Company",
                    "company_name": "_Test Company",
                    "default_currency": "YER",
                }
            ).insert(ignore_permissions=True)

        result = get_counts_of_unposted_or_cancelled_vouchers("_Test Company")
        self.assertIsInstance(result, list)

    def test_query_similar_name_or_number(self):
        # Create a party master
        pm_name = "Duplicate Check PM"
        pm_number = "PM-DUP-001"
        pm = frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": pm_name,
                "party_number": pm_number,
                "is_group": 0,
                "party_type": "Customer",
            }
        ).insert(ignore_permissions=True)

        # 1. Exact Name match
        res = query_similar_name_or_number(party_name=pm_name)
        self.assertEqual(res.get("exact_name"), pm.name)

        # 2. Case variation (normalization check)
        res = query_similar_name_or_number(party_name=pm_name.upper())
        self.assertEqual(res.get("exact_name"), pm.name)

        # 3. Exact Number match
        res = query_similar_name_or_number(party_number=pm_number)
        self.assertEqual(res.get("exact_number"), pm.name)

        # 4. No match
        res = query_similar_name_or_number(party_name="Non Existent PM")
        self.assertNotIn("exact_name", res)


def create_customer(name, party_master=None):
    if not frappe.db.exists("Customer", name):
        cust = frappe.get_doc(
            {"doctype": "Customer", "customer_name": name, "party_master": party_master}
        ).insert(ignore_permissions=True)
        return cust.name
    return name
