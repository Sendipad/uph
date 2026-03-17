import frappe
from frappe.model import no_value_fields


# Cache field options for 1 hour
@frappe.whitelist()  # nosemgrep
def get_field_options(doctype):
	cache_key = f"field_options:{doctype}"
	cached = frappe.cache().get_value(cache_key)

	if cached:
		return cached

	result = _get_field_options(doctype)
	frappe.cache().set_value(cache_key, result, expires_in_sec=3600)
	return result


def _get_field_options(doctype):
	"""Return all available fields including child tables"""
	meta = frappe.get_meta(doctype)
	options = []

	# Parent fields
	for field in meta.fields:
		if field.fieldtype not in no_value_fields:
			options.append(
				{
					"label": f"{field.label} ({field.fieldname})",
					"value": field.fieldname,
					"fieldtype": field.fieldtype,
					"options": field.options,
				}
			)

	# Child table fields
	for table_field in meta.get_table_fields():
		child_meta = frappe.get_meta(table_field.options)
		for child_field in child_meta.fields:
			if child_field.fieldtype not in no_value_fields:
				options.append(
					{
						"label": f"{table_field.label} → {child_field.label}",
						"value": f"{table_field.fieldname}.{child_field.fieldname}",
						"fieldtype": child_field.fieldtype,
						"options": child_field.options,
					}
				)

	return options
