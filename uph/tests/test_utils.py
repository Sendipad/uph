import frappe

try:
	from frappe.tests.utils import make_test_records
except ImportError:
	from frappe.test_runner import make_test_records


from uph.setup.install import seed_default_party_master_structure


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
		except Exception:
			# We don't want to crash before_tests if some optional records fail.
			pass

	# 3. Seed UPH Party Master Structure
	# Required for tests to have a valid tree to work with
	seed_default_party_master_structure()

	# 4. Ensure default Address Template (prevents failures in clean CI)
	ensure_address_template()


def ensure_address_template():
	"""Ensure a default Address Template exists to prevent validation errors in tests"""
	if not frappe.db.exists("Address Template", {"country": "Saudi Arabia"}):
		try:
			frappe.get_doc(
				{
					"doctype": "Address Template",
					"country": "Saudi Arabia",
					"is_default": 0,
					"template": "{{ address_line1 }}\n{{ city }}\n{{ country }}",
				}
			).insert(ignore_permissions=True)
		except Exception:
			pass

	if not frappe.db.exists("Address Template", {"is_default": 1}):
		try:
			frappe.get_doc(
				{
					"doctype": "Address Template",
					"country": "India",
					"is_default": 1,
					"template": "{{ address_line1 }}\n{{ city }}\n{{ country }}",
				}
			).insert(ignore_permissions=True)
		except Exception:
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

	# These arguments match what ERPNext's setup wizard expects.
	# We use Yemen/YER to match AccountsTestMixin defaults.
	args = {
		"company_name": "_Test Company",
		"company_abbr": "_TC",
		"country": "Yemen",
		"currency": "YER",
		"chart_of_accounts": "Standard",
		"full_name": "Administrator",
		"email": "admin@example.com",
		"timezone": "UTC",
		"fy_start_date": f"{today()[:4]}-01-01",
		"fy_end_date": f"{today()[:4]}-12-31",
	}

	try:
		# Pass a frappe._dict to support attribute access inside setup_wizard
		frappe.flags.ignore_mandatory = True
		setup_complete(frappe._dict(args))
	except Exception:
		pass
	finally:
		frappe.flags.ignore_mandatory = False

	# Ensure a Fiscal Year exists for the current year (double check)
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
