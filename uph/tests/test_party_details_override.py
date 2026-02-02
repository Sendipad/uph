import frappe
from frappe.tests.utils import FrappeTestCase
from erpnext.accounts.party import get_party_details
from uph.party.controllers.party import get_party_details as uph_get_party_details


class TestPartyDetailsOverride(FrappeTestCase):
    def setUp(self):
        self.company = "_Test Company"
        self.currency_usd = "USD"
        self.currency_sar = "SAR"

        # 1. Ensure Currencies exist
        if not frappe.db.exists("Currency", self.currency_usd):
            frappe.get_doc(
                {"doctype": "Currency", "currency": self.currency_usd}
            ).insert()
        if not frappe.db.exists("Currency", self.currency_sar):
            frappe.get_doc(
                {"doctype": "Currency", "currency": self.currency_sar}
            ).insert()

        # 2. Setup Party Master Hierarchy
        self.parent_pm = frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": "Parent PM",
                "is_group": 1,
                "party_type": "Customer",
            }
        ).insert(ignore_permissions=True)

        self.child_pm = frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": "Child PM",
                "is_group": 0,
                "parent_party_master": self.parent_pm.name,
                "party_type": "Customer",
            }
        ).insert(ignore_permissions=True)

        # 3. Create Customer linked to Child PM
        self.customer = frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": "Hierarchical Customer",
                "party_master": self.child_pm.name,
            }
        ).insert(ignore_permissions=True)

        # 4. Setup Group Account for PM
        self.group_account = frappe.get_doc(
            {
                "doctype": "Account",
                "account_name": "PM Group Receivable",
                "parent_account": "Temporary Accounts - _TC",
                "is_group": 1,
                "company": self.company,
                "account_type": "Receivable",
            }
        ).insert(ignore_permissions=True)

        # 5. Create Currency-specific accounts under group
        self.acc_usd = frappe.get_doc(
            {
                "doctype": "Account",
                "account_name": "PM Receivable USD",
                "parent_account": self.group_account.name,
                "is_group": 0,
                "company": self.company,
                "account_currency": self.currency_usd,
                "account_type": "Receivable",
            }
        ).insert(ignore_permissions=True)

        self.acc_sar = frappe.get_doc(
            {
                "doctype": "Account",
                "account_name": "PM Receivable SAR",
                "parent_account": self.group_account.name,
                "is_group": 0,
                "company": self.company,
                "account_currency": self.currency_sar,
                "account_type": "Receivable",
            }
        ).insert(ignore_permissions=True)

        # 6. Map Group Account to Parent PM
        self.parent_pm.append(
            "accounts", {"company": self.company, "account": self.group_account.name}
        )
        self.parent_pm.save(ignore_permissions=True)

        # 7. Enable Override in Settings
        settings = frappe.get_doc("Party Master Settings")
        settings.override_party_details_api = 1
        settings.save(ignore_permissions=True)

        # 8. Ensure Company has default receivable account (for fallback test)
        if not frappe.db.get_value(
            "Company", self.company, "default_receivable_account"
        ):
            frappe.db.set_value(
                "Company", self.company, "default_receivable_account", "Debtors - _TC"
            )
            frappe.clear_cache(doctype="Company", name=self.company)

    def tearDown(self):
        frappe.db.rollback()

    def test_hierarchical_account_lookup_usd(self):
        # Call the UPH override directly to verify logic
        details = uph_get_party_details(
            party=self.customer.name,
            party_type="Customer",
            company=self.company,
            currency=self.currency_usd,
        )
        self.assertEqual(details.get("debit_to"), self.acc_usd.name)

    def test_hierarchical_account_lookup_sar(self):
        details = uph_get_party_details(
            party=self.customer.name,
            party_type="Customer",
            company=self.company,
            currency=self.currency_sar,
        )
        self.assertEqual(details.get("debit_to"), self.acc_sar.name)

    def test_fallback_to_erp_defaults(self):
        # Create a customer without any PM linkage
        plain_customer = frappe.get_doc(
            {"doctype": "Customer", "customer_name": "Plain Customer"}
        ).insert(ignore_permissions=True)

        details = uph_get_party_details(
            party=plain_customer.name, party_type="Customer", company=self.company
        )

        # Verify that UPH doesn't interfere with standard ERPNext result when PM is missing
        erp_details = get_party_details(
            party=plain_customer.name, party_type="Customer", company=self.company
        )
        self.assertEqual(details.get("debit_to"), erp_details.get("debit_to"))
