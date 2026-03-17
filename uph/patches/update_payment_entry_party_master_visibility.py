import frappe

from uph.party.utils import setup_party_master_custom_fields


def execute():
	"""
	Ensure Party Master custom fields are updated after migration,
	including Payment Entry visibility rules.
	"""
	logger = frappe.logger("uph.patches")
	try:
		setup_party_master_custom_fields()
	except Exception:
		logger.warning("Custom fields update encountered an issue")

	try:
		from uph.party.doctype.party_master_settings.party_master_settings import (
			create_party_master_on_document_types,
		)

		create_party_master_on_document_types()
	except Exception:
		logger.warning("Settings-based field update encountered an issue")
