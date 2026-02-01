import frappe
from frappe.tests.utils import make_test_records


def before_tests():
    """Setup necessary fixtures for tests, especially for clean environments like CI"""

    # 1. Initialize ERPNext Test baseline (Company, Fiscal Year, etc.)
    setup_erpnext_test_fixtures()

    # 2. Pre-load essential ERPNext test records that are commonly required by plugins
    # This prevents LinkValidationError during automatic upfront preloading in v16+
    for doctype in [
        "Unit of Measure",
        "Account",
        "Cost Center",
        "Item Group",
        "Item",
        "Warehouse",
    ]:
        try:
            make_test_records(doctype, commit=True)
        except Exception as e:
            # We don't want to crash before_tests if some optional records fail,
            # but we log it for debugging.
            print(f"DEBUG: before_tests failed for {doctype}: {e}")


def setup_erpnext_test_fixtures():
    """Create essential ERPNext test baseline if it doesn't exist"""

    # Ensure _Test Company exists
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

    # Ensure Fiscal Year exists
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
