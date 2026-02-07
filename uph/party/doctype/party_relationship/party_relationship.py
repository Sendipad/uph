# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PartyRelationship(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        authority_ref: DF.Data | None
        consolidate_financials: DF.Check
        credit_allocation: DF.Currency
        end_date: DF.Date | None
        is_guarantor: DF.Check
        is_primary: DF.Check
        notes: DF.SmallText | None
        object_party: DF.Link
        ownership_percentage: DF.Percent
        relationship_type: DF.Link
        start_date: DF.Date | None
        status: DF.Literal["Active", "Inactive", "Terminated"]
        subject_party: DF.Link
        termination_reason: DF.Data | None
    # end: auto-generated types
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
        self._validate_circular_dependency()

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

    def _validate_circular_dependency(self):
        """
        Check for circular dependencies if the relationship type requires it.
        Uses BFS to traverse the relationship graph.
        """
        rel_type = frappe.get_cached_doc(
            "Party Relationship Type", self.relationship_type
        )
        if not rel_type.prevent_circular:
            return

        # We are proposing A -> B. Check if B leads back to A.
        seen = set()
        queue = [self.object_party]

        while queue:
            current = queue.pop(0)
            if current == self.subject_party:
                frappe.throw(
                    _(
                        "Circular dependency detected: {0} is already related to {1} via {2}."
                    ).format(
                        frappe.bold(self.subject_party),
                        frappe.bold(self.object_party),
                        frappe.bold(self.relationship_type),
                    ),
                    title=_("Circular Relationship"),
                )

            if current in seen:
                continue
            seen.add(current)

            # Find all parties that 'current' relates to with the same type
            # i.e. current -> next
            next_parties = frappe.get_all(
                "Party Relationship",
                filters={
                    "subject_party": current,
                    "relationship_type": self.relationship_type,
                    "status": "Active",
                },
                pluck="object_party",
            )
            queue.extend(next_parties)

    def _create_reverse_relationship(self):
        """
        Auto-create reverse relationship if one is defined or if symmetric.
        """
        if frappe.flags.in_reverse_relationship_creation:
            return

        rel_type = frappe.get_cached_doc(
            "Party Relationship Type", self.relationship_type
        )

        target_type = None
        if rel_type.is_symmetric:
            target_type = self.relationship_type
        elif rel_type.reverse_relationship_type:
            target_type = rel_type.reverse_relationship_type

        if not target_type:
            return

        # Check if reverse already exists
        existing_reverse = frappe.db.exists(
            "Party Relationship",
            {
                "subject_party": self.object_party,
                "relationship_type": target_type,
                "object_party": self.subject_party,
                "status": ["!=", "Terminated"],
            },
        )
        if existing_reverse:
            return

        try:
            frappe.flags.in_reverse_relationship_creation = True
            new_doc = frappe.new_doc("Party Relationship")
            new_doc.update(
                {
                    "subject_party": self.object_party,
                    "relationship_type": target_type,
                    "object_party": self.subject_party,
                    "status": self.status,
                    "start_date": self.start_date,
                    "end_date": self.end_date,
                    "ownership_percentage": self.ownership_percentage,
                    "notes": _("Auto-created reciprocal relationship from {0}").format(
                        self.name
                    ),
                    "is_guarantor": self.is_guarantor if rel_type.is_symmetric else 0,
                    "consolidate_financials": (
                        self.consolidate_financials if rel_type.is_symmetric else 0
                    ),
                }
            )
            new_doc.insert(ignore_permissions=True)
        finally:
            frappe.flags.in_reverse_relationship_creation = False

    def _delete_reverse_relationship(self):
        """Delete reverse relationship when this one is deleted."""
        if frappe.flags.in_reverse_relationship_deletion:
            return

        rel_type = frappe.get_cached_doc(
            "Party Relationship Type", self.relationship_type
        )

        target_type = None
        if rel_type.is_symmetric:
            target_type = self.relationship_type
        elif rel_type.reverse_relationship_type:
            target_type = rel_type.reverse_relationship_type

        if not target_type:
            return

        reverse_name = frappe.db.get_value(
            "Party Relationship",
            {
                "subject_party": self.object_party,
                "relationship_type": target_type,
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
