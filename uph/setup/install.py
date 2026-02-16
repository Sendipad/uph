import json
import frappe
from frappe import _
from frappe.utils.nestedset import rebuild_tree
from uph.party.doctype.party_master_settings.party_master_settings import (
    setup_initial_document_types,
    setup_party_types_table,
)


class PartyMasterSeeder:
    def __init__(self, structure=None, update_existing=False):
        self.updated = False
        self.structure = structure
        self.update_existing = update_existing

    def run(self):
        structure = self.structure if self.structure else self._load_structure()
        if not structure:
            return

        for node in structure:
            self._process_node(node)

        if self.updated:
            rebuild_tree("Party Master")

    # -------------------------

    def _load_structure(self):
        try:
            path = frappe.get_app_path("uph", "setup/data/party_master_structure.json")
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            frappe.log_error(
                title="UPH: Party Master Seeding Error",
                message=str(e),
            )
            return []

    # -------------------------

    def _process_node(self, node, parent=None):
        pm_name = self._ensure_node(node, parent)

        for child in node.get("children", []):
            self._process_node(child, parent=pm_name)

        if node.get("sync_erpnext_group"):
            self._sync_erpnext_groups(
                node["sync_erpnext_group"],
                pm_name,
                node.get("party_type"),
            )

    # -------------------------

    def _ensure_node(self, node, parent):
        party_number = node.get("party_number")

        if party_number:
            filters = {"party_number": party_number}
        else:
            filters = {
                "party_name": _(node.get("party_name")),
                "parent_party_master": parent,
                "is_group": 1,
            }

        values = {
            "party_name": _(node.get("party_name")),
            "parent_party_master": parent,
            "is_group": 1,
            "party_type": node.get("party_type"),
            "group_type": node.get("group_type"),
            "party_type_group": node.get("party_type_group"),
        }

        return self._upsert(filters, values, party_number)

    # -------------------------

    def _upsert(self, filters, values, party_number=None):
        existing = frappe.db.exists("Party Master", filters)

        # Fallback: Check by name if not found by primary filter (to avoid uniqueness errors)
        if not existing and values.get("party_name"):
            existing = frappe.db.exists(
                "Party Master", {"party_name": values["party_name"]}
            )

        if existing:
            if not self.update_existing:
                return existing

            doc = frappe.get_doc("Party Master", existing)
            changed = False

            for k, v in values.items():
                if v is not None and doc.get(k) != v:
                    doc.set(k, v)
                    changed = True

            if party_number and doc.party_number != party_number:
                doc.party_number = party_number
                changed = True

            if not doc.title:
                doc.title = doc.party_name
                changed = True

            if changed:
                doc.save(ignore_permissions=True)
                self.updated = True

            return doc.name

        doc = frappe.new_doc("Party Master")
        doc.update(values)

        if party_number:
            doc.party_number = party_number

        doc.title = doc.party_name
        doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
        self.updated = True
        return doc.name

    # -------------------------

    def _sync_erpnext_groups(self, doctype, parent_pm, party_type):
        parent_field = "parent_" + doctype.lower().replace(" ", "_")

        try:
            groups = frappe.get_all(
                doctype,
                fields=["name", parent_field],
                order_by="lft asc",
            )
        except Exception:
            # ERPNext not installed
            return

        pm_map = {None: parent_pm}

        for group in groups:
            erp_parent = group.get(parent_field) or None
            pm_parent = pm_map.get(erp_parent)

            if not pm_parent:
                continue

            filters = {
                "party_type_group": group.name,
                "group_type": doctype,
                "is_group": 1,
            }

            values = {
                "party_name": group.name,
                "party_type": party_type,
                "group_type": doctype,
                "party_type_group": group.name,
                "parent_party_master": pm_parent,
                "is_group": 1,
            }

            pm_name = self._upsert(filters, values)
            pm_map[group.name] = pm_name


# ---------------------------------------------------------
# Public Lifecycle Hooks
# ---------------------------------------------------------


def full_setup():
    run_install_setup()


def setup():
    full_setup()


def after_install():
    _post_install()


def on_migrate():
    # Prevent accidental execution during install
    if frappe.flags.in_install:
        return

    _safe_setup_operations()


# ---------------------------------------------------------
# Install / Migrate Routines
# ---------------------------------------------------------


def run_install_setup():
    _safe_setup_operations()
    # seed_default_party_master_structure() # Deferred to Setup Wizard


def run_pending_setup():
    run_install_setup()


def _safe_setup_operations():
    ensure_essential_erpnext_fixtures()
    setup_initial_document_types()
    setup_party_types_table()
    create_party_master_tree()
    create_party_analytic_accounting_dimension()
    create_gender_fixtures()
    create_custom_indices()


