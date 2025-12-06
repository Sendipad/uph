import frappe
from frappe.utils import getdate, add_days
from uph.controllers.mdm.utils import get_field_value

def get_blocking_filters(doc, conditions):
    """
    Generate SQL filters to fetch potential candidates.
    Uses OR logic: if ANY condition matches (loosely), it's a candidate.
    """
    or_filters = []
    
    for condition in conditions:
        # For blocking, we only look at parent fields for now to avoid complex joins in get_all
        # If dotted path, we skip optimization or handle if possible.
        # Current limitation: get_all doesn't support child table filters easily without joins.
        # We'll skip child table fields for blocking unless we implement custom SQL.
        if "." in condition.field:
            continue
        
        # Get the field value
        # If the field is a normalized field (e.g., normalized_party_name),
        # we need to derive it from the source field if it's not already set
        field_value = doc.get(condition.field)
        
        # Handle normalized fields: if field starts with "normalized_" and is empty,
        # try to derive it from the source field
        if not field_value and condition.field.startswith("normalized_"):
            source_field = condition.field.replace("normalized_", "", 1)
            source_value = doc.get(source_field)
            if source_value:
                from uph.controllers.mdm.normalization import normalize_text
                field_value = normalize_text(source_value)
        
        if not field_value:
            continue

        if condition.check_type == "Exact Match":
            or_filters.append([condition.field, "=", field_value])
        
        elif condition.check_type == "Date Range":
            window = condition.window_days or 0
            date_val = getdate(field_value)
            start_date = add_days(date_val, -window)
            end_date = add_days(date_val, window)
            or_filters.append([condition.field, "between", [start_date, end_date]])
        
        elif condition.check_type == "Fuzzy Match":
            # Prefix blocking: First 3 chars
            val = str(field_value)
            if len(val) >= 3:
                or_filters.append([condition.field, "like", val[:3] + "%"])
            else:
                # If short, exact match
                or_filters.append([condition.field, "=", val])
                
    frappe.errprint(f"Generated blocking filters: {or_filters}")
    return or_filters
