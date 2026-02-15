import frappe


def before_request():
    """Force setup wizard for admin users until setup is finished."""
    try:
        if not frappe.session.user or frappe.session.user == "Guest":
            return

        # Do not enforce setup routing during automated tests (Python/UI)
        if getattr(frappe.flags, "in_test", False):
            return

        if frappe.session.user != "Administrator" and "System Manager" not in frappe.get_roles(
            frappe.session.user
        ):
            return

        setup_finished = frappe.db.get_single_value(
            "Party Master Settings", "setup_finished"
        )
        if setup_finished:
            return

        path = (frappe.local.request.path or "").rstrip("/")
        allowed_paths = {
            "/app/setup-wizard",
            "/api/method/uph.party.page.setup_wizard.setup_wizard.get_setup_status",
            "/api/method/uph.party.page.setup_wizard.setup_wizard.get_tree_templates",
            "/api/method/uph.party.page.setup_wizard.setup_wizard.apply_setup_settings",
            "/api/method/frappe.desk.desktop.get_desktop_page",
        }

        if path.startswith("/app") and not path.startswith("/app/setup-wizard") and path not in allowed_paths:
            frappe.local.flags.redirect_location = "/app/setup-wizard"
            raise frappe.Redirect
    except frappe.Redirect:
        raise
    except Exception:
        # never block request lifecycle on setup enforcement failure
        frappe.log_error(frappe.get_traceback(), "UPH Setup enforcement failed")
