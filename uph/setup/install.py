import frappe
from frappe import _
from uph.party.doctype.party_master_settings.party_master_settings import (
    setup_initial_document_types,
    setup_party_types_table,
)

# from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
#     make_dimension_in_accounting_doctypes,
# )


def full_setup():
    """Run full setup for fresh install or substantial updates"""
    run_install_setup()


def setup():
    """Legacy setup alias"""
    full_setup()


def on_migrate():
    """Run after migrate"""
    # Only run safe updates on migrate
    ensure_essential_erpnext_fixtures()
    setup_initial_document_types()
    setup_party_types_table()
    create_party_master_tree()
    # seed_default_party_master_structure() # Skipped on migrate
    create_party_analytic_accounting_dimension()
    create_gender_fixtures()


def after_install():
    """Run at install time"""
    post_install()


def run_install_setup():
    """Run full setup including seeding for new installations"""
    ensure_essential_erpnext_fixtures()
    setup_initial_document_types()
    setup_party_types_table()
    create_party_master_tree()
    seed_default_party_master_structure()
    create_party_analytic_accounting_dimension()
    create_gender_fixtures()


def run_pending_setup():
    """Legacy function, redirect to install setup for backward compatibility"""
    run_install_setup()


def ensure_essential_erpnext_fixtures():
    """Create essential ERPNext records needed for UPH installation if they are missing"""
    essential_party_types = [
        ("Customer", "Receivable"),
        ("Supplier", "Payable"),
        ("Employee", "Receivable"),
    ]
    for party_type, acc_type in essential_party_types:
        if not frappe.db.exists("Party Type", party_type):
            if frappe.db.exists("DocType", party_type):
                frappe.get_doc(
                    {
                        "doctype": "Party Type",
                        "party_type": party_type,
                        "account_type": acc_type,
                    }
                ).insert(ignore_permissions=True)
    frappe.db.commit()


def create_gender_fixtures():
    """Ensure core Gender records exist for tests and system consistency"""
    for gender in ["Female", "Male", "Other"]:
        if not frappe.db.exists("Gender", gender):
            doc = frappe.new_doc("Gender")
            doc.gender = gender
            doc.insert(ignore_permissions=True)


def post_install():
    """Run post-install configuration"""
    settings = frappe.get_doc("Party Master Settings")
    settings.flags.document_types_same = False
    if hasattr(settings, "sync_update_to_doctype_fields"):
        settings.sync_update_to_doctype_fields(force_update=True)
    settings.save()

    run_pending_setup()


def create_party_master_tree():
    """Create root node for Party Master if not exists"""
    root_filter = {"is_group": 1, "parent_party_master": ["in", ["", None]]}
    if frappe.db.exists("Party Master", root_filter):
        return

    existing = frappe.db.get_value(
        "Party Master",
        "1000",
        ["name", "is_group", "parent_party_master"],
        as_dict=True,
    )
    if existing:
        try:
            doc = frappe.get_doc("Party Master", "1000")
            doc.flags.ignore_validate = True
            doc.is_group = 1
            doc.parent_party_master = None
            if not doc.party_name:
                doc.party_name = "All Party Masters"
            doc.save(ignore_permissions=True)
        except Exception:
            frappe.log_error(
                title="UPH: Failed to normalize Party Master root",
                message="Party Master '1000' exists but could not be normalized to root.",
            )
        return

    doc = frappe.new_doc("Party Master")
    doc.party_name = "All Party Masters"
    doc.is_group = 1
    doc.party_number = "1000"
    doc.insert(ignore_permissions=True)


def seed_default_party_master_structure():
    """Seed a default Party Master structure using translatable English labels.

    This is idempotent and only updates records if they are missing.
    It supports recursive mapping of ERPNext Customer/Supplier groups.
    """
    PartyMasterSeeder().run()


