import frappe
from uph.controllers.mdm.engine import DuplicateFinder

@frappe.whitelist()
def test_rule(rule_name, doc_name):
    """
    Test a Data Quality Rule against a specific document.
    Returns the potential duplicates found.
    """
    if not rule_name or not doc_name:
        frappe.throw("Rule Name and Document Name are required.")
        
    rule = frappe.get_doc("Data Quality Rule", rule_name)
    doc = frappe.get_doc(rule.document_type, doc_name)
    
    # Initialize DuplicateFinder with the document and rule name
    finder = DuplicateFinder(doc, rule_name)
    
    # Debug: Log what we're searching for
    frappe.errprint(f"Testing rule '{rule_name}' against document '{doc_name}'")
    frappe.errprint(f"Document party_name: {doc.get('party_name')}")
    frappe.errprint(f"Document normalized_party_name: {doc.get('normalized_party_name')}")
    
    # Run the check
    duplicates = finder.find_duplicates()
    
    frappe.errprint(f"Found {len(duplicates)} duplicates")
    
    # Format results for frontend
    results = []
    for dup in duplicates:
        # dup is a dict: {'docname': '...', 'score': ...}
        dup_doc_name = dup.get("docname")
        score = dup.get("score")
        
        # Fetch title for display
        title = dup_doc_name
        try:
            title = frappe.db.get_value(rule.document_type, dup_doc_name, "title") or dup_doc_name
        except Exception:
            pass
            
        results.append({
            "name": dup_doc_name,
            "title": title,
            "score": score,
            "rule": rule_name
        })
        
    return results

@frappe.whitelist()
def test_rule_with_data(rule_name, test_data):
    """
    Test a Data Quality Rule against custom test data (not an existing document).
    Returns the potential duplicates found.
    """
    if not rule_name or not test_data:
        frappe.throw("Rule Name and Test Data are required.")
    
    # Parse test_data if it's a JSON string
    if isinstance(test_data, str):
        import json
        test_data = json.loads(test_data)
        
    rule = frappe.get_doc("Data Quality Rule", rule_name)
    
    # Create a temporary document object from the test data
    # We use frappe._dict to create a dict-like object that behaves like a document
    doc = frappe._dict(test_data)
    doc.doctype = rule.document_type
    doc.name = "TEST_DOC_" + frappe.generate_hash(length=8)  # Temporary name for blocking
    
    # Debug: Log what we're testing
    frappe.errprint(f"Testing rule '{rule_name}' with test data")
    frappe.errprint(f"Test data: {test_data}")
    
    # Initialize DuplicateFinder with the test document
    finder = DuplicateFinder(doc, rule_name)
    
    # Run the check
    duplicates = finder.find_duplicates()
    
    frappe.errprint(f"Found {len(duplicates)} duplicates")
    
    # Format results for frontend
    results = []
    for dup in duplicates:
        # dup is a dict: {'docname': '...', 'score': ...}
        dup_doc_name = dup.get("docname")
        score = dup.get("score")
        
        # Fetch title for display
        title = dup_doc_name
        try:
            title = frappe.db.get_value(rule.document_type, dup_doc_name, "title") or dup_doc_name
        except Exception:
            pass
            
        results.append({
            "name": dup_doc_name,
            "title": title,
            "score": score,
            "rule": rule_name
        })
        
    return results
