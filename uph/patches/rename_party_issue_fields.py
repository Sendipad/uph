"""
Pre-model-sync patch: rename Party Issue fields.

1. Rename field ``party`` -> ``party_master`` (preserves column data via rename-field)
2. Migrate ``party_secondary`` -> ``reference_name`` / ``reference_doctype``
   for rows that have a party_secondary value (Duplicate issues).

Must run BEFORE the DocType JSON is synced so the old columns still exist.
"""

import frappe


def execute():
	if not frappe.db.exists("DocType", "Party Issue"):
		return

	# Step 0 - reload the new JSON so the new fieldname exists in the schema
	frappe.reload_doc("party", "doctype", "party_issue")

	# Step 1 - rename ``party`` -> ``party_master`` (copies data)
	if frappe.db.has_column("Party Issue", "party"):
		from frappe.model.utils.rename_field import rename_field

		rename_field("Party Issue", "party", "party_master")

	# Step 2 - migrate ``party_secondary`` -> reference fields
	if frappe.db.has_column("Party Issue", "party_secondary"):
		# Only migrate rows where party_secondary has a value AND reference_name
		# is currently empty (to avoid overwriting existing references).
		frappe.db.sql(
			"""
            UPDATE `tabParty Issue`
            SET
                reference_name = party_secondary,
                reference_doctype = 'Party Master'
            WHERE party_secondary IS NOT NULL
              AND party_secondary != ''
              AND (reference_name IS NULL OR reference_name = '')
            """
		)

		# Null out the old column so it's clean before the column is dropped
		frappe.db.sql(
			"""
            UPDATE `tabParty Issue`
            SET party_secondary = NULL
            WHERE party_secondary IS NOT NULL
            """
		)

	frappe.db.commit()
