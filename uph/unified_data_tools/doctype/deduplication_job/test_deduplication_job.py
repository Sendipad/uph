# Copyright (c) 2025, Abdo Mohammed Ruzaqi and Contributors
# See license.txt
import frappe
from frappe.tests.utils import FrappeTestCase
from uph.unified_data_tools.doctype.deduplication_job.deduplication_job import (
    get_doctype_with_validation_deduplication_jobs,
)


class TestDeduplicationJob(FrappeTestCase):
    def test_deduplication_cache_clear():
        jobs = get_doctype_with_validation_deduplication_jobs()
        assert isinstance(jobs, dict)

        # Add new job
        job = frappe.get_doc(
            {
                "doctype": "Deduplication Job",
                "document_type": "Contact",
                "validate_on_form_save": 1,
                "active": 1,
                "schedule": "Manual",
            }
        ).insert()

        job.clear_cache()
        jobs_after = get_doctype_with_validation_deduplication_jobs()
        assert job.name in jobs_after.get("Contact", [])
