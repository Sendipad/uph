# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class PartyRelationshipType(Document):
    """
    Party Relationship Type - Lookup table for relationship categories.

    Examples: Parent Company, Subsidiary, Partner, Agent, Distributor

    Features:
    - Optional reverse relationship type for bidirectional relationships
    - Hierarchical flag for ownership/control relationships
    """

    pass
