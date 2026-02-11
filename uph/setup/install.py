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

    This is idempotent and only updates records if they are missing or match known legacy names.
    """

    def ensure_group(group_doctype, group_name):
        if not (group_doctype and group_name):
            return None
        if frappe.db.exists(group_doctype, group_name):
            return group_name
        parent = (
            "All Customer Groups"
            if group_doctype == "Customer Group"
            else "All Supplier Groups"
            if group_doctype == "Supplier Group"
            else None
        )
        if parent and frappe.db.exists(group_doctype, parent):
            doc = frappe.new_doc(group_doctype)
            doc.group_name = group_name
            doc.parent_customer_group = parent if group_doctype == "Customer Group" else None
            doc.parent_supplier_group = parent if group_doctype == "Supplier Group" else None
            doc.insert(ignore_permissions=True)
            return group_name
        return None

    structure = [
        {
            "party_number": "1000",
            "party_name": _("Debtors"),
            "legacy_names": ["مدينون", "All Party Masters", "Root Group"],
            "parent_party_master": None,
            "is_group": 1,
            "party_type": "Customer",
            "group_type": "Customer Group",
        },
        {
            "party_number": "1300",
            "party_name": _("Customers"),
            "legacy_names": ["العملاء"],
            "parent_party_master": "1000",
            "is_group": 1,
            "party_type": "Customer",
            "group_type": "Customer Group",
        },
        {
            "party_number": "1301",
            "party_name": _("Cash Sales"),
            "legacy_names": ["المبيعات النقدية"],
            "parent_party_master": "1300",
            "is_group": 1,
            "party_type": "Customer",
            "group_type": "Customer Group",
        },
        {
            "party_number": "1310",
            "party_name": _("Local Customers"),
            "legacy_names": ["عملاء تجاريون"],
            "parent_party_master": "1300",
            "is_group": 1,
            "party_type": "Customer",
            "group_type": "Customer Group",
        },
        {
            "party_number": "1320",
            "party_name": _("International Customers"),
            "legacy_names": ["عملاء مزارعون"],
            "parent_party_master": "1300",
            "is_group": 1,
            "party_type": "Customer",
            "group_type": "Customer Group",
            "party_type_group": _("Farmers"),
        },
        {
            "party_number": "1340",
            "party_name": _("Other Debtors - Advances"),
            "legacy_names": ["مدينون آخرون -سلف"],
            "parent_party_master": "1300",
            "is_group": 1,
            "party_type": "Customer",
            "group_type": "Customer Group",
        },
        {
            "party_number": "1600",
            "party_name": _("Employees"),
            "legacy_names": ["المؤظفين"],
            "parent_party_master": "1000",
            "is_group": 1,
            "party_type": "Customer",
            "group_type": "Customer Group",
            "default_currency": "YER",
        },
        {
            "party_number": "2000",
            "party_name": _("Creditors"),
            "legacy_names": ["الدائنون"],
            "parent_party_master": None,
            "is_group": 1,
            "party_type": "Supplier",
            "group_type": "Supplier Group",
        },
        {
            "party_number": "2110",
            "party_name": _("Foreign Suppliers"),
            "legacy_names": ["الموردين الخارجيون"],
            "parent_party_master": "2000",
            "is_group": 1,
            "party_type": "Supplier",
            "group_type": "Supplier Group",
        },
        {
            "party_number": "2120",
            "party_name": _("Local Suppliers"),
            "legacy_names": ["الدائنون المحليون"],
            "parent_party_master": "2000",
            "is_group": 1,
            "party_type": "Supplier",
            "group_type": "Supplier Group",
            "party_type_group": _("Local"),
        },
        {
            "party_number": "2140",
            "party_name": _("Lessors and Service Providers"),
            "legacy_names": ["المؤجرين ومقدمي الخدمات"],
            "parent_party_master": "2000",
            "is_group": 1,
            "party_type": "Supplier",
            "group_type": "Supplier Group",
        },
        {
            "party_number": "3000",
            "party_name": _("Company Branches"),
            "legacy_names": ["فروع الشركه"],
            "parent_party_master": None,
            "is_group": 1,
            "party_type": "Customer",
        },
    ]

    updated = False
    for row in structure:
        name = row["party_number"]
        legacy_names = set(row.get("legacy_names") or [])
        if frappe.db.exists("Party Master", name):
            doc = frappe.get_doc("Party Master", name)
            changed = False
            if not doc.party_name or doc.party_name in legacy_names:
                doc.party_name = row["party_name"]
                changed = True
            if row.get("parent_party_master") is not None and not doc.parent_party_master:
                doc.parent_party_master = row["parent_party_master"]
                changed = True
            if doc.is_group != 1:
                doc.is_group = 1
                changed = True
            if row.get("party_type") and not doc.party_type:
                doc.party_type = row["party_type"]
                changed = True
            if row.get("group_type") and not doc.group_type:
                doc.group_type = row["group_type"]
                changed = True
            if row.get("default_currency") and not doc.default_currency:
                doc.default_currency = row["default_currency"]
                changed = True
            if row.get("party_type_group") and not doc.party_type_group:
                group_name = ensure_group(doc.group_type, row["party_type_group"])
                if group_name:
                    doc.party_type_group = group_name
                    changed = True
            if changed:
                doc.flags.ignore_validate = True
                doc.save(ignore_permissions=True)
                updated = True
        else:
            doc = frappe.new_doc("Party Master")
            doc.party_number = row["party_number"]
            doc.party_name = row["party_name"]
            doc.is_group = 1
            doc.party_type = row.get("party_type")
            doc.group_type = row.get("group_type")
            doc.parent_party_master = row.get("parent_party_master")
            doc.default_currency = row.get("default_currency")
            if row.get("party_type_group"):
                doc.party_type_group = ensure_group(doc.group_type, row["party_type_group"])
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
