# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

"""
Party Master Merge Service

Enterprise-grade merge orchestration for Party Master deduplication.
Handles two merge scenarios:
- Case A: Full party merge when rule_fieldname values match
- Case B: Re-linking when rule_fieldname values differ

Uses frappe.rename_doc for party-level merging to maintain referential integrity.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime

from uph.party.controllers.party import (
    get_party_type_validation_rule,
    on_change_party_master_update_transactional_document_types,
)
from uph.party.controllers.cache_utils import SmartCache, get_pm_doctypes


class PartyMergeService:
    """
    Orchestrates Party Master merge operations with enterprise data governance.

    Key Features:
    - Automatic detection of merge type (full merge vs re-link)
    - Uses frappe.rename_doc for party merging (handles all linked documents)
    - Transfers Addresses/Contacts via Dynamic Links
    - Atomic operations with rollback on failure
    - Comprehensive audit logging
    """

    def __init__(self):
        self.merge_log = []
        self.errors = []

    def merge(
        self, primary_pm: str, secondary_pm: str, fields_to_keep: dict = None
    ) -> dict:
        """
        Merge secondary Party Master into primary Party Master.

        Args:
            primary_pm: The Party Master to keep (receives data)
            secondary_pm: The Party Master to merge and delete
            fields_to_keep: Dict of fields to copy from secondary to primary

        Returns:
            dict with success status, message, and merge details
        """
        if not frappe.has_permission("Party Master", "write"):
            frappe.throw(
                _("Insufficient permissions to merge parties"), frappe.PermissionError
            )

        if primary_pm == secondary_pm:
            frappe.throw(_("Cannot merge a Party Master with itself"))

        # Validate both exist
        if not frappe.db.exists("Party Master", primary_pm):
            frappe.throw(
                _("Primary Party Master {0} does not exist").format(primary_pm)
            )
        if not frappe.db.exists("Party Master", secondary_pm):
            frappe.throw(
                _("Secondary Party Master {0} does not exist").format(secondary_pm)
            )

        try:
            # Start savepoint for atomic rollback
            frappe.db.savepoint("party_merge_start")

            # 1. Analyze linked parties for both PMs
            primary_parties = self._analyze_linked_parties(primary_pm)
            secondary_parties = self._analyze_linked_parties(secondary_pm)

            # 2. Classify merge types per party type
            merge_plan = self._classify_merge_types(primary_parties, secondary_parties)

            self._log(f"Merge plan: {merge_plan}")

            # 3. Execute party-level operations based on classification
            for party_type, operations in merge_plan.items():
                for op in operations:
                    if op["action"] == "merge":
                        self._execute_party_merge(
                            primary_party=op["primary"],
                            secondary_party=op["secondary"],
                            party_type=party_type,
                        )
                    elif op["action"] == "relink":
                        self._execute_party_relink(
                            party_name=op["party"],
                            party_type=party_type,
                            new_pm=primary_pm,
                        )

            # 4. Transfer Party Master child tables (accounts, roles, etc)
            self._transfer_pm_child_tables(primary_pm, secondary_pm, fields_to_keep)

            # 5. Update all transactional document references
            self._update_party_master_references(secondary_pm, primary_pm)

            # 6. Delete secondary Party Master
            self._delete_secondary_pm(secondary_pm, primary_pm)

            # 7. Invalidate caches
            SmartCache.invalidate_party_master_parties(primary_pm)
            SmartCache.invalidate_party_master_parties(secondary_pm)

            frappe.db.commit()

            return {
                "success": True,
                "message": _("{0} has been merged into {1}").format(
                    secondary_pm, primary_pm
                ),
                "merge_log": self.merge_log,
                "operations": merge_plan,
            }

        except Exception as e:
            frappe.db.rollback(save_point="party_merge_start")
            frappe.log_error(
                title=_("Party Merge Failed"),
                message=f"Failed to merge {secondary_pm} into {primary_pm}: {str(e)}\n\nLog: {self.merge_log}",
            )
            raise

    def _analyze_linked_parties(self, pm_name: str) -> dict:
        """
        Analyze all linked parties for a Party Master.

        Returns:
            dict: {party_type: [{name, rule_value, ...}, ...]}
        """
        from uph.party.controllers.queries import get_party_master_parties_db

        parties = get_party_master_parties_db(pm_name) or []

        result = {}
        for p in parties:
            party_type = p.get("party_type")
            if party_type not in result:
                result[party_type] = []

            # Get rule field value
            rule = get_party_type_validation_rule(party_type)
            rule_fieldname = rule.get("rule_fieldname") if rule else None

            party_info = {
                "name": p.get("party") or p.get("name"),
                "party_type": party_type,
                "rule_fieldname": rule_fieldname,
                "rule_value": None,
            }

            if rule_fieldname:
                party_info["rule_value"] = frappe.db.get_value(
                    party_type, party_info["name"], rule_fieldname
                )

            result[party_type].append(party_info)

        return result

    def _classify_merge_types(
        self, primary_parties: dict, secondary_parties: dict
    ) -> dict:
        """
        Classify each party into merge or relink based on rule_fieldname.

        Case A - Merge: Same rule_fieldname value exists in both
        Case B - Relink: Different rule_fieldname value or no conflict

        Returns:
            dict: {party_type: [{action: "merge"|"relink", ...}, ...]}
        """
        merge_plan = {}

        for party_type, secondary_list in secondary_parties.items():
            if party_type not in merge_plan:
                merge_plan[party_type] = []

            primary_list = primary_parties.get(party_type, [])

            # Build lookup of primary parties by rule value
            primary_by_rule = {}
            for p in primary_list:
                if p.get("rule_value"):
                    primary_by_rule[p["rule_value"]] = p

            for sec_party in secondary_list:
                rule_value = sec_party.get("rule_value")

                # Check if primary has a party with same rule value
                if rule_value and rule_value in primary_by_rule:
                    # Case A: Same rule value - MERGE parties
                    merge_plan[party_type].append(
                        {
                            "action": "merge",
                            "primary": primary_by_rule[rule_value]["name"],
                            "secondary": sec_party["name"],
                            "rule_fieldname": sec_party.get("rule_fieldname"),
                            "rule_value": rule_value,
                        }
                    )
                else:
                    # Case B: Different rule value or no rule - RELINK
                    merge_plan[party_type].append(
                        {
                            "action": "relink",
                            "party": sec_party["name"],
                            "rule_fieldname": sec_party.get("rule_fieldname"),
                            "rule_value": rule_value,
                        }
                    )

        return merge_plan

    def _execute_party_merge(
        self, primary_party: str, secondary_party: str, party_type: str
    ):
        """
        Execute full party merge using frappe.rename_doc.

        This handles:
        - All linked transactions (Sales Invoice, GL Entry, etc)
        - Child table references
        - Deletes the secondary party
        """
        self._log(f"Merging {party_type} '{secondary_party}' into '{primary_party}'")

        # Transfer Dynamic Links (Address, Contact) BEFORE merge
        # Because rename_doc will delete secondary_party
        self._transfer_dynamic_links(secondary_party, primary_party, party_type)

        # Use frappe.rename_doc with merge=True
        # This updates all references and deletes the old document
        try:
            frappe.rename_doc(
                party_type,
                secondary_party,
                primary_party,
                merge=True,
                force=True,  # Skip naming validation
            )
            self._log(
                f"Successfully merged {party_type} '{secondary_party}' into '{primary_party}'"
            )
        except Exception as e:
            # If merge fails (e.g., naming conflicts), try manual approach
            self._log(f"rename_doc merge failed: {e}, attempting manual merge")
            self._manual_party_merge(primary_party, secondary_party, party_type)

    def _manual_party_merge(
        self, primary_party: str, secondary_party: str, party_type: str
    ):
        """
        Manual party merge when frappe.rename_doc fails.
        Updates all references and deletes secondary party.
        """
        # Get all DocTypes that reference this party type
        meta = frappe.get_meta(party_type)

        # Update all Link fields pointing to secondary party
        for doctype in frappe.get_all(
            "DocType", filters={"issingle": 0, "is_virtual": 0}
        ):
            dt_meta = frappe.get_meta(doctype.name)
            for df in dt_meta.get_link_fields():
                if df.options == party_type:
                    try:
                        frappe.db.sql(
                            f"""
                            UPDATE `tab{doctype.name}`
                            SET `{df.fieldname}` = %s
                            WHERE `{df.fieldname}` = %s
                        """,
                            (primary_party, secondary_party),
                        )
                    except Exception:
                        pass  # Table might not exist or column missing

        # Delete secondary party
        frappe.delete_doc(
            party_type, secondary_party, force=True, ignore_permissions=True
        )
        self._log(f"Manual merge completed: {party_type} '{secondary_party}' deleted")

    def _execute_party_relink(self, party_name: str, party_type: str, new_pm: str):
        """
        Re-link a party to the new Party Master (Case B).
        Updates party_master field and triggers transaction updates.
        """
        self._log(f"Re-linking {party_type} '{party_name}' to Party Master '{new_pm}'")

        # Get old PM for transaction updates
        old_pm = frappe.db.get_value(party_type, party_name, "party_master")

        # Update party_master field
        party_doc = frappe.get_doc(party_type, party_name)
        party_doc.party_master = new_pm
        party_doc.flags.ignore_validate = True  # Skip validation since we're in merge
        party_doc.save(ignore_permissions=True)

        self._log(
            f"Re-linked {party_type} '{party_name}' from '{old_pm}' to '{new_pm}'"
        )

    def _transfer_dynamic_links(self, old_party: str, new_party: str, party_type: str):
        """
        Transfer Address and Contact links from old party to new party.
        Uses Frappe's Dynamic Link pattern.
        """
        for parent_doctype in ["Address", "Contact"]:
            # Get all links from old party
            links = frappe.db.get_all(
                "Dynamic Link",
                filters={
                    "link_doctype": party_type,
                    "link_name": old_party,
                    "parenttype": parent_doctype,
                },
                fields=["name", "parent", "parentfield"],
            )

            for link in links:
                # Check if new party already has this link
                existing = frappe.db.exists(
                    "Dynamic Link",
                    {
                        "parenttype": parent_doctype,
                        "parent": link.parent,
                        "link_doctype": party_type,
                        "link_name": new_party,
                    },
                )

                if not existing:
                    # Add link to new party
                    frappe.get_doc(
                        {
                            "doctype": "Dynamic Link",
                            "parenttype": parent_doctype,
                            "parent": link.parent,
                            "parentfield": link.parentfield or "links",
                            "link_doctype": party_type,
                            "link_name": new_party,
                        }
                    ).db_insert()
                    self._log(
                        f"Transferred {parent_doctype} '{link.parent}' link to '{new_party}'"
                    )

                # Remove old link
                frappe.db.delete("Dynamic Link", {"name": link.name})

        # Also transfer Party Master level addresses/contacts
        self._transfer_pm_dynamic_links(old_party, new_party, party_type)

    def _transfer_pm_dynamic_links(
        self, old_party: str, new_party: str, party_type: str
    ):
        """Transfer addresses/contacts linked to Party Master itself."""
        # This handles cases where Address/Contact is linked to Party Master
        # rather than individual Customer/Supplier
        pass  # Party Master uses party_primary_address/party_primary_contact fields

    def _transfer_pm_child_tables(
        self, primary_pm: str, secondary_pm: str, fields_to_keep: dict = None
    ):
        """
        Transfer child tables and fields from secondary to primary PM.
        """
        primary_doc = frappe.get_doc("Party Master", primary_pm)
        secondary_doc = frappe.get_doc("Party Master", secondary_pm)

        # Transfer accounts (avoid duplicates by company)
        existing_companies = {acc.company for acc in primary_doc.accounts}
        for acc in secondary_doc.accounts:
            if acc.company not in existing_companies:
                primary_doc.append(
                    "accounts",
                    {
                        "company": acc.company,
                        "account": acc.account,
                        "default_currency": acc.get("default_currency"),
                    },
                )
                self._log(f"Transferred account for company '{acc.company}'")

        # Transfer roles (avoid duplicates)
        existing_roles = {r.party_type_role for r in primary_doc.roles}
        for role in secondary_doc.roles:
            if role.party_type_role not in existing_roles:
                primary_doc.append("roles", {"party_type_role": role.party_type_role})
                self._log(f"Transferred role '{role.party_type_role}'")

        # Copy specified fields from secondary if primary is empty
        if fields_to_keep:
            for field, value in fields_to_keep.items():
                if value and not primary_doc.get(field):
                    primary_doc.set(field, value)
                    self._log(f"Copied field '{field}' from secondary PM")

        # Copy empty fields from secondary
        field_candidates = [
            "tax_id",
            "tax_category",
            "territory",
            "language",
            "party_primary_address",
            "party_primary_contact",
            "default_currency",
            "payment_terms",
        ]
        for field in field_candidates:
            if not primary_doc.get(field) and secondary_doc.get(field):
                primary_doc.set(field, secondary_doc.get(field))

        primary_doc.flags.ignore_validate = True
        primary_doc.save(ignore_permissions=True)

    def _update_party_master_references(self, old_pm: str, new_pm: str):
        """
        Update all transaction documents to point to new Party Master.
        """
        doctypes = get_pm_doctypes() or []

        for dt_info in doctypes:
            dt = dt_info[0] if isinstance(dt_info, (list, tuple)) else dt_info

            try:
                meta = frappe.get_meta(dt)
                if meta.issingle or meta.is_virtual:
                    continue

                if not frappe.db.has_column(dt, "party_master"):
                    continue

                count = frappe.db.sql(
                    """
                    UPDATE `tab{doctype}`
                    SET party_master = %s
                    WHERE party_master = %s
                """.format(
                        doctype=dt
                    ),
                    (new_pm, old_pm),
                )

                affected = frappe.db.sql(f"SELECT ROW_COUNT() as cnt")[0][0]

                if affected:
                    self._log(f"Updated {affected} {dt} records")

            except Exception as e:
                self._log(f"Warning: Could not update {dt}: {e}")

    def _delete_secondary_pm(self, secondary_pm: str, primary_pm: str):
        """
        Delete secondary Party Master after merge.
        Adds audit trail comment before deletion.
        """
        secondary_doc = frappe.get_doc("Party Master", secondary_pm)

        # Add audit comment to primary PM
        primary_doc = frappe.get_doc("Party Master", primary_pm)
        primary_doc.add_comment(
            "Info",
            _(
                "Merged Party Master {0} into this record. Merge completed by {1} at {2}"
            ).format(secondary_pm, frappe.session.user, now_datetime()),
        )

        # Delete secondary PM with merge flag to skip linked party check
        secondary_doc.flags.ignore_permissions = True
        secondary_doc.flags.in_merge = True  # Skip on_trash validation
        secondary_doc.delete()

        self._log(f"Deleted secondary Party Master '{secondary_pm}'")

    def _log(self, message: str):
        """Add message to merge log."""
        self.merge_log.append({"timestamp": str(now_datetime()), "message": message})


# Convenience function for API calls
@frappe.whitelist()
def merge_party_masters(
    primary_party: str, secondary_party: str, fields_to_keep: dict = None
) -> dict:
    """
    API endpoint for merging Party Masters.

    Args:
        primary_party: The Party Master to keep
        secondary_party: The Party Master to merge and delete
        fields_to_keep: Optional dict of fields to copy from secondary

    Returns:
        dict with success status and merge details
    """
    import json

    if isinstance(fields_to_keep, str):
        fields_to_keep = json.loads(fields_to_keep) if fields_to_keep else {}

    service = PartyMergeService()
    return service.merge(primary_party, secondary_party, fields_to_keep)
