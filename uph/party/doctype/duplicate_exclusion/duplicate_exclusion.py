# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class DuplicateExclusion(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        detected_on: DF.Datetime | None
        dismissed_by: DF.Link | None
        dismissed_on: DF.Date | None
        dismissed_reason: DF.SmallText | None
        normalized_name_1: DF.Data | None
        normalized_name_2: DF.Data | None
        party_1: DF.Link
        party_2: DF.Link
        similarity_score: DF.Float
        status: DF.Literal["Detected", "Dismissed", "Merged"]
    # end: auto-generated types
    """
    Duplicate Exclusion - Tracks duplicate detection candidates and
    party pairs that have been reviewed and dismissed/merged.

    Status flow: Detected -> Dismissed (manual review)
                 Detected -> Merged (via merge service)
    """

    def validate(self):
        self._validate_different_parties()
        self._normalize_party_order()
        self._validate_unique_exclusion()
        self._set_status_on_dismiss()

    def _validate_different_parties(self):
        """Ensure party_1 and party_2 are different."""
        if self.party_1 == self.party_2:
            frappe.throw(
                _("Party 1 and Party 2 must be different."),
                title=_("Invalid Exclusion"),
            )

    def _normalize_party_order(self):
        """
        Normalize party order to ensure consistent storage.
        Always store alphabetically: party_1 < party_2
        """
        if self.party_1 > self.party_2:
            self.party_1, self.party_2 = self.party_2, self.party_1
            # Swap normalized names too
            if self.normalized_name_1 or self.normalized_name_2:
                self.normalized_name_1, self.normalized_name_2 = (
                    self.normalized_name_2,
                    self.normalized_name_1,
                )

    def _validate_unique_exclusion(self):
        """Ensure the exclusion pair doesn't already exist with conflicting status."""
        existing = frappe.db.get_value(
            "Duplicate Exclusion",
            {
                "party_1": self.party_1,
                "party_2": self.party_2,
                "name": ["!=", self.name or ""],
            },
            ["name", "status"],
            as_dict=True,
        )
        if not existing:
            return

        if self.is_new():
            # If existing is Detected and we're dismissing, update existing instead
            if existing.status == "Detected" and self.status == "Dismissed":
                frappe.db.set_value(
                    "Duplicate Exclusion",
                    existing.name,
                    {
                        "status": "Dismissed",
                        "dismissed_by": frappe.session.user,
                        "dismissed_on": frappe.utils.today(),
                        "dismissed_reason": self.dismissed_reason,
                    },
                )
                frappe.throw(
                    _("Updated existing detection record to Dismissed."),
                    title=_("Record Updated"),
                    exc=frappe.DuplicateEntryError,
                )
            elif existing.status == self.status:
                frappe.throw(
                    _("This party pair already has a {0} record.").format(
                        existing.status
                    ),
                    title=_("Duplicate Exclusion Exists"),
                )

    def _set_status_on_dismiss(self):
        """Auto-set status to Dismissed when a reason is provided."""
        if self.dismissed_reason and self.status == "Detected":
            self.status = "Dismissed"
            if not self.dismissed_on:
                self.dismissed_on = frappe.utils.today()
            if not self.dismissed_by:
                self.dismissed_by = frappe.session.user


def is_excluded_pair(party_1: str, party_2: str) -> bool:
    """
    Check if a party pair has been excluded from duplicate detection.

    Args:
        party_1: First party master name
        party_2: Second party master name

    Returns:
        True if the pair is excluded (Dismissed or Merged)
    """
    # Normalize order
    if party_1 > party_2:
        party_1, party_2 = party_2, party_1

    return frappe.db.exists(
        "Duplicate Exclusion",
        {
            "party_1": party_1,
            "party_2": party_2,
            "status": ["in", ["Dismissed", "Merged"]],
        },
    )


def upsert_duplicate_candidate(
    party_1: str,
    party_2: str,
    similarity_score: float,
    normalized_name_1: str = "",
    normalized_name_2: str = "",
) -> str:
    """
    Insert or update a duplicate candidate record.
    Used by the background scanning job.

    Returns:
        Name of the Duplicate Exclusion record
    """
    # Normalize order
    if party_1 > party_2:
        party_1, party_2 = party_2, party_1
        normalized_name_1, normalized_name_2 = normalized_name_2, normalized_name_1

    existing = frappe.db.get_value(
        "Duplicate Exclusion",
        {"party_1": party_1, "party_2": party_2},
        ["name", "status"],
        as_dict=True,
    )

    if existing:
        # Don't overwrite Dismissed/Merged records
        if existing.status in ("Dismissed", "Merged"):
            return existing.name
        # Update score on existing Detected record
        frappe.db.set_value(
            "Duplicate Exclusion",
            existing.name,
            {
                "similarity_score": similarity_score,
                "normalized_name_1": normalized_name_1,
                "normalized_name_2": normalized_name_2,
                "detected_on": frappe.utils.now_datetime(),
            },
        )
        return existing.name

    doc = frappe.get_doc(
        {
            "doctype": "Duplicate Exclusion",
            "party_1": party_1,
            "party_2": party_2,
            "status": "Detected",
            "similarity_score": similarity_score,
            "normalized_name_1": normalized_name_1,
            "normalized_name_2": normalized_name_2,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name
