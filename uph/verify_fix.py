import frappe
from frappe import _


def verify_fix():
    print("Verifying validation fix for Party Master...")

    parent_number = "9999"
    parent_name = "TestParent9999"

    # Clean up any existing test data first
    if frappe.db.exists("Party Master", parent_name):
        frappe.delete_doc("Party Master", parent_name, force=True)
    if frappe.db.exists("Party Master", parent_number):  # Since name is party_number
        frappe.delete_doc("Party Master", parent_number, force=True)

    # 1. Setup Parent
    try:
        doc = frappe.new_doc("Party Master")
        doc.party_name = parent_name
        doc.party_number = parent_number
        doc.is_group = 1
        doc.flags.ignore_validate = True
        doc.insert(ignore_permissions=True)
        print(f"Created parent: {doc.name}")
    except Exception as e:
        print(f"Setup Failed: {e}")
        return

    # 2. Test Case 1: Insert CHILD without party_type (Expect FAIL)
    print("\nTest Case 1: Insert without ignore_validate (Should Fail)")
    try:
        doc1 = frappe.new_doc("Party Master")
        doc1.party_name = "Child Fail Test"
        doc1.parent_party_master = parent_number
        doc1.is_group = 0
        # party_type purposefully omitted
        doc1.insert(ignore_permissions=True)
        print("FAIL: Insertion succeeded unexpectedly!")
        # Clean up if it succeeded (bad)
        frappe.delete_doc("Party Master", doc1.name, force=True)
    except frappe.exceptions.ValidationError as e:
        # We need to catch the SPECIFIC error about Party Type
        if "Default Party Type is Mandatory" in str(e):
            print(f"SUCCESS: Caught expected ValidationError: {e}")
        else:
            print(f"FAIL: Caught unexpected ValidationError: {e}")
    except Exception as e:
        print(f"FAIL: Caught unexpected exception: {e}")

    # 3. Test Case 2: Insert CHILD with ignore_validate=True (Expect PASS)
    print("\nTest Case 2: Insert with ignore_validate=True (Should Pass)")
    try:
        doc2 = frappe.new_doc("Party Master")
        doc2.party_name = "Child Pass Test"
        doc2.parent_party_master = parent_number
        doc2.is_group = 0
        doc2.flags.ignore_validate = True

        doc2.insert(ignore_permissions=True)
        print(f"SUCCESS: Insertion succeeded as expected. New Doc: {doc2.name}")

        # Cleanup doc2
        frappe.delete_doc("Party Master", doc2.name, force=True)
    except Exception as e:
        print(f"FAIL: Insertion failed unexpectedly: {e}")
        import traceback

        traceback.print_exc()

    # Final Cleanup Parent
    try:
        frappe.delete_doc("Party Master", parent_number, force=True)
        print("\nCleanup completed.")
    except:
        pass


if __name__ == "__main__":
    pass
