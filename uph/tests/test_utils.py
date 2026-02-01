import frappe

try:
    from frappe.tests.utils import make_test_records
except ImportError:
    from frappe.test_runner import make_test_records


def before_tests():
    """Setup necessary fixtures for tests, especially for clean environments like CI"""
    # 1. Initialize ERPNext Test baseline (Company, Fiscal Year, etc.)
    setup_erpnext_test_fixtures()

    # 2. Pre-load essential ERPNext test records
    # This satisfies dependencies for tests that assume standard ERPNext data exists.
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
            # We don't want to crash before_tests if some optional records fail.
            pass


def setup_erpnext_test_fixtures():
    """Ensure basic records exist for preloading to succeed"""
    if not frappe.db.exists("Company", "_Test Company"):
        try:
            setup_erpnext_baseline()
        except Exception as e:
            print(f"DEBUG: setup_erpnext_baseline failed: {e}")


def setup_erpnext_baseline():
    """Programmatically complete the ERPNext setup wizard for CI baseline"""
    from erpnext.setup.setup_wizard.setup_wizard import setup_complete

    if frappe.db.exists("Company", "_Test Company"):
        return

    from frappe.utils import today
    from frappe import _dict

    # We use _dict to allow attribute access like args.fy_start_date
    args = _dict(
        {
            "company_name": "_Test Company",
            "company_abbr": "_TC",
            "country": "United States",
            "currency": "USD",
            "chart_of_accounts": "Standard",
            "full_name": "Administrator",
            "email": "admin@example.com",
            "timezone": "UTC",
            "fy_start_date": f"{today()[:4]}-01-01",
            "fy_end_date": f"{today()[:4]}-12-31",
        }
    )

    try:
        # Ignore mandatory for setup wizard if it's acting up in new environments
        frappe.flags.ignore_mandatory = True
        setup_complete(args)
    except Exception as e:
        # We don't want to crash everything if setup wizard is partially broken in dev
        print(f"DEBUG: setup_erpnext_baseline failed: {e}")
    finally:
        frappe.flags.ignore_mandatory = False

    # Ensure a Fiscal Year exists for the current year
    from frappe.utils import getdate

    current_date = getdate(today())
    year = str(current_date.year)
    if not frappe.db.exists("Fiscal Year", year):
        try:
            frappe.get_doc(
                {
                    "doctype": "Fiscal Year",
                    "year": year,
                    "year_start_date": f"{year}-01-01",
                    "year_end_date": f"{year}-12-31",
                }
            ).insert(ignore_permissions=True)
        except Exception:
            pass

    frappe.db.commit()
    frappe.clear_cache()
    print("DEBUG: ERPNext baseline setup attempt complete.")
