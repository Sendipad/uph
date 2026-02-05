# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class DuplicateExclusion(Document):
    """
    Duplicate Exclusion - Tracks party pairs that have been reviewed
    and marked as non-duplicates.

    This prevents the same pair from appearing in duplicate detection
    repeatedly after being dismissed.
    """

    def validate(self):
        self._validate_different_parties()
        self._normalize_party_order()
        self._validate_unique_exclusion()

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

    def _validate_unique_exclusion(self):
        """Ensure the exclusion pair doesn't already exist."""
        existing = frappe.db.exists(
            "Duplicate Exclusion",
            {
                "party_1": self.party_1,
                "party_2": self.party_2,
                "name": ["!=", self.name or ""],
            },
        )
        if existing:
            frappe.throw(
                _(
                    "This party pair has already been excluded from duplicate detection."
                ),
                title=_("Duplicate Exclusion Exists"),
            )


def is_excluded_pair(party_1: str, party_2: str) -> bool:
    """
    Check if a party pair has been excluded from duplicate detection.

    Args:
        party_1: First party master name
        party_2: Second party master name

    Returns:
        True if the pair is excluded
    """
    # Normalize order
    if party_1 > party_2:
        party_1, party_2 = party_2, party_1

    return frappe.db.exists(
        "Duplicate Exclusion", {"party_1": party_1, "party_2": party_2}
    )
