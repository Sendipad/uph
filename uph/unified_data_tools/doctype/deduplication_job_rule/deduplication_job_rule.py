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

        custom_normalizer: DF.Link | None
        custom_scorer: DF.Link | None
        field_path: DF.Autocomplete
        field_type: DF.ReadOnly | None
        is_critical: DF.Check
        normalizer: DF.Literal["", "Strict Arabic", "Clean Text", "Trim Whitespace", "Lowercase", "Uppercase", "Remove Special Chars", "Phone Format (E164)", "Email Normalize", "Address Standardization", "Numeric Only", "Alphanumeric Only", "Date to ISO", "Custom Normalizer"]
        normalizer_params: DF.JSON | None
        operator: DF.Literal["Exact Match", "Fuzzy Match", "Contains", "Starts With", "Ends With", "Exact Date", "Within Days", "Exact Number", "Within Range", "Percent Difference", "Any Item Exists", "All Items Exist", "Exact Sequence", "Both Checked", "Syntax Match", "Phonetic Match"]
        parent: DF.Data
        parentfield: DF.Data
        parenttype: DF.Data
        scorer: DF.Literal["Levenshtein Distance", "Jaro-Winkler", "Cosine Similarity", "Jaccard Index", "Token Set Ratio", "Partial Ratio", "Soundex", "Metaphone", "Double Metaphone", "Custom Scorer"]
        scorer_params: DF.JSON | None
        tolerance: DF.Float
        use_in_filter: DF.Check
        weight: DF.Float
    # end: auto-generated types
    pass
