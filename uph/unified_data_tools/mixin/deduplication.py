import frappe
from frappe.model.document import Document
from uph.unified_data_tools.mdm.validator import DeduplicationValidator


class DeduplicationMixin(Document):
    """To be inherited by any doctype that needs deduplication checks"""

    def validate(self):
        super().validate()  # Call parent validation first

        if self._should_skip_deduplication():
            return

        validator = DeduplicationValidator(self.doctype)
        validator.validate(self)

    def _should_skip_deduplication(self):
        """Conditions where deduplication should be skipped"""
        return (
            frappe.flags.in_import
            or frappe.flags.in_migrate
            or not self._has_deduplication_jobs()
        )

    def _has_deduplication_jobs(self):
        """Check if active jobs exist for this doctype"""
        return bool(
            frappe.db.exists(
                "Deduplication Job", {"document_type": self.doctype, "is_active": 1}
            )
        )
