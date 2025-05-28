# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class DeduplicationJobRule(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        field_path: DF.Autocomplete
        field_type: DF.ReadOnly | None
        fuzzy_method: DF.Literal["Ratio", "Partial Ratio", "Token Sort Ratio", "Token Set Ratio", "QRatio", "WRatio"]
        operator: DF.Literal["Exact Match", "Fuzzy Match", "Contains", "Starts With", "Ends With", "Exact Date", "Within Days", "Exact Number", "Within Range", "Percent Difference", "Any Item Exists", "All Items Exist", "Exact Sequence", "Both Checked", "Syntax Match"]
        parent: DF.Data
        parentfield: DF.Data
        parenttype: DF.Data
        tolerance: DF.Float
        use_in_filter: DF.Check
        weight: DF.Float
    # end: auto-generated types
    pass
