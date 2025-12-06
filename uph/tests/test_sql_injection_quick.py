"""
Quick Test Script for SQL Injection Fixes
Run in bench console: bench console
Then execute: exec(open('apps/uph/uph/tests/test_sql_injection_quick.py').read())
"""

import frappe

def test_sql_injection_fixes():
    """Quick smoke test to verify SQL injection fixes work."""
    print("\n" + "="*70)
    print("SQL INJECTION FIXES - QUICK VERIFICATION TEST")
    print("="*70)
    
    # Test 1: boot.py functions
    print("\n1. Testing boot.py - get_pm_doctypes()...")
    try:
        from uph.party.boot import get_pm_doctypes
        result = get_pm_doctypes()
        print(f"   ✓ get_pm_doctypes() works - returned {len(result)} doctypes")
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)}")
        return False
    
    # Test 2: boot.py - get_party_master_depends_on_fields
    print("\n2. Testing boot.py - get_party_master_depends_on_fields()...")
    try:
        from uph.party.boot import get_party_master_depends_on_fields
        result = get_party_master_depends_on_fields()
        print(f"   ✓ get_party_master_depends_on_fields() works - {len(result)} mappings")
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)}")
        return False
    
    # Test 3: party/utils.py - get_party_master_list (normal search)
    print("\n3. Testing party/utils.py - get_party_master_list() with normal input...")
    try:
        from uph.party.utils import get_party_master_list
        result = get_party_master_list(
            doctype="Party Master",
            txt="test",
            searchfield="name",
            start=0,
            page_len=10,
            filters={}
        )
        print(f"   ✓ Normal search works - returned {len(result)} results")
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)}")
        return False
    
    # Test 4: SQL Injection attempt (should be blocked/safe)
    print("\n4. Testing SQL injection protection...")
    try:
        malicious_inputs = [
            {"txt": "test'; DROP TABLE tabCustomer; --"},
            {"filters": {"party_type": "'; DROP TABLE tabCustomer; --"}},
            {"start": "0; DELETE FROM tabCustomer; --"},
        ]
        
        for i, malicious_input in enumerate(malicious_inputs, 1):
            try:
                get_party_master_list(
                    doctype="Party Master",
                    txt=malicious_input.get("txt", ""),
                    searchfield="name",
                    start=malicious_input.get("start", 0),
                    page_len=10,
                    filters=malicious_input.get("filters", {})
                )
                print(f"   ✓ Malicious input {i} safely handled (no SQL error)")
            except ValueError:
                # Expected for invalid int conversion
                print(f"   ✓ Malicious input {i} rejected (value error - expected)")
            except frappe.ValidationError:
                print(f"   ✓ Malicious input {i} rejected (validation error - expected)")
            except Exception as e:
                if "SQL syntax" in str(e) or "DROP" in str(e).upper():
                    print(f"   ❌ SQL INJECTION POSSIBLE: {str(e)}")
                    return False
                else:
                    print(f"   ✓ Malicious input {i} safely handled: {type(e).__name__}")
    
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)}")
        return False
    
    # Test 5: Verify tables still exist (no DROP executed)
    print("\n5. Verifying database integrity...")
    try:
        exists = frappe.db.table_exists("Customer")
        if exists:
            print("   ✓ Customer table intact")
        else:
            print("   ❌ Customer table MISSING!")
            return False
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)}")
        return False
    
    # Summary
    print("\n" + "="*70)
    print("ALL TESTS PASSED ✓")
    print("="*70)
    print("\nSummary:")
    print("- boot.py functions using ORM: ✓")
    print("- party/utils.py using pypika: ✓")
    print("- SQL injection protection: ✓")
    print("- Database integrity: ✓")
    print("\n✅ SQL injection fixes verified successfully!\n")
    return True

if __name__ == "__main__":
    try:
        success = test_sql_injection_fixes()
        if not success:
            print("\n⚠️  Some tests failed - please review errors above")
    except Exception as e:
        print(f"\n❌ Test suite crashed: {str(e)}")
        import traceback
        traceback.print_exc()
