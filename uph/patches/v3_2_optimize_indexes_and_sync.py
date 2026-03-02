import frappe
from uph.setup.install import create_custom_indices


def execute():
    """
    1. Ensure indexes are present to prevent deadlocks.
    2. Sync missing party_master fields using index-friendly queries.
    """
    frappe.logger("uph").info("Starting Patch: v3_2_optimize_indexes_and_sync")

    # Step 1: Optimize Indexes
    create_custom_indices()

    # Step 2: Sync missing party_master data
    settings_doc = frappe.get_cached_doc("Party Master Settings")
    if not settings_doc.document_types:
        return

    party_types = [pt.party_type for pt in settings_doc.party_types if pt.party_type]
    total_updated = 0

    for pt_name in party_types:
        if not frappe.db.exists("DocType", pt_name):
            continue

        # Get parties with party_master
        linked_parties = frappe.get_all(
            pt_name,
            filters={"party_master": ["!=", ""]},
            fields=["name", "party_master"],
            limit_page_length=0,
        )

        if not linked_parties:
            continue

        for pt_doc in linked_parties:
            # For each doctype where this party type might appear
            for d in settings_doc.document_types:
                if d.party_type and d.party_type != pt_name:
                    continue
                if not d.party_fieldname:
                    continue

                doctype = d.document_type
                if not frappe.db.exists("DocType", doctype):
                    continue

                meta = frappe.get_meta(doctype)
                if meta.issingle or not meta.has_field("party_master"):
                    continue

                # Run the optimized update from the controller
                # This uses the non-blocking isnull() / == '' logic implemented in party.py
                from uph.party.controllers.party import (
                    _update_party_master_field_on_exists_transactional_document_types,
                )

                count = (
                    _update_party_master_field_on_exists_transactional_document_types(
                        doctype=doctype,
                        party_fieldname=d.party_fieldname,
                        party=pt_doc.name,
                        party_master=pt_doc.party_master,
                        party_type=pt_name,
                        party_type_fieldname=d.get("party_type_fieldname"),
                        counts_only=False,
                    )
                )

                if count:
                    total_updated += count
                    frappe.logger("uph").info(
                        f"Fixed {count} records in {doctype} for {pt_name} {pt_doc.name}"
                    )

        frappe.db.commit()

    if total_updated:
        frappe.msgprint(
            f"Safe Patch: Synchronized {total_updated} transactional records with Party Master.",
            alert=True,
        )
