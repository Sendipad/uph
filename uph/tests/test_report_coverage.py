import frappe
from frappe.tests.utils import FrappeTestCase
from uph.tests.setup_mixin import AccountsTestMixin


class TestReportCoverage(FrappeTestCase, AccountsTestMixin):
    def setUp(self):
        self.create_company()
        self.create_item()
        self.create_party_master()
        self.create_customer(party_master=self.party_master)

        # Create a Sales Invoice for data
        si = frappe.new_doc("Sales Invoice")
        si.company = self.company
        si.customer = self.customer
        si.party_master = self.party_master
        si.debit_to = self.debit_to
        si.currency = self.currency
        si.posting_date = frappe.utils.today()
        si.due_date = frappe.utils.today()
        si.conversion_rate = 1
        si.plc_conversion_rate = 1
        si.append(
            "items",
            {
                "item_code": "_Test Item",
                "qty": 1,
                "rate": 100,
                "income_account": self.income_account,
                "cost_center": self.cost_center,
            },
        )
        si.insert()
        si.submit()

    def test_party_account_statement(self):
        from uph.party.report.party_account_statement.party_account_statement import (
            execute,
        )

        filters = {
            "company": self.company,
            "from_date": frappe.utils.add_days(frappe.utils.today(), -7),
            "to_date": frappe.utils.today(),
            "party_master": self.party_master,
        }
        columns, data, message, chart = execute(filters)
        self.assertTrue(len(columns) > 0)
        self.assertTrue(len(data) > 0)

    def test_party_accounting_ledger(self):
        from uph.party.report.party_accounting_ledger.party_accounting_ledger import (
            execute,
        )

        filters = {
            "company": self.company,
            "from_date": frappe.utils.add_days(frappe.utils.today(), -7),
            "to_date": frappe.utils.today(),
            "party_master": self.party_master,
        }
        columns, data, message, chart = execute(filters)
        self.assertTrue(len(columns) > 0)
        self.assertTrue(len(data) > 0)

    def test_chronological_party_ledger(self):
        from uph.party.report.chronological_party_ledger.chronological_party_ledger import (
            execute,
        )

        filters = {
            "company": self.company,
            "from_date": frappe.utils.add_days(frappe.utils.today(), -7),
            "to_date": frappe.utils.today(),
            "party_master": self.party_master,
        }
        columns, data, message, chart = execute(filters)
        self.assertTrue(len(columns) > 0)
        self.assertTrue(len(data) > 0)

    def test_party_account_balances(self):
        from uph.party.report.party_account_balances.party_account_balances import (
            execute,
        )

        filters = {"company": self.company, "party_master": self.party_master}
        columns, data = execute(filters)
        self.assertTrue(len(columns) > 0)
        self.assertTrue(len(data) > 0)

    def test_party_master_health_report(self):
        from uph.party.report.party_master_health_report.party_master_health_report import (
            execute,
        )

        filters = {"party_type": ["Customer"]}
        columns, data, message, chart = execute(filters)
        self.assertTrue(len(columns) > 0)
        self.assertIsInstance(data, list)
