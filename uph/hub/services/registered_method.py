# filepath: apps/uph/uph/hub/services/registered_method.py
import frappe
from frappe import _

def execute_method(method_name: str, params: dict):
    """Execute a registered method with parameters"""
    if not method_name or not frappe.db.exists("Registered Method", method_name):
        frappe.throw(_("Method not found: {0}").format(method_name))
    
    method = frappe.get_cached_doc("Registered Method", method_name)
    return frappe.call(method.method_path, **params)
