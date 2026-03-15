import frappe

from uph.party.utils import setup_party_master_custom_fields


def execute():
	"""
	IDEMPOTENT: Setup custom fields for party master integration.
	Safe to run multiple times - setup_party_master_custom_fields handles duplicates.
	"""
	logger = frappe.logger("uph.patches")
	try:
		setup_party_master_custom_fields()
		logger.info("Party master custom fields setup completed")
	except Exception as e:
		# Log error but don't fail patch (fields might already exist)
		frappe.log_error(
			title="Party Master Custom Fields Setup Warning",
			message=f"Error during custom fields setup: {e!s}",
		)
		logger.warning("Custom fields setup encountered an issue (may already exist): %s", str(e))
