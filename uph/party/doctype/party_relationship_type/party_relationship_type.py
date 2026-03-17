# Copyright (c) 2026, Abdo Ruzaqi and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class PartyRelationshipType(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		category: DF.Literal["Structural", "Commercial", "Compliance", "Social", "Other"]
		description: DF.SmallText | None
		is_enabled: DF.Check
		is_hierarchical: DF.Check
		is_symmetric: DF.Check
		prevent_circular: DF.Check
		relationship_type_name: DF.Data
		reverse_relationship_type: DF.Link | None
	# end: auto-generated types
	"""
    Party Relationship Type - Lookup table for relationship categories.

    Examples: Parent Company, Subsidiary, Partner, Agent, Distributor

    Features:
    - Optional reverse relationship type for bidirectional relationships
    - Hierarchical flag for ownership/control relationships
    """

	pass