class PartyMasterSeeder:
    def __init__(self):
        self.updated = False
        import json

    def run(self):
        structure = self.get_structure()
        if not structure:
            return

        for node in structure:
            self.process_node(node)

        if self.updated:
            from frappe.utils.nestedset import rebuild_tree

            rebuild_tree("Party Master")
            frappe.db.commit()

    def get_structure(self):
        import json

        try:
            # fix: path should be relative to the app module
            file_path = frappe.get_app_path(
                "uph", "setup/data/party_master_structure.json"
            )
            print(f"Loading structure from: {file_path}")
            with open(file_path, "r") as f:
                data = json.load(f)
                print(f"Loaded {len(data)} root nodes.")
                return data
        except Exception as e:
            frappe.log_error(
                "Party Master Seeding Error", f"Could not load structure JSON: {e}"
            )
            print(f"Error loading structure: {e}")
            return []

    def process_node(self, node, parent=None):
        # 1. Ensure current node exists
        pm_name = self.ensure_node(node, parent)

        # 2. Process predefined children
        if node.get("children"):
            for child in node.get("children"):
                self.process_node(child, parent=pm_name)

        # 3. Process dynamic sync (ERPNext Groups)
        if node.get("sync_erpnext_group"):
            self.sync_erpnext_groups(
                node.get("sync_erpnext_group"), pm_name, node.get("party_type")
            )

    def ensure_node(self, node, parent):
        party_number = node.get("party_number")

        # Define identification filters
        if party_number:
            filters = {"party_number": party_number}
        else:
            # Fallback for nodes without fixed number
            filters = {
                "party_name": _(node.get("party_name")),
                "parent_party_master": parent,
                "is_group": 1,
            }

        # Prepare values
        values = {
            "party_name": _(node.get("party_name")),
            "parent_party_master": parent,
            "is_group": 1,
            "party_type": node.get("party_type"),
            "group_type": node.get("group_type"),
            "party_type_group": node.get("party_type_group"),
        }

        return self.upsert(filters, values, party_number)

    def upsert(self, filters, values, party_number=None):
        existing = frappe.db.exists("Party Master", filters)

        if existing:
            doc = frappe.get_doc("Party Master", existing)
            changed = False

            # Compare values
            for k, v in values.items():
                if v is not None and doc.get(k) != v:
                    doc.set(k, v)
                    changed = True

            # Ensure number matches strict ID if provided
            if party_number and doc.party_number != party_number:
                doc.party_number = party_number
                changed = True

            if not doc.title:
                changed = True

            if changed:
                doc.flags.ignore_validate = False
                doc.save(ignore_permissions=True)
                self.updated = True

            return doc.name
        else:
            doc = frappe.new_doc("Party Master")
            doc.update(values)
            if party_number:
                doc.party_number = party_number

            doc.flags.ignore_validate = False
            doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
            self.updated = True
            return doc.name

    def sync_erpnext_groups(self, doctype, parent_pm, party_type):
        group_type = doctype
        parent_field = "parent_" + group_type.lower().replace(" ", "_")

        groups = frappe.get_all(
            doctype,
            fields=["name", parent_field],
            order_by="lft asc",
        )

        pm_map = {None: parent_pm}

        for group in groups:
            erp_parent = group.get(parent_field)
            if not erp_parent:
                erp_parent = None

            pm_parent = pm_map.get(erp_parent)

            if not pm_parent:
                continue

            filters = {
                "party_type_group": group.name,
                "group_type": group_type,
                "is_group": 1,
            }

            values = {
                "party_name": group.name,
                "party_type": party_type,
                "group_type": group_type,
                "party_type_group": group.name,
                "parent_party_master": pm_parent,
                "is_group": 1,
            }

            pm_name = self.upsert(filters, values)
            pm_map[group.name] = pm_name


def create_party_analytic_accounting_dimension():
    """Create Accounting Dimension for Party Analytic Accounting"""
    dimension_label = "Party Analytic Accounting"
    if not frappe.db.exists("Accounting Dimension", {"label": dimension_label}):
        doc = frappe.new_doc("Accounting Dimension")
        doc.label = dimension_label
        doc.document_type = "Party Master"
        doc.insert(ignore_permissions=True)

    # Sync columns immediately (critical for CI environments)
    doc = frappe.get_doc("Accounting Dimension", {"label": dimension_label})
    from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
        make_dimension_in_accounting_doctypes,
    )

    make_dimension_in_accounting_doctypes(doc)

    # Ensure cache is fresh for all transactional doctypes
    frappe.clear_cache(doctype="GL Entry")
    frappe.db.commit()
