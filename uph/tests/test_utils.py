import frappe


def before_tests():
    """Setup necessary fixtures for tests, especially for clean environments like CI"""
    setup_erpnext_test_fixtures()


def setup_erpnext_test_fixtures():
    """Create essential ERPNext test records if they don't exist"""
    # 1. Create Item Group
    if not frappe.db.exists("Item Group", "_Test Item Group"):
        frappe.get_doc(
            {
                "doctype": "Item Group",
                "item_group_name": "_Test Item Group",
                "parent_item_group": "All Item Groups",
                "is_group": 0,
            }
        ).insert(ignore_permissions=True)

    # 2. Create Warehouse (requires a Company)
    # Note: We use the default _Test Company typically used in ERPNext tests
    if not frappe.db.exists("Company", "_Test Company"):
        try:
            from erpnext.setup.doctype.company.company import install_country_fixtures
        except ImportError:
            from erpnext.setup.default_after_install import install_country_fixtures

        install_country_fixtures("_Test Company", "United States")

        frappe.get_doc(
            {
                "doctype": "Company",
                "company_name": "_Test Company",
                "abbr": "_TC",
                "default_currency": "USD",
                "country": "United States",
            }
        ).insert(ignore_permissions=True)

    if not frappe.db.exists("Warehouse", "_Test Warehouse - _TC"):
        frappe.get_doc(
            {
                "doctype": "Warehouse",
                "warehouse_name": "_Test Warehouse",
                "company": "_Test Company",
                "warehouse_type": "Transit",
                "is_group": 0,
            }
        ).insert(ignore_permissions=True)

    # 3. Create Fiscal Year for current date
    from frappe.utils import getdate, today

    current_date = getdate(today())
    year = str(current_date.year)
    if not frappe.db.exists("Fiscal Year", year):
        frappe.get_doc(
            {
                "doctype": "Fiscal Year",
                "year": year,
                "year_start_date": f"{year}-01-01",
                "year_end_date": f"{year}-12-31",
            }
        ).insert(ignore_permissions=True)

    frappe.db.commit()
