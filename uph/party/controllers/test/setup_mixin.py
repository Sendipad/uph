import frappe
from frappe import qb

from erpnext.stock.doctype.item.test_item import create_item


class AccountsTestMixin:
    def create_party_master(
        self, party_name="_Test Party Master", parent_party_master="1310"
    ):
        if not frappe.db.exists("Party Master", {"party_name": party_name}):
            pm = frappe.new_doc("Party Master")
            pm.party_name = party_name
            pm.parent_party_master = parent_party_master
			pm.type="Individual"
            pm.save()
            self.party_master = pm.name

    def create_company(self, company_name="_Test Company", abbr="_TC"):
        self.company_abbr = abbr
        if frappe.db.exists("Company", company_name):
            company = frappe.get_doc("Company", company_name)
        else:
            company = frappe.get_doc(
                {
                    "doctype": "Company",
                    "company_name": company_name,
                    "country": "Yemen",
                    "default_currency": "YER",
                    "create_chart_of_accounts_based_on": "Standard Template",
                    "chart_of_accounts": "Standard",
                }
            )
            company = company.save()

        self.company = company.name
        self.cost_center = company.cost_center
        self.warehouse = "Stores - " + abbr
        self.finished_warehouse = "Finished Goods - " + abbr
        self.income_account = "Sales - " + abbr
        self.expense_account = "Cost of Goods Sold - " + abbr
        self.debit_to = "Debtors - " + abbr
        self.cash = "Cash - " + abbr
        self.creditors = "Creditors - " + abbr
        self.retained_earnings = "Retained Earnings - " + abbr

        # Deferred revenue, expense and bank accounts
        
    def create_customer(
        self, customer_name="_Test Customer", party_master=None, currency=None
    ):
        if not frappe.db.exists("Customer", customer_name):
            customer = frappe.new_doc("Customer")
            customer.customer_name = customer_name
            customer.type = "Individual"
            if party_master:
                customer.party_master = party_master
            if currency:
                customer.default_currency = currency
            customer.save()
            self.customer = customer.name
        else:
            self.customer = customer_name

    def create_supplier(
        self, supplier_name="_Test Supplier", party_master=None, currency=None
    ):
        if not frappe.db.exists("Supplier", supplier_name):
            supplier = frappe.new_doc("Supplier")
            supplier.supplier_name = supplier_name
            supplier.supplier_type = "Individual"
            supplier.supplier_group = "Local"
            if party_master:

                supplier.party_master = party_master

            if currency:
                supplier.default_currency = currency
            supplier.save()
            self.supplier = supplier.name
        else:
            self.supplier = supplier_name

    def create_item(
        self,
        item_name="_Test Item",
        is_stock=0,
        warehouse=None,
        company=None,
        valuation_rate=0,
    ):
        item = create_item(
            item_name,
            is_stock_item=is_stock,
            warehouse=warehouse,
            company=company,
            valuation_rate=valuation_rate,
        )
        self.item = item.name

    def enable_advance_as_liability(self):
        company = frappe.get_doc("Company", self.company)
        company.book_advance_payments_in_separate_party_account = True
        company.default_advance_received_account = self.advance_received
        company.default_advance_paid_account = self.advance_paid
        company.save()

    def disable_advance_as_liability(self):
        company = frappe.get_doc("Company", self.company)
        company.book_advance_payments_in_separate_party_account = False
        company.default_advance_paid_account = (
            company.default_advance_received_account
        ) = None
        company.save()

    def identify_default_warehouses(self):
        for w in frappe.db.get_all(
            "Warehouse",
            filters={"company": self.company},
            fields=["name", "warehouse_name"],
        ):
            setattr(
                self,
                "warehouse_" + w.warehouse_name.lower().strip().replace(" ", "_"),
                w.name,
            )

    def create_usd_receivable_account(self):
        account_name = "Debtors USD"
        if not frappe.db.get_value(
            "Account", filters={"account_name": account_name, "company": self.company}
        ):
            acc = frappe.new_doc("Account")
            acc.account_name = account_name
            acc.parent_account = "Accounts Receivable - " + self.company_abbr
            acc.company = self.company
            acc.account_currency = "USD"
            acc.account_type = "Receivable"
            acc.insert()
        else:
            name = frappe.db.get_value(
                "Account",
                filters={"account_name": account_name, "company": self.company},
                fieldname="name",
                pluck=True,
            )
            acc = frappe.get_doc("Account", name)
        self.debtors_usd = acc.name

    def create_usd_payable_account(self):
        account_name = "Creditors USD"
        if not frappe.db.get_value(
            "Account", filters={"account_name": account_name, "company": self.company}
        ):
            acc = frappe.new_doc("Account")
            acc.account_name = account_name
            acc.parent_account = "Accounts Payable - " + self.company_abbr
            acc.company = self.company
            acc.account_currency = "USD"
            acc.account_type = "Payable"
            acc.insert()
        else:
            name = frappe.db.get_value(
                "Account",
                filters={"account_name": account_name, "company": self.company},
                fieldname="name",
                pluck=True,
            )
            acc = frappe.get_doc("Account", name)
        self.creditors_usd = acc.name

    def clear_old_entries(self):
        doctype_list = [
            "GL Entry",
            "Payment Ledger Entry",
            "Sales Invoice",
            "Purchase Invoice",
            "Payment Entry",
            "Journal Entry",
            "Sales Order",
            "Exchange Rate Revaluation",
            "Bank Account",
            "Bank Transaction",
        ]
        for doctype in doctype_list:
            qb.from_(qb.DocType(doctype)).delete().where(
                qb.DocType(doctype).company == self.company
            ).run()

    def create_price_list(self):
        pl_name = "Mixin Price List"
        if not frappe.db.exists("Price List", pl_name):
            self.price_list = (
                frappe.get_doc(
                    {
                        "doctype": "Price List",
                        "currency": "INR",
                        "enabled": True,
                        "selling": True,
                        "buying": True,
                        "price_list_name": pl_name,
                    }
                )
                .insert()
                .name
            )
        else:
            self.price_list = frappe.get_doc("Price List", pl_name).name
