import frappe


def before_uninstall():
	"""Called before app uninstall to clean up safely"""
	remove_custom_fields()
	remove_party_analytic_accounting_dimension()


def remove_custom_fields():
	"""Remove custom fields specifically added by UPH"""
	party_types = _get_party_types()
	tx_doctypes = _get_tx_doctypes()

	# Party Master link field on configured party types + transaction doctypes
	_delete_custom_fields(
		fieldname="party_master",
		doctypes=sorted(set(party_types + tx_doctypes)),
		fieldtype="Link",
		options="Party Master",
	)

	# Default flag only applies to party types
	_delete_custom_fields(
		fieldname="is_default_for_party_master",
		doctypes=party_types,
		fieldtype="Check",
	)


def remove_party_analytic_accounting_dimension():
	"""Remove Party Analytic Accounting dimension safely (and its generated fields)."""
	dimension_label = "Party Analytic Accounting"
	if not frappe.db.exists("Accounting Dimension", {"label": dimension_label}):
		return

	try:
		from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
			delete_accounting_dimension,
		)
	except Exception:
		# If ERPNext isn't available, fallback to disabling only
		_disable_accounting_dimension(dimension_label)
		return

	dim = frappe.get_doc("Accounting Dimension", {"label": dimension_label})
	delete_accounting_dimension(dim)
	dim.delete(ignore_permissions=True)


def _disable_accounting_dimension(dimension_label):
	if frappe.db.exists("Accounting Dimension", {"label": dimension_label}):
		dim = frappe.get_doc("Accounting Dimension", {"label": dimension_label})
		dim.disabled = 1
		dim.save(ignore_permissions=True)


def _delete_custom_fields(fieldname, doctypes, fieldtype=None, options=None):
	if not doctypes:
		return

	filters = {"fieldname": fieldname, "dt": ["in", doctypes]}
	if fieldtype:
		filters["fieldtype"] = fieldtype
	if options:
		filters["options"] = options

	fields = frappe.get_all("Custom Field", filters=filters, pluck="name")
	for name in fields:
		frappe.delete_doc("Custom Field", name, ignore_missing=True)


def _get_party_types():
	try:
		party_types = frappe.get_all(
			"Party Master Settings Party Type",
			filters={"parenttype": "Party Master Settings"},
			pluck="party_type",
		)
	except Exception:
		party_types = []
	return party_types or ["Customer", "Supplier", "Employee"]


def _get_tx_doctypes():
	doctypes = frappe.get_hooks("tx_doctype_with_party_master") or []
	doctypes.extend(["POS Invoice", "POS Profile"])
	return doctypes
