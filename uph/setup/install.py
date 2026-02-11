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
    run_pending_setup()


def setup():
    """Legacy setup alias"""
    full_setup()


def on_migrate():
    """Run after migrate"""
    run_pending_setup()


def after_install():
    """Run at install time"""
    post_install()


def run_pending_setup():
    """Run new setup safely for existing sites"""
    ensure_essential_erpnext_fixtures()
    setup_initial_document_types()
    setup_party_types_table()
    create_party_master_tree()
    seed_default_party_master_structure()
    create_party_analytic_accounting_dimension()
    create_gender_fixtures()


def ensure_essential_erpnext_fixtures():
    """Create essential ERPNext records needed for UPH installation if they are missing"""
    for party_type, acc_type in [("Customer", "Receivable"), ("Supplier", "Payable")]:
        if not frappe.db.exists("Party Type", party_type):
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
    It also creates a level under Customers/Suppliers based on existing groups.
    """

    def ensure_pm_node(party_number, party_name, parent, party_type, group_type=None):
        if party_number and frappe.db.exists("Party Master", party_number):
            doc = frappe.get_doc("Party Master", party_number)
            changed = False
            if not doc.party_name:
                doc.party_name = party_name
                changed = True
            if parent is not None and not doc.parent_party_master:
                doc.parent_party_master = parent
                changed = True
            if doc.is_group != 1:
                doc.is_group = 1
                changed = True
            if party_type and not doc.party_type:
                doc.party_type = party_type
                changed = True
            if group_type and not doc.group_type:
                doc.group_type = group_type
                changed = True
            if changed:
                doc.flags.ignore_validate = True
                doc.save(ignore_permissions=True)
                return doc.name, True
            return doc.name, False

        if not party_number:
            existing = frappe.get_all(
                "Party Master",
                filters={
                    "party_name": party_name,
                    "parent_party_master": parent,
                    "is_group": 1,
                },
                pluck="name",
                limit=1,
            )
            if existing:
                return existing[0], False

        doc = frappe.new_doc("Party Master")
        if party_number:
            doc.party_number = party_number
        doc.party_name = party_name
        doc.is_group = 1
        doc.party_type = party_type
        doc.group_type = group_type
        doc.parent_party_master = parent
        doc.flags.ignore_validate = True
        doc.insert(ignore_permissions=True)
        return doc.name, True

    structure = [
        {
            "party_number": "1000",
            "party_name": _("Debtors"),
            "parent_party_master": None,
            "is_group": 1,
            "party_type": "Customer",
            "group_type": "Customer Group",
        },
        {
            "party_number": "1300",
            "party_name": _("Customers"),
            "parent_party_master": "1000",
            "is_group": 1,
            "party_type": "Customer",
            "group_type": "Customer Group",
        },
        {
            "party_number": "1301",
            "party_name": _("Cash Sales"),
            "parent_party_master": "1300",
            "is_group": 1,
            "party_type": "Customer",
            "group_type": "Customer Group",
        },
        {
            "party_number": "1600",
            "party_name": _("Employees"),
            "parent_party_master": "1000",
            "is_group": 1,
            "party_type": "Employee",
        },
        {
            "party_number": "2000",
            "party_name": _("Creditors"),
            "parent_party_master": None,
            "is_group": 1,
            "party_type": "Supplier",
            "group_type": "Supplier Group",
        },
        {
            "party_number": "2100",
            "party_name": _("Suppliers"),
            "parent_party_master": "2000",
            "is_group": 1,
            "party_type": "Supplier",
            "group_type": "Supplier Group",
        },
        {
            "party_number": "3000",
            "party_name": _("Company Branches"),
            "parent_party_master": None,
            "is_group": 1,
            "party_type": "Customer",
        },
    ]

    updated = False
    for row in structure:
        _, changed = ensure_pm_node(
            row.get("party_number"),
            row.get("party_name"),
            row.get("parent_party_master"),
            row.get("party_type"),
            row.get("group_type"),
        )
        if changed:
            updated = True

    # Create third-level nodes based on existing Customer/Supplier Groups
    customers_parent, _ = ensure_pm_node(
        "1300", _("Customers"), "1000", "Customer", "Customer Group"
    )
    suppliers_parent, _ = ensure_pm_node(
        "2100", _("Suppliers"), "2000", "Supplier", "Supplier Group"
    )

    customer_groups = frappe.get_all(
        "Customer Group",
        filters={"parent_customer_group": ["!=", ""]},
        pluck="name",
        order_by="name asc",
    )
    for group_name in customer_groups:
        existing = frappe.get_all(
            "Party Master",
            filters={
                "group_type": "Customer Group",
                "party_type_group": group_name,
                "parent_party_master": customers_parent,
                "is_group": 1,
            },
            pluck="name",
            limit=1,
        )
        if existing:
            continue
        doc = frappe.new_doc("Party Master")
        doc.party_name = group_name
        doc.is_group = 1
        doc.party_type = "Customer"
        doc.group_type = "Customer Group"
        doc.party_type_group = group_name
        doc.parent_party_master = customers_parent
        doc.flags.ignore_validate = True
        doc.insert(ignore_permissions=True)
        updated = True

    supplier_groups = frappe.get_all(
        "Supplier Group",
        filters={"parent_supplier_group": ["!=", ""]},
        pluck="name",
        order_by="name asc",
    )
    for group_name in supplier_groups:
        existing = frappe.get_all(
            "Party Master",
            filters={
                "group_type": "Supplier Group",
                "party_type_group": group_name,
                "parent_party_master": suppliers_parent,
                "is_group": 1,
            },
            pluck="name",
            limit=1,
        )
        if existing:
            continue
        doc = frappe.new_doc("Party Master")
        doc.party_name = group_name
        doc.is_group = 1
        doc.party_type = "Supplier"
        doc.group_type = "Supplier Group"
        doc.party_type_group = group_name
        doc.parent_party_master = suppliers_parent
        doc.flags.ignore_validate = True
        doc.insert(ignore_permissions=True)
        updated = True

    if updated:
        from frappe.utils.nestedset import rebuild_tree

        rebuild_tree("Party Master")
        frappe.db.commit()


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
