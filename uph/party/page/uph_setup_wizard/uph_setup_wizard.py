import json
import os

import frappe
from frappe import _


@frappe.whitelist()
def get_setup_status():
	"""Check if setup is already finished and if data exists."""
	return {
		"setup_finished": frappe.db.get_single_value("Party Master Settings", "setup_finished"),
		"has_data": frappe.db.count("Party Master") > 1,
		"languages": frappe.get_all("Language", fields=["name", "language_name"], order_by="language_name"),
	}


@frappe.whitelist()
def get_tree_templates():
	"""Return available templates from disk."""
	templates = []
	path = frappe.get_app_path("uph", "setup/data/templates")

	if os.path.exists(path):
		for fname in os.listdir(path):
			if fname.endswith(".json"):
				name = fname.replace(".json", "").title()
				templates.append(
					{
						"id": fname.replace(".json", ""),
						"name": name,
						"preview": _get_template_preview(os.path.join(path, fname)),
					}
				)
	return templates


def _get_template_preview(filepath):
	"""Return a simplified tree for preview."""
	try:
		with open(filepath) as f:
			data = json.load(f)
			# Return top-level nodes only for preview to save bandwidth
			return [
				{
					"party_name": d.get("party_name"),
					"party_number": d.get("party_number"),
				}
				for d in data
			]
	except Exception:
		return []


@frappe.whitelist()
def apply_setup_settings(settings: str, template_id: str):
	"""
	Apply settings and seed the tree.
	"""
	if frappe.db.get_single_value("Party Master Settings", "setup_finished"):
		frappe.throw(_("Setup is already finished."))

	data = json.loads(settings)

	# 1. Update Settings
	doc = frappe.get_doc("Party Master Settings")
	for field in [
		"digits_count",
		"group_digits",
		"numbering_format",
		"enforce_cross_type_uniqueness",
		"sync_erp_party_naming",
		"language",
	]:
		if field in data:
			doc.set(field, data[field])

	doc.setup_finished = 1
	doc.save()

	# 2. Seed Tree
	if not data.get("skip_seeding"):
		template_path = frappe.get_app_path("uph", f"setup/data/templates/{template_id}.json")
		if os.path.exists(template_path):
			with open(template_path) as f:
				structure = json.load(f)

			from uph.setup.install import PartyMasterSeeder

			seeder = PartyMasterSeeder(structure=structure, update_existing=data.get("update_existing"))
			seeder.run()

	return {"message": _("Setup Complete"), "success": True}
