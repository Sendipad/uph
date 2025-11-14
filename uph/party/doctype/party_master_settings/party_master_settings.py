# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt
from frappe.custom.doctype.custom_field.custom_field import (
    create_custom_field,
    create_custom_fields,
)
from collections import OrderedDict
import frappe
from frappe import _
from frappe.model.document import Document
import uph


class PartyMasterSettings(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from uph.party.doctype.party_master_settings_docfield.party_master_settings_docfield import PartyMasterSettingsDocField
        from uph.party.doctype.party_master_settings_doctype.party_master_settings_doctype import PartyMasterSettingsDocType
        from uph.party.doctype.party_master_settings_party_type.party_master_settings_party_type import PartyMasterSettingsPartyType

        document_types: DF.Table[PartyMasterSettingsDocType]
        party_master_fields: DF.Table[PartyMasterSettingsDocField]
        party_types: DF.Table[PartyMasterSettingsPartyType]
    # end: auto-generated types
    def validate(self):
        self.validate_document_types()
        self.validate_party_master_fields_options()

    def on_update(self):
        frappe.cache.delete_key(uph.make_key(f"{self.doctype}.party_types"))
        frappe.cache.delete_key(uph.make_key(f"{self.doctype}.document_types"))
        self.create_pm_fields_on_party_doctype()
        self.sync_update_to_doctype_fields()

    def create_pm_fields_on_party_doctype(self):
        if not getattr(self, "_doc_before_save", None):
            return

        if self.is_child_table_same("party_types"):
            return

        party_types = [x.get("party_type") for x in self.party_types]
        custom_fields = {}

        for d in party_types:
            meta = frappe.get_meta(d)
            fieldnames = [f.fieldname for f in meta.fields]

            insert_after = None
            if "naming_series" in fieldnames:
                insert_after = "naming_series"
            elif f"{d.lower()}_name" in fieldnames:
                idx = fieldnames.index(f"{d.lower()}_name")
                if idx > 0:
                    prev_field = fieldnames[idx - 1]
                    insert_after = prev_field
            else:
                insert_after = "naming_series"  # fallback default

            custom_fields[d] = [
                {
                    "fieldname": "party_master",
                    "fieldtype": "Link",
                    "options": "Party Master",
                    "label": "Party Master",
                    "placeholder": "Set Parent Party Master",
                    "reqd": 0,
                    "in_list_view": 1,
                    "in_standard_filter": 1,
                    "bold": 1,
                    "allow_in_quick_entry": 1,
                    "insert_after": insert_after,
                    "search_index": 1,
                    "read_only_depends_on": "",
                    "read_only": 0,
                },
                {
                    "fieldname": "is_default_for_party_master",
                    "fieldtype": "Check",
                    "label": "Is Default for Party Master",
                    "reqd": 0,
                    "in_list_view": 1,
                    "in_standard_filter": 0,
                    "allow_in_quick_entry": 1,
                    "insert_after": "party_master",
                    "search_index": 1,
                    "depends_on": "eval:doc.party_master",
                    "description": "Checking this will make it the default for Party Master.",
                },
            ]

        if custom_fields:
            create_custom_fields(custom_fields, update=True)

    def validate_party_master_fields_options(self):
        if self.is_child_table_same("party_master_fields"):
            return

        old_docfields = self.get_doc_before_save().get("party_master_fields", [])
        party_types = frappe.get_all("Party Type", pluck="name")

        new_row_mapped = OrderedDict()
        new_row_mapped = {d.fieldname: d.options for d in self.party_master_fields}

        if not old_docfields:
            return

        old_mapped = {d.fieldname: d.options for d in old_docfields}

        for df, option in new_row_mapped.items():
            # Skip if unchanged from old doc
            if df in old_mapped and option == old_mapped.get(df):
                continue

            option_list = []
            if option:
                option_list = [
                    (line.split(":")[0].strip(), line.split(":")[1].strip())
                    for line in option.split("\n")
                    if ":" in line
                ]

            for party_name in party_types:
                # Skip if party already exists with '_' value
                if any(name == party_name and val == "_" for name, val in option_list):
                    continue

                meta = frappe.get_meta(party_name)
                party_field = next(
                    (field for name, field in option_list if name == party_name), None
                )

                # If valid field exists, continue
                if party_field and meta.has_field(party_field):
                    continue

                # Try to use df as fieldname if it exists
                if meta.has_field(df):
                    option_list.append((party_name, df))
                    continue

                # Default case
                option_list.append((party_name, "_"))

            # Convert back to string format
            new_row_mapped[df] = "\n".join(
                f"{name}:{field}" for name, field in option_list
            )

        # Update the child table
        for d in self.party_master_fields:
            d.options = new_row_mapped.get(d.fieldname)

    def validate_document_types(self):

        self.flags.document_types_same = False
        if self.is_child_table_same("document_types"):
            self.flags.document_types_same = True
            return
        if (
            frappe.session.user != "Administrator"
            and "System Manager" not in frappe.get_roles()
        ):
            frappe.throw(
                _("Only System Managers are allowed to update this settings."),
                frappe.PermissionError,
            )
        doctypes = set()
        for d in self.document_types:
            # Validate required fields
            if not d.document_type and not d.parent_doctype:
                frappe.throw(_("Document Type and Parent Doctype are Required"))

            dt_meta = frappe.get_meta(d.document_type)
            meta = None  # Meta of the Parent Doctype

            # Handle cases where parent doctype is not provided
            if not d.parent_doctype:
                if dt_meta.istable:
                    frappe.throw(
                        _("Parent Doctype is Required at row {0}").format(d.idx)
                    )
                d.parent_doctype = d.document_type  # Self-parented

            # If parent and child are different, validate the linkage
            if d.parent_doctype != d.document_type:
                meta = frappe.get_meta(d.parent_doctype)
                child_tables = [
                    df.options for df in meta.fields if df.fieldtype == "Table"
                ]
                if d.document_type not in child_tables:
                    frappe.throw(
                        _(
                            "The Parent Doctype at row {0} has no Child Table pointing to {1}"
                        ).format(d.idx, _(d.document_type))
                    )

            # Validate party field
            if not d.party_fieldname:
                frappe.throw(
                    _(
                        "Party Fieldname is required at the target Document Type at row {0}"
                    ).format(d.idx)
                )

            field = dt_meta.get_field(d.party_fieldname)
            if not field:
                frappe.throw(
                    _('Party Fieldname "{0}" does not exist in {1} (row {2})').format(
                        d.party_fieldname, d.document_type, d.idx
                    )
                )

            fieldtype = field.fieldtype
            if fieldtype not in ("Link", "Dynamic Link"):
                frappe.throw(
                    _(
                        "Party Fieldname at the target Document Type at row {0} must be either a Link or Dynamic Link"
                    ).format(d.idx)
                )

            # Assign dynamic/static party type fields
            option = field.options
            if fieldtype == "Link":
                d.party_type = option
                d.is_dynamic_party_type = 0
                d.party_type_fieldname = ""
            elif fieldtype == "Dynamic Link":
                d.party_type = None
                d.is_dynamic_party_type = 1
                d.party_type_fieldname = option

            # Check for duplicates
            key = (d.document_type, d.parent_doctype)
            if key in doctypes:
                frappe.throw(
                    _("Duplicate Document Type mapping found at row {0}").format(d.idx)
                )

            doctypes.add(key)

    def sync_update_to_doctype_fields(self, force_update=False):
        if self.flags.document_types_same:
            return

        create_party_master_on_document_types()

    def after_save(self):
        doctypes = [d.document_type for d in self.document_types]
        for d in doctypes:
            meta = frappe.get_meta(d)
            if not meta.issingle:
                frappe.db.add_index(d, ["party_master"])


def create_party_master_on_document_types(document_types=None):
    base_cf = {
        "fieldname": "party_master",
        "fieldtype": "Link",
        "options": "Party Master",
        "label": "Party Master",
        "placeholder": "Set Party Master",
        "reqd": 0,
        "in_list_view": 1,
        "in_standard_filter": 1,
        "bold": 1,
        "allow_in_quick_entry": 1,
        "search_index": 1,
        "read_only": 0,
        "fetch_if_empty": 0,
        "allow_on_submit": 0,
    }

    def get_safe_insert_after(fieldnames, meta, preferred_fields):
        for fname in preferred_fields:
            df = meta.get_field(fname)
            if df and not frappe.db.exists(
                "Custom Field", {"dt": meta.name, "fieldname": fname}
            ):
                return fname
        for df in meta.fields:
            if not frappe.db.exists(
                "Custom Field", {"dt": meta.name, "fieldname": df.fieldname}
            ):
                return df.fieldname

    setting = frappe.get_doc("Party Master Settings")
    all_doc_types = {row.document_type for row in setting.document_types}

    if (
        document_types
        and isinstance(document_types, str)
        and document_types in all_doc_types
    ):
        document_types = [document_types]
    elif not document_types:
        document_types = all_doc_types

    custom_fields = {}

    for doctype in document_types:
        meta = frappe.get_meta(doctype)
        fieldnames = [
            df.fieldname
            for df in meta.fields
            if df.fieldtype not in ("Column Break", "Section Break", "Tab Break")
        ]

        # Avoid inserting after a deleted or custom field
        if "party_master" in fieldnames:
            fieldnames.remove("party_master")

        # Get settings for this doctype
        setting_row = next(
            (row for row in setting.document_types if row.document_type == doctype),
            None,
        )
        party_fieldname = setting_row.party_fieldname if setting_row else None
        party_type_fieldname = (
            setting_row.get("party_type_fieldname") if setting_row else None
        )

        # Build insert_after preference list
        preferred_fields = []
        if party_type_fieldname and party_type_fieldname in fieldnames:
            idx = fieldnames.index(party_type_fieldname)
            if idx > 0:
                preferred_fields.append(fieldnames[idx - 1])
        elif party_fieldname and party_fieldname in fieldnames:
            idx = fieldnames.index(party_fieldname)
            if idx > 0:
                preferred_fields.append(fieldnames[idx - 1])

        preferred_fields += ["naming_series", "company"]

        insert_after = get_safe_insert_after(fieldnames, meta, preferred_fields)

        # Build custom field
        custom_field = base_cf.copy()
        custom_field["insert_after"] = insert_after

        if meta.issingle:
            custom_field.update(
                {
                    "in_list_view": 0,
                    "in_standard_filter": 0,
                    "bold": 0,
                    "allow_in_quick_entry": 0,
                    "search_index": 0,
                }
            )

        custom_fields[doctype] = custom_field

    if custom_fields:
        create_custom_fields(custom_fields, update=True)
        """
        for dt in custom_fields:
            docs = frappe.get_all("DocType Layout", {"document_type": dt})
            if docs:
                for d in docs:
                    doc = frappe.get_doc("DocType Layout", d.name)
                    doc.sync_fields()
                    doc.save()
        """


def create_custom_party_master_field(docfield, update=False, field_properity=None):
    doctype = docfield.get("document_type")
    if not doctype:
        frappe.throw(_("Missing document_type in docfield"))

    meta = frappe.get_meta(doctype)
    # options = options or {}

    # Check if field already exists
    field = meta.get_field("party_master")
    if field:
        if field.fieldtype != "Link" or field.options != "Party Master":
            frappe.log_error(
                _("Cannot create Party Master field in {0}").format(doctype),
                f"Field exists with conflicting properties: {field}",
            )
            return None
        if not update:
            return field.fieldname

    # If custom field is defined in options, use that
    if not field and docfield.get("party_master_custom_field"):
        field = meta.get_field(docfield.get("party_master_custom_field"))
        if field:
            return field.fieldname

    # Build fetch logic
    fetch_from = (
        f"{docfield.get('party_fieldname')}.party_master"
        if not docfield.get("party_type")
        else ""
    )
    fetch_if_empty = 1 if fetch_from else 0
    reqd = docfield.get("reqd", 0)
    # Determine where to insert the field
    insert_after = None
    if docfield.get("party_fieldname"):
        party_field = meta.get_field(docfield.get("party_fieldname"))
        if party_field:
            insert_after = party_field.fieldname

    # Create the custom field
    field_doc = {
        "fieldname": "party_master",
        "label": "Party Master",
        "fieldtype": "Link",
        "options": "Party Master",
        "insert_after": insert_after,
        "in_list_view": 1 if not meta.istable else 0,
        "in_standard_filter": 1 if not meta.istable else 0,
        "fetch_from": fetch_from,
        "fetch_if_empty": fetch_if_empty,
        "reqd": reqd,
        "translatable": 0,
    }
    customfield = create_custom_field(doctype, field_doc)

    return customfield.name


def get_fixtures_document_types():
    return [
        {
            "document_type": "Sales Invoice",
            "document_categories": "Selling DocType",
            "party_fieldname": "customer",
            "party_type": "Customer",
        },
        {
            "document_type": "Delivery Note",
            "document_categories": "Selling DocType",
            "party_fieldname": "customer",
            "party_type": "Customer",
        },
        {
            "document_type": "Sales Order",
            "document_categories": "Selling DocType",
            "party_fieldname": "customer",
            "party_type": "Customer",
        },
        {
            "document_type": "Purchase Invoice",
            "document_categories": "Purchasing DocType",
            "party_fieldname": "supplier",
            "party_type": "Supplier",
        },
        {
            "document_type": "Purchase Receipt",
            "document_categories": "Purchasing DocType",
            "party_fieldname": "supplier",
            "party_type": "Supplier",
        },
        {
            "document_type": "Purchase Order",
            "document_categories": "Purchasing DocType",
            "party_fieldname": "supplier",
            "party_type": "Supplier",
        },
        {
            "document_type": "Payment Entry",
            "document_categories": "Dynamic type As Parent",
            "party_fieldname": "party",
            "party_type_fieldname": "party_type",
            "is_dynamic_party_type": 1,
        },
        {
            "document_type": "Journal Entry Account",
            "parent_doctype": "Journal Entry",
            "document_categories": "Dynamic Type As Child",
            "party_fieldname": "party",
            "party_type_fieldname": "party_type",
            "is_dynamic_party_type": 1,
        },
        {
            "document_type": "Expense Claim",
            "document_categories": "Employee DocType",
            "party_fieldname": "employee",
            "party_type": "Employee",
        },
        {
            "document_type": "Payment Reconciliation",
            "reqd": 0,
            "document_categories": "Dynamic type As Parent",
            "party_fieldname": "party",
            "party_type_fieldname": "party_type",
            "is_dynamic_party_type": 1,
        },
    ]


def setup_initial_document_types():
    docs = get_fixtures_document_types()
    if not frappe.db.exists("Party Master Settings", "Party Master Settings"):
        settings = frappe.new_doc("Party Master Settings")
        settings.save()

    settings = frappe.get_doc("Party Master Settings")
    settings_document_types = settings.document_types or []
    exists = {d.get("document_type") for d in settings_document_types}

    for d in docs:
        doctype = d.get("document_type")
        if doctype in exists:
            continue

        parent = d.get("parent_doctype") or doctype
        if frappe.db.exists("DocType", doctype):
            new_row = {
                "document_type": doctype,
                "parent_doctype": parent,
                "party_fieldname": d.get("party_fieldname"),
                "party_type": d.get("party_type"),
                "party_type_fieldname": d.get("party_type_fieldname"),
                "is_dynamic_party_type": d.get("is_dynamic_party_type", 0),
                "document_categories": d.get("document_categories"),
            }
            settings.append("document_types", new_row)
            exists.add(doctype)

    settings.save()


# if Reset will Reset to Default
def setup_party_types_table(reset=False):
    party_types = frappe.db.get_all("Party Type", pluck="name", order_by="name asc")
    settings = frappe.get_doc("Party Master Settings")
    exist_party_type = [x.get("party_type") for x in settings.party_types]
    for d in party_types:
        if d in exist_party_type and not reset:
            continue
        if d not in exist_party_type or reset:
            row = party_types_dict(d)
            if d in exist_party_type:
                for x in settings.party_types:
                    if d == x.get("party_type"):
                        d.update(row)
            else:
                settings.append("party_types", row)

    # Remove party types that are not in the current list
    for d in exist_party_type:
        if d not in party_types:
            settings.party_types = [
                x for x in settings.party_types if x.get("party_type") != d
            ]
    settings.save()


def party_types_dict(party_type):
    return frappe._dict(
        {
            "party_type": party_type,
            "reqd": 1,
            "allowed": 1 if party_type in ("Customer", "Supplier") else 0,
            "rule_fieldname": (
                "default_currency" if party_type in ("Customer", "Supplier") else ""
            ),
        }
    )


@frappe.whitelist()
def get_party_type_party_master_rules_dict():
    result = {}
    doc = frappe.get_doc("Party Master Settings")
    for d in doc.get("party_types"):
        result.update(
            {
                d.get("party_type"): {
                    "reqd": d.get("reqd"),
                    "allowed": d.get("allowed"),
                    "rule_fieldname": d.get("rule_fieldname"),
                }
            }
        )

    return result


# Depricated
def setup_party_master_mapping_fields():
    common_maps = {
        "party_details": "Customer:customer_details\nSupplier:supplier_details",
        "type": "Customer:customer_type\nSupplier:supplier_type",
        "party_name": "Customer : customer_name\nSupplier:supplier_name\nEmployee: employee_name\nShareholder:title",
        "is_internal_party": "Customer:is_internal_customer\nSupplier:is_internal_supplier",
        "party_type_group": "Customer:customer_group\nSupplier:supplier_group",
        "group_type": "Customer:_\nSupplier:_\nEmployee:_\nShareholder:_",
    }
    fields = frappe.get_meta("Party Master").fields
    fields = [
        df.fieldname
        for df in fields
        if df.fieldname
        not in (
            "default_currency",
            "default_customer",
            "default_supplier",
            "is_group",
            "lft",
            "rgt",
            "old_parent",
            "party_type",
            "accounts",
        )
        and df.fieldtype not in ("Section Break", "Column Break", "Tab Break")
    ]
    settings = frappe.get_doc("Party Master Settings")
    for f in fields:
        if f in common_maps:
            settings.append(
                "party_master_fields", {"fieldname": f, "options": common_maps.get(f)}
            )
            continue
        settings.append("party_master_fields", {"fieldname": f})
    settings.save()
