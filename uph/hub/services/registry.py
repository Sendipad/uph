# filepath: apps/uph/uph/hub/services/registry.py
import importlib
import os
import pathlib
import frappe
from frappe import _

# Core services registry
_core_services = {}
_plugin_services = {}
_loaded = False


def register(plugin=True):
    def decorator(cls):
        if not getattr(cls, "service_type", None):
            frappe.throw(_("Service class must have 'service_type' attribute"))

        if plugin:
            _plugin_services[cls.service_type] = cls
        else:
            _core_services[cls.service_type] = cls

        frappe.cache().delete_value("rule_services")
        return cls

    return decorator


def core_register(cls):
    return register(plugin=False)(cls)


def sync_rule_service_types():
    """
    After migrate, ensure all registered services have Rule Service Type documents.
    """
    load_core_services()

    for service_type, cls in _core_services.items():
        label = getattr(cls, "label", service_type)
        doc = frappe.db.exists("Rule Service Type", {"name": service_type})
        if not doc:
            frappe.get_doc(
                {
                    "doctype": "Rule Service Type",
                    "name": service_type,
                    "label": label,
                    "plugin": 0,
                    "is_core": 1,
                }
            ).insert(ignore_permissions=True)


def get_service(service_type):
    """
    Get service class by type
    :param service_type: Service type identifier
    :return: Service class or None
    """
    services = get_all_services()
    return services.get(service_type)


@frappe.whitelist()
def list_services():
    """List all registered service types"""
    services = get_all_services()
    return list(services.keys())


def get_all_services():
    """Get all services with caching"""
    services = frappe.cache().get_value("rule_services")

    if services is None:
        # Ensure core services are loaded
        load_core_services()

        services = {**_core_services, **_plugin_services}
        frappe.cache().set_value("rule_services", services, expires_in_sec=3600)

    return services


def load_core_services():
    """Load core services from hub/mdm directory"""
    global _loaded
    if _loaded:
        return

    try:
        mdm_dir = pathlib.Path(__file__).resolve().parent.parent / "mdm"

        if mdm_dir.exists():
            for f in os.listdir(mdm_dir):
                if f.endswith(".py") and not f.startswith("__"):
                    module_name = f"uph.hub.mdm.{f[:-3]}"
                    try:
                        importlib.import_module(module_name)
                    except ImportError as e:
                        frappe.log_error(
                            title=_("Failed to load core service module"),
                            message=f"Module: {module_name}\nError: {str(e)}",
                        )
        _loaded = True
    except Exception as e:
        frappe.log_error(title=_("Core service loading failed"), message=str(e))
        _loaded = True  # Prevent repeated attempts


def clear_registry():
    """Clear registry (for testing and cache invalidation)"""
    global _core_services, _plugin_services, _loaded
    _core_services = {}
    _plugin_services = {}
    _loaded = False
    frappe.cache().delete_value("rule_services")


# Load core services on module init
load_core_services()
