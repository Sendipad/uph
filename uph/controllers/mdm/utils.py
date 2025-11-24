import frappe

def get_field_value(doc, field_path):
    """
    Get value from a document using a dotted path.
    Supports parent fields (e.g. "item_code") and child table fields (e.g. "items.item_code").
    Returns a list of values for child table fields, or a single value for parent fields.
    """
    if "." not in field_path:
        return doc.get(field_path)
    
    parts = field_path.split(".")
    parent_field = parts[0]
    child_field = parts[1]
    
    # Check if it's a child table
    if isinstance(doc.get(parent_field), list):
        values = []
        for row in doc.get(parent_field):
            val = row.get(child_field)
            if val:
                values.append(val)
        return values
    
    # Fallback for non-list dotted path (if any)
    return doc.get(parent_field)
