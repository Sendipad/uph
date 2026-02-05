# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PartyRelationship(Document):
    """
    Party Relationship - Manages N-to-N relationships between Party Masters.

    Similar to Oracle TCA Party Relationships, this allows complex relationship
    modeling like Parent-Subsidiary, Partner, Agent, Distributor, etc.

    Features:
    - Prevents self-referential relationships
    - Validates date ranges (end_date >= start_date)
    - Auto-creates reverse relationship if relationship type has one defined
    - Checks for duplicate relationships
    - Status-based lifecycle management
    """

    def validate(self):
        self._validate_not_self_referential()
        self._validate_date_range()
        self._validate_unique_relationship()
        self._validate_ownership_percentage()

    def after_insert(self):
        self._create_reverse_relationship()

    def on_trash(self):
        self._delete_reverse_relationship()

    def _validate_not_self_referential(self):
        """Prevent a party from having a relationship with itself."""
        if self.subject_party == self.object_party:
            frappe.throw(
                _("A party cannot have a relationship with itself."),
                title=_("Invalid Relationship"),
            )

    def _validate_date_range(self):
        """Ensure end_date is after start_date if both are set."""
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                frappe.throw(
                    _("End Date cannot be before Start Date."),
                    title=_("Invalid Date Range"),
                )

    def _validate_unique_relationship(self):
        """
        Prevent duplicate relationships between the same parties.
        A duplicate is defined as same subject, object, and relationship type.
        """
        existing = frappe.db.exists(
            "Party Relationship",
            {
                "subject_party": self.subject_party,
                "relationship_type": self.relationship_type,
                "object_party": self.object_party,
                "name": ["!=", self.name or ""],
                "status": ["!=", "Terminated"],
            },
        )
        if existing:
            frappe.throw(
                _("A {0} relationship already exists between {1} and {2}.").format(
                    frappe.bold(self.relationship_type),
                    frappe.bold(self.subject_party),
                    frappe.bold(self.object_party),
                ),
                title=_("Duplicate Relationship"),
            )

    def _validate_ownership_percentage(self):
        """Validate ownership percentage is within valid range."""
        if self.ownership_percentage:
            if self.ownership_percentage < 0 or self.ownership_percentage > 100:
                frappe.throw(
                    _("Ownership percentage must be between 0 and 100."),
                    title=_("Invalid Percentage"),
                )

    def _create_reverse_relationship(self):
        """
        Auto-create reverse relationship if the relationship type has one defined.
        For example: If A is 'Parent Company' of B, create B is 'Subsidiary' of A.
        """
        if frappe.flags.in_reverse_relationship_creation:
            return

        rel_type = frappe.get_cached_doc(
            "Party Relationship Type", self.relationship_type
        )
        if not rel_type.reverse_relationship_type:
            return

        # Check if reverse already exists
        existing_reverse = frappe.db.exists(
            "Party Relationship",
            {
                "subject_party": self.object_party,
                "relationship_type": rel_type.reverse_relationship_type,
                "object_party": self.subject_party,
                "status": ["!=", "Terminated"],
            },
        )
        if existing_reverse:
            return

        try:
            frappe.flags.in_reverse_relationship_creation = True
            reverse_rel = frappe.get_doc(
                {
                    "doctype": "Party Relationship",
                    "subject_party": self.object_party,
                    "relationship_type": rel_type.reverse_relationship_type,
                    "object_party": self.subject_party,
                    "status": self.status,
                    "start_date": self.start_date,
                    "end_date": self.end_date,
                    "ownership_percentage": self.ownership_percentage,
                    "notes": _("Auto-created reverse relationship from {0}").format(
                        self.name
                    ),
                }
            )
            reverse_rel.insert(ignore_permissions=True)
        finally:
            frappe.flags.in_reverse_relationship_creation = False

    def _delete_reverse_relationship(self):
        """Delete reverse relationship when this one is deleted."""
        if frappe.flags.in_reverse_relationship_deletion:
            return

        rel_type = frappe.get_cached_doc(
            "Party Relationship Type", self.relationship_type
        )
        if not rel_type.reverse_relationship_type:
            return

        reverse_name = frappe.db.get_value(
            "Party Relationship",
            {
                "subject_party": self.object_party,
                "relationship_type": rel_type.reverse_relationship_type,
                "object_party": self.subject_party,
            },
        )

        if reverse_name:
            try:
                frappe.flags.in_reverse_relationship_deletion = True
                frappe.delete_doc(
                    "Party Relationship", reverse_name, ignore_permissions=True
                )
            finally:
                frappe.flags.in_reverse_relationship_deletion = False


@frappe.whitelist()
def get_party_relationships(party_master: str, direction: str = "all"):
    """
    Get all relationships for a party master.

    Args:
        party_master: Name of the Party Master
        direction: 'outgoing' (as subject), 'incoming' (as object), or 'all'

    Returns:
        List of relationship records
    """
    filters = {"status": ["!=", "Terminated"]}

    if direction == "outgoing":
        filters["subject_party"] = party_master
    elif direction == "incoming":
        filters["object_party"] = party_master
    else:
        # All relationships
        return frappe.get_all(
            "Party Relationship",
            filters={"status": ["!=", "Terminated"]},
            or_filters={"subject_party": party_master, "object_party": party_master},
            fields=[
                "name",
                "subject_party",
                "relationship_type",
                "object_party",
                "status",
                "start_date",
                "end_date",
                "ownership_percentage",
            ],
            order_by="creation desc",
        )

    return frappe.get_all(
        "Party Relationship",
        filters=filters,
        fields=[
            "name",
            "subject_party",
            "relationship_type",
            "object_party",
            "status",
            "start_date",
            "end_date",
            "ownership_percentage",
        ],
        order_by="creation desc",
    )


@frappe.whitelist()
def get_related_parties(party_master: str, relationship_type: str = None):
    """
    Get all parties related to the given party master.

    Args:
        party_master: Name of the Party Master
        relationship_type: Optional filter by relationship type

    Returns:
        List of related party names with relationship details
    """
    filters = {"subject_party": party_master, "status": "Active"}
    if relationship_type:
        filters["relationship_type"] = relationship_type

    relationships = frappe.get_all(
        "Party Relationship",
        filters=filters,
        fields=["object_party", "relationship_type", "ownership_percentage"],
    )

    return relationships