def create_custom_indices():
    """Create custom database indices for performance optimization."""
    indices = [
        # Table, Columns
        ("tabSales Invoice", ["party_master", "docstatus"]),
        ("tabPurchase Invoice", ["party_master", "docstatus"]),
        ("tabPayment Entry", ["party_master", "docstatus"]),
        ("tabJournal Entry", ["party_master", "docstatus"]),
    ]

    for table, columns in indices:
        doctype = table.replace("tab", "")
        if not frappe.db.exists("DocType", doctype):
            continue

        # check if columns exist
        if not frappe.db.has_column(doctype, columns[0]) or not frappe.db.has_column(
            doctype, columns[1]
        ):
            continue

        index_name = (
            f"uph_{table.replace('tab', '').replace(' ', '_').lower()}_pm_status"
        )

        # Check if index exists
        if not frappe.db.sql(
            f"SHOW INDEX FROM `{table}` WHERE Key_name = %s", (index_name,)
        ):
            try:
                frappe.db.sql(
                    f"CREATE INDEX `{index_name}` ON `{table}` ({', '.join(columns)})"
                )
            except Exception as e:
                frappe.log_error(
                    f"UPH: Failed to create index {index_name} on {table}: {str(e)}"
                )


def _post_install():
    settings = frappe.get_doc("Party Master Settings")
    settings.flags.document_types_same = False

    if hasattr(settings, "sync_update_to_doctype_fields"):
        settings.sync_update_to_doctype_fields(force_update=True)

    settings.save(ignore_permissions=True)
    run_pending_setup()


# ---------------------------------------------------------
# Core Fixtures
# ---------------------------------------------------------


def ensure_essential_erpnext_fixtures():
    essential_party_types = [
        ("Customer", "Receivable"),
        ("Supplier", "Payable"),
        ("Employee", "Receivable"),
    ]

    for party_type, acc_type in essential_party_types:
        if frappe.db.exists("Party Type", party_type):
            continue

        if not frappe.db.exists("DocType", party_type):
            continue

        frappe.get_doc(
            {
                "doctype": "Party Type",
                "party_type": party_type,
                "account_type": acc_type,
            }
        ).insert(ignore_permissions=True, ignore_if_duplicate=True)


def create_gender_fixtures():
    for gender in ["Female", "Male", "Other"]:
        if frappe.db.exists("Gender", gender):
            continue

        doc = frappe.new_doc("Gender")
        doc.gender = gender
        doc.insert(ignore_permissions=True, ignore_if_duplicate=True)


# ---------------------------------------------------------
# Party Master Root
# ---------------------------------------------------------


def create_party_master_tree():
    root_filter = {"is_group": 1, "parent_party_master": ["in", ["", None]]}
    roots = frappe.get_all("Party Master", filters=root_filter, pluck="name")

    if len(roots) == 1:
        return

    if len(roots) > 1:
        frappe.log_error(
            title="UPH: Multiple Party Master Roots",
            message=f"Detected multiple root nodes: {roots}",
        )
        return

    # Normalize if 1000 exists
    existing = frappe.db.get_value(
        "Party Master",
        "1000",
        ["name", "is_group"],
        as_dict=True,
    )

    if existing:
        doc = frappe.get_doc("Party Master", "1000")
        doc.flags.ignore_validate = True
        doc.is_group = 1
        doc.parent_party_master = None
        if not doc.party_name:
            doc.party_name = "All Party Masters"
        doc.title = doc.party_name
        doc.save(ignore_permissions=True)
        return

    # Create fresh root
    doc = frappe.new_doc("Party Master")
    doc.party_name = "All Party Masters"
    doc.party_number = "1000"
    doc.is_group = 1
    doc.parent_party_master = None
    doc.title = doc.party_name
    doc.insert(ignore_permissions=True)


# ---------------------------------------------------------
# Seeder
# ---------------------------------------------------------


def seed_default_party_master_structure():
    PartyMasterSeeder().run()


# ---------------------------------------------------------
# Accounting Dimension
# ---------------------------------------------------------


def create_party_analytic_accounting_dimension():
    dimension_label = "Party Analytic Accounting"

    if not frappe.db.exists("Accounting Dimension", {"label": dimension_label}):
        doc = frappe.new_doc("Accounting Dimension")
        doc.label = dimension_label
        doc.document_type = "Party Master"
        doc.insert(ignore_permissions=True)

    try:
        from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
            make_dimension_in_accounting_doctypes,
        )
    except ImportError:
        return

    doc = frappe.get_doc("Accounting Dimension", {"label": dimension_label})
    make_dimension_in_accounting_doctypes(doc)

    frappe.clear_cache(doctype="GL Entry")
