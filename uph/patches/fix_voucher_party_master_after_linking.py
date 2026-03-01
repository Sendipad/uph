# Copyright (c) 2026, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

"""
Fix voucher party_master after linking.

Historical bug: `create_party_master_from_unlinked_role` used `db_set()`
which bypassed ORM hooks, so the background job to update `party_master`
on existing vouchers was never triggered.

This patch retroactively updates vouchers where the party (Customer/Supplier)
has a `party_master` set but the voucher's `party_master` is still NULL.
"""

import frappe
from frappe.utils import now_datetime
from pypika.functions import Coalesce
from frappe.query_builder.functions import Count


def execute():
    settings_doc = frappe.get_doc("Party Master Settings")
    if not settings_doc.document_types:
        return

    party_types_conf = settings_doc.party_types or []
    party_type_list = [pt.party_type for pt in party_types_conf if pt.party_type]
    if not party_type_list:
        return

    total_updated = 0

    for party_type in party_type_list:
        if not frappe.db.exists("DocType", party_type):
            continue
        meta = frappe.get_meta(party_type)
        if not meta.has_field("party_master"):
            continue

        # Get all parties that have a party_master set
        linked_parties = frappe.get_all(
            party_type,
            filters={"party_master": ["is", "set"]},
            fields=["name", "party_master"],
            limit_page_length=0,
        )

        if not linked_parties:
            continue

        party_pm_map = {p.name: p.party_master for p in linked_parties}

        # For each configured transactional doctype, update vouchers
        for dt_conf in settings_doc.document_types:
            if not dt_conf.party_fieldname:
                continue
            if dt_conf.party_type and dt_conf.party_type != party_type:
                continue
            if dt_conf.is_dynamic_party_type and not dt_conf.party_type_fieldname:
                continue

            doctype = dt_conf.document_type
            if not frappe.db.exists("DocType", doctype):
                continue

            doc_meta = frappe.get_meta(doctype)
            if doc_meta.issingle:
                continue

            if not doc_meta.has_field("party_master"):
                continue

            party_fieldname = dt_conf.party_fieldname
            party_type_fieldname = dt_conf.get("party_type_fieldname", None)

            tbl = frappe.qb.DocType(doctype)

            # Process in batches by party
            for party_name, party_master in party_pm_map.items():
                conditions = tbl[party_fieldname] == party_name
                conditions &= Coalesce(tbl.party_master, "") == ""

                if party_type_fieldname:
                    conditions &= tbl[party_type_fieldname] == party_type

                # Skip cancelled docs
                if doc_meta.has_field("docstatus"):
                    conditions &= tbl.docstatus < 2

                # Count first
                count_result = (
                    frappe.qb.from_(tbl)
                    .select(Count("*").as_("cnt"))
                    .where(conditions)
                    .run(as_dict=True)
                )
                count = count_result[0]["cnt"] if count_result else 0

                if count > 0:
                    frappe.qb.update(tbl).set(tbl.party_master, party_master).where(
                        conditions
                    ).run()

                    total_updated += count

                    frappe.logger("uph").info(
                        f"Patch fix_voucher_pm: Updated {count} {doctype} "
                        f"records for {party_type} {party_name} → {party_master}"
                    )

        frappe.db.commit()

    if total_updated:
        frappe.logger("uph").info(
            f"Patch fix_voucher_pm: Total {total_updated} voucher records updated"
        )
        frappe.msgprint(
            f"Migration patch: Updated party_master on {total_updated} voucher records.",
            alert=True,
        )
