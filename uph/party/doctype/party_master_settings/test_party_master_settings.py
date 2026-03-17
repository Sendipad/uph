# Copyright (c) 2025, Abdo Mohammed Ruzaqi and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestPartyMasterSettings(FrappeTestCase):
	"""Comprehensive tests for every field in Party Master Settings."""

	def _get_settings(self):
		"""Get fresh copy of Party Master Settings."""
		return frappe.get_doc("Party Master Settings")

	# ═══════════════════════════════════════════
	# General Configuration
	# ═══════════════════════════════════════════

	def test_override_party_details_api_default(self):
		"""override_party_details_api should default to 1 (enabled)."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("override_party_details_api")
		self.assertEqual(field.default, "1")
		self.assertEqual(field.fieldtype, "Check")

	def test_enforce_strict_currency_default(self):
		"""enforce_strict_currency should default to 1 (enabled)."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("enforce_strict_currency")
		self.assertEqual(field.default, "1")
		self.assertEqual(field.fieldtype, "Check")

	# ═══════════════════════════════════════════
	# Numbering Section
	# ═══════════════════════════════════════════

	def test_numbering_format_default(self):
		"""numbering_format should default to 'Concatenated'."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("numbering_format")
		self.assertEqual(field.default, "Concatenated")
		self.assertEqual(field.fieldtype, "Select")

	def test_numbering_format_options(self):
		"""numbering_format should only allow Concatenated or Dash-Separated."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("numbering_format")
		options = [o.strip() for o in field.options.split("\n") if o.strip()]
		self.assertEqual(options, ["Concatenated", "Dash-Separated"])

	def test_digits_count_default(self):
		"""digits_count should default to 6."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("digits_count")
		self.assertEqual(field.default, "6")
		self.assertEqual(field.fieldtype, "Int")

	def test_digits_count_non_negative(self):
		"""digits_count should enforce non_negative constraint."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("digits_count")
		self.assertTrue(field.non_negative)

	def test_group_digits_default(self):
		"""group_digits should default to 4."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("group_digits")
		self.assertEqual(field.default, "4")
		self.assertEqual(field.fieldtype, "Int")

	def test_group_digits_non_negative(self):
		"""group_digits should enforce non_negative constraint."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("group_digits")
		self.assertTrue(field.non_negative)

	# ═══════════════════════════════════════════
	# Governance Rules Section
	# ═══════════════════════════════════════════

	def test_enforce_parent_numbering_default(self):
		"""enforce_parent_numbering should default to 0 (disabled)."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("enforce_parent_numbering")
		self.assertEqual(field.default, "0")
		self.assertEqual(field.fieldtype, "Check")

	def test_enforce_cross_type_uniqueness_default(self):
		"""enforce_cross_type_uniqueness should default to 0 (disabled)."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("enforce_cross_type_uniqueness")
		self.assertEqual(field.default, "0")
		self.assertEqual(field.fieldtype, "Check")

	def test_sync_erp_party_naming_default(self):
		"""sync_erp_party_naming should default to 0 (disabled)."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("sync_erp_party_naming")
		self.assertEqual(field.default, "0")
		self.assertEqual(field.fieldtype, "Check")

	def test_role_prefix_mode_options(self):
		"""role_prefix_mode should have 4 valid options."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("role_prefix_mode")
		options = [o.strip() for o in field.options.split("\n") if o.strip()]
		self.assertEqual(len(options), 4)
		self.assertIn("Prefix for All Role", options)
		self.assertIn("Prefix for Secondary Role", options)
		self.assertIn("Suffix for All Role", options)
		self.assertIn("Suffix Secondary Roles", options)

	def test_role_prefix_mode_default(self):
		"""role_prefix_mode should default to 'Prefix for All Role'."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("role_prefix_mode")
		self.assertEqual(field.default, "Prefix for All Role")

	def test_role_prefix_mode_depends_on_sync(self):
		"""role_prefix_mode should only appear when sync_erp_party_naming is enabled."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("role_prefix_mode")
		self.assertEqual(field.depends_on, "sync_erp_party_naming")

	# ═══════════════════════════════════════════
	# Setup Section
	# ═══════════════════════════════════════════

	def test_setup_finished_default(self):
		"""setup_finished should default to 0."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("setup_finished")
		self.assertEqual(field.default, "0")

	def test_setup_finished_is_read_only(self):
		"""setup_finished should be read_only to prevent manual changes."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("setup_finished")
		self.assertTrue(field.read_only)

	def test_governance_immutability_blocks_changes(self):
		"""Changing numbering_format after setup_finished=1 should throw."""
		settings = self._get_settings()
		original_format = settings.numbering_format
		original_setup = settings.setup_finished

		try:
			# Simulate: doc is already setup_finished
			settings.db_set("setup_finished", 1)

			# Now create a changed version in memory
			updated_settings = frappe.get_doc("Party Master Settings")
			# Manually set the "before save" state for the mock-validation
			updated_settings._doc_before_save = settings

			updated_settings.numbering_format = (
				"Dash-Separated" if original_format == "Concatenated" else "Concatenated"
			)

			# Now validate should throw because setup_finished=1 and numbering_format changed
			self.assertRaises(frappe.ValidationError, updated_settings.validate)
		finally:
			settings.db_set("setup_finished", original_setup)
			settings.db_set("numbering_format", original_format)

	def test_governance_immutability_allows_same_value(self):
		"""Saving same value when setup_finished=1 should NOT throw."""
		settings = self._get_settings()
		original_setup = settings.setup_finished

		try:
			settings.db_set("setup_finished", 1)
			settings.reload()

			# Same value — should not throw
			settings.validate()
		finally:
			settings.db_set("setup_finished", original_setup)

	# ═══════════════════════════════════════════
	# Party Master Tab — Tree View
	# ═══════════════════════════════════════════

	def test_auto_expand_levels_default(self):
		"""auto_expand_levels should default to 4."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("auto_expand_levels")
		self.assertEqual(field.default, "4")
		self.assertEqual(field.fieldtype, "Int")

	def test_hide_balance_default(self):
		"""hide_balance should default to 1 (hidden)."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("hide_balance")
		self.assertEqual(field.default, "1")
		self.assertEqual(field.fieldtype, "Check")

	# ═══════════════════════════════════════════
	# PAA Tab
	# ═══════════════════════════════════════════

	def test_enable_party_analytic_accounting_default(self):
		"""enable_party_analytic_accounting should default to 0."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("enable_party_analytic_accounting")
		self.assertEqual(field.default, "0")
		self.assertEqual(field.fieldtype, "Check")

	# ═══════════════════════════════════════════
	# Duplicate Voucher Configuration Tab
	# ═══════════════════════════════════════════

	def test_check_party_master_duplicate_vouchers_default(self):
		"""check_party_master_duplicate_vouchers should default to 1 (enabled)."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("check_party_master_duplicate_vouchers")
		self.assertEqual(field.default, "1")
		self.assertEqual(field.fieldtype, "Check")

	def test_duplicate_voucher_action_default(self):
		"""duplicate_voucher_action should default to 'Warn'."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("duplicate_voucher_action")
		self.assertEqual(field.default, "Warn")

	def test_duplicate_voucher_action_options(self):
		"""duplicate_voucher_action should only allow Warn or Stop."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("duplicate_voucher_action")
		options = [o.strip() for o in field.options.split("\n") if o.strip()]
		self.assertEqual(options, ["Warn", "Stop"])

	def test_duplicate_voucher_action_depends_on(self):
		"""duplicate_voucher_action visibility depends on check_party_master_duplicate_vouchers."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("duplicate_voucher_action")
		self.assertEqual(field.depends_on, "check_party_master_duplicate_vouchers")

	def test_role_to_bypass_duplicate_voucher_field(self):
		"""role_to_bypass_duplicate_voucher should be a Link to Role."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("role_to_bypass_duplicate_voucher")
		self.assertEqual(field.fieldtype, "Link")
		self.assertEqual(field.options, "Role")

	def test_role_to_bypass_depends_on(self):
		"""role_to_bypass_duplicate_voucher visibility depends on check_party_master_duplicate_vouchers."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("role_to_bypass_duplicate_voucher")
		self.assertEqual(field.depends_on, "check_party_master_duplicate_vouchers")

	# ═══════════════════════════════════════════
	# Child Table Fields
	# ═══════════════════════════════════════════

	def test_party_types_table_field(self):
		"""party_types should be a Table linked to 'Party Master Settings Party Type'."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("party_types")
		self.assertEqual(field.fieldtype, "Table")
		self.assertEqual(field.options, "Party Master Settings Party Type")

	def test_document_types_table_field(self):
		"""document_types should be a Table linked to 'Party Master Settings DocType'."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("document_types")
		self.assertEqual(field.fieldtype, "Table")
		self.assertEqual(field.options, "Party Master Settings DocType")

	def test_party_master_fields_table_field(self):
		"""party_master_fields should be a Table linked to 'Party Master Settings DocField'."""
		meta = frappe.get_meta("Party Master Settings")
		field = meta.get_field("party_master_fields")
		self.assertEqual(field.fieldtype, "Table")
		self.assertEqual(field.options, "Party Master Settings DocField")

	# ═══════════════════════════════════════════
	# Validate actual live settings have rows
	# ═══════════════════════════════════════════

	def test_settings_has_party_types(self):
		"""After install, party_types table should have rows."""
		settings = self._get_settings()
		self.assertGreater(len(settings.party_types), 0)

	def test_settings_has_document_types(self):
		"""After install, document_types table should have rows."""
		settings = self._get_settings()
		self.assertGreater(len(settings.document_types), 0)

	def test_party_types_have_required_columns(self):
		"""Each party_type row should have party_type set."""
		settings = self._get_settings()
		for row in settings.party_types:
			self.assertTrue(
				row.party_type,
				f"party_type is missing in party_types row {row.idx}",
			)

	def test_document_types_have_party_fieldname(self):
		"""Each document_type row should have party_fieldname set."""
		settings = self._get_settings()
		for row in settings.document_types:
			self.assertTrue(
				row.party_fieldname,
				f"party_fieldname is missing in document_types row {row.idx}",
			)

	# ═══════════════════════════════════════════
	# Validation Logic Tests
	# ═══════════════════════════════════════════

	def test_validate_duplicate_document_type_throws(self):
		"""Adding duplicate document_type mapping should throw ValidationError."""
		settings = self._get_settings()

		# Find an existing document type to duplicate
		if not settings.document_types:
			self.skipTest("No document_types configured")

		# Simulate save lifecycle by setting _doc_before_save
		settings._doc_before_save = settings.get_doc_before_save() or frappe._dict(
			{"document_types": list(settings.document_types)}
		)

		existing_row = settings.document_types[0]
		settings.append(
			"document_types",
			{
				"document_type": existing_row.document_type,
				"parent_doctype": existing_row.parent_doctype,
				"party_fieldname": existing_row.party_fieldname,
			},
		)
		self.assertRaises(frappe.ValidationError, settings.validate_document_types)

	def test_validate_missing_party_fieldname_throws(self):
		"""Adding a document type without party_fieldname should throw."""
		settings = self._get_settings()

		# Simulate save lifecycle
		settings._doc_before_save = settings.get_doc_before_save() or frappe._dict(
			{"document_types": list(settings.document_types)}
		)

		settings.append(
			"document_types",
			{
				"document_type": "Sales Invoice",
				"parent_doctype": "Sales Invoice",
				"party_fieldname": "",
			},
		)
		self.assertRaises(frappe.ValidationError, settings.validate_document_types)

	# ═══════════════════════════════════════════
	# Issingle and permissions
	# ═══════════════════════════════════════════

	def test_settings_is_single(self):
		"""Party Master Settings should be a Single DocType."""
		meta = frappe.get_meta("Party Master Settings")
		self.assertTrue(meta.issingle)

	def test_settings_has_system_manager_permission(self):
		"""System Manager should have full CRUD access."""
		meta = frappe.get_meta("Party Master Settings")
		sm_perms = [p for p in meta.permissions if p.role == "System Manager"]
		self.assertTrue(len(sm_perms) > 0)
		perm = sm_perms[0]
		self.assertTrue(perm.read)
		self.assertTrue(perm.write)
		self.assertTrue(perm.create)

	# ═══════════════════════════════════════════
	# Field Ordering
	# ═══════════════════════════════════════════

	def test_field_order_has_all_expected_fields(self):
		"""Field order should contain all key data fields."""
		meta = frappe.get_meta("Party Master Settings")
		fieldnames = [f.fieldname for f in meta.fields]
		expected = [
			"override_party_details_api",
			"enforce_strict_currency",
			"numbering_format",
			"digits_count",
			"group_digits",
			"enforce_parent_numbering",
			"enforce_cross_type_uniqueness",
			"sync_erp_party_naming",
			"role_prefix_mode",
			"setup_finished",
			"auto_expand_levels",
			"hide_balance",
			"enable_party_analytic_accounting",
			"check_party_master_duplicate_vouchers",
			"duplicate_voucher_action",
			"role_to_bypass_duplicate_voucher",
			"party_types",
			"document_types",
			"party_master_fields",
		]
		for field in expected:
			self.assertIn(field, fieldnames, f"Field '{field}' missing from meta")
