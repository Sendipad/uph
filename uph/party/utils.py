import frappe
from frappe.utils import unique
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

from uph.regional.arabic import money_in_words


def test_arabic():
    amount = 10000.00
    currency = "YER"
    frappe.local.lang == "ar"
    return money_in_words(amount, currency)


def get_common_party_with_party_master_fields():
    return {
        "party_name": "Customer : customer_name\nSupplier:supplier_name\nEmployee: employee_name",
        "is_internal_party": "Customer:is_internal_customer\nSupplier:is_internal_supplier",
        "party_type_group": "Customer:customer_group\nSupplier:supplier_group",
        "group_type": "Customer:_\nSupplier:_\nEmployee:_\nShareholder:_",
    }


def get_mapped_fieldnames(doctype, fields=None):

    if doctype == "Journal Entry":
        doctype = "Journal Entry Account"
    mapped = {
        "Sales Invoice": frappe._dict(
            party_fieldname="customer",
            isdynamic_party_type=0,
            party_type="Customer",
            currency_fieldname="currency",
            party_type_fieldname=None,
        ),
        "Sales Order": frappe._dict(
            party_fieldname="customer",
            isdynamic_party_type=0,
            party_type="Customer",
            currency_fieldname="currency",
            party_type_fieldname=None,
        ),
        "Delivery Note": frappe._dict(
            party_fieldname="customer",
            isdynamic_party_type=0,
            party_type="Customer",
            currency_fieldname="currency",
            party_type_fieldname=None,
        ),
        "Customer": frappe._dict(
            party_fieldname="name",
            isdynamic_party_type=0,
            party_type="Customer",
            currency_fieldname="default_currency",
            party_type_fieldname=None,
            party_name_fieldname="customer_name",
        ),
        "Payment Entry": frappe._dict(
            party_fieldname="party",
            isdynamic_party_type=1,
            party_type=None,
            party_type_fieldname="party_type",
            currency_fieldname=None,
        ),
        "Journal Entry Account": frappe._dict(
            party_fieldname="party",
            isdynamic_party_type=1,
            party_type=None,
            party_type_fieldname="party_type",
            currency_fieldname="account_currency",
        ),
        "Supplier": frappe._dict(
            party_fieldname="name",
            isdynamic_party_type=0,
            party_type="Supplier",
            currency_fieldname="default_currency",
            party_type_fieldname=None,
            party_name_fieldname="supplier_name",
        ),
        "Employee": frappe._dict(
            party_fieldname="name",
            isdynamic_party_type=0,
            party_type="Employee",
            currency_fieldname="salary_currency",
            party_type_fieldname=None,
            party_name_fieldname="employee_name",
        ),
        "ShareHolder": frappe._dict(
            party_fieldname="name",
            isdynamic_party_type=0,
            party_type="ShareHolder",
            currency_fieldname=None,
            party_type_fieldname=None,
        ),
        "Purchase Invoice": frappe._dict(
            party_fieldname="supplier",
            isdynamic_party_type=0,
            party_type="Supplier",
            currency_fieldname="currency",
            party_type_fieldname=None,
        ),
        "Purchase Order": frappe._dict(
            party_fieldname="supplier",
            isdynamic_party_type=0,
            party_type="Supplier",
            currency_fieldname="currency",
            party_type_fieldname=None,
        ),
        "Purchase Reciept": frappe._dict(
            party_fieldname="supplier",
            isdynamic_party_type=0,
            party_type="Supplier",
            currency_fieldname="currency",
            party_type_fieldname=None,
        ),
        "Expense Claim": frappe._dict(
            party_fieldname="employee",
            isdynamic_party_type=0,
            party_type="Employee",
            currency_fieldname="currency",
            party_type_fieldname=None,
        ),
    }
    result = mapped.get(doctype, None)
    if not result:
        return None

    if fields:
        if isinstance(fields, str):
            return result.get(fields, None)
        elif isinstance(fields, (list, tuple)):
            return tuple(result.get(field, None) for field in fields)
    return result


def get_party_type_currency_field(party_type):
    cf = {
        "Customer": "default_currency",
        "Supplier": "default_currency",
        "Employee": "salary_currency",
    }
    return cf.get(party_type, "")


def get_party_type_name_field(party_type):
    cf = {
        "Customer": "customer_name",
        "Supplier": "supplier_name",
        "Employee": "employee_name",
        "Shareholder": "title",
    }
    return cf.get(party_type)


def get_transactional_doctype_list_to_add_pm():
    dt = [
        "Sales Invoice",
        "Sales Order",
        "Purchase Order",
        "Delivery Note",
        "Purchase Receipt",
        "Purchase Invoice",
        "Payment Entry",
        "Journal Entry",
    ]
    if frappe.db.exists("DocType", "Expense Claim"):
        dt.append("Expense Claim")

    return dt


def get_party_field_in_doctype(doctype):
    cf = {
        "Sales Invoice": "customer",
        "Sales Order": "customer",
        "Purchase Order": "supplier",
        "Delivery Note": "customer",
        "Purchase Receipt": "supplier",
        "Purchase Invoice": "supplier",
        "Payment Entry": "party",
        "Journal Entry Account": "party",
        "Expense Claim": "employee",
        "POS Profile": "customer",
        "POS Invoice": "customer",
    }
    return cf.get(doctype)


def get_party_type_party_field_from_doc(doc, value=False, party_type=None):

    if doc.doctype in ("Payment Entry", "Journal Entry Account") and party_type is None:
        party_type = doc.party_type

    list_dict = {
        "Sales Invoice": {"party_type": "Customer", "party": "customer"},
        "Sales Order": {"party_type": "Customer", "party": "customer"},
        "Purchase Order": {"party_type": "Supplier", "party": "supplier"},
        "Delivery Note": {"party_type": "Customer", "party": "customer"},
        "Purchase Receipt": {"party_type": "Supplier", "party": "supplier"},
        "Purchase Invoice": {"party_type": "Supplier", "party": "supplier"},
        "Payment Entry": {"party_type": party_type, "party": "party"},
        "Journal Entry Account": {"party_type": party_type, "party": "party"},
        "Expense Claim": {"party_type": "Employee", "party": "employee"},
    }
    if doc.doctype in list_dict.keys() and not value:
        return list_dict.get(doc.doctype)
    else:
        fields = list_dict.get(doc.doctype)
        return {
            "party_type": fields.get("party_type"),
            "party": doc.get(fields.get("party")),
        }


def get_party_type_from_doctype(doctype):
    pt_map = {
        "Sales Invoice": "Customer",
        "Sales Order": "Customer",
        "Purchase Order": "Supplier",
        "Delivery Note": "Customer",
        "Purchase Receipt": "Supplier",
        "Purchase Invoice": "Supplier",
        "Journal Entry Account": "party",
        "Expense Claim": "Employee",
    }
    if pt_map.get(doctype):
        return pt_map.get(doctype)
    return ""


def setup_party_master_custom_fields():
    dt_df = frappe._dict()
    doclist = frappe.get_hooks("tx_doctype_with_party_master")
    doclist.extend(["POS Invoice", "POS Profile"])
    for d in doclist:
        # Use `d` directly as the Doctype name
        doctype = d  # ✅ No need for getattr()

        # Skip if the Doctype doesn't exist (except for "Expense Claim")
        if doctype == "Expense Claim" and not frappe.db.exists("DocType", doctype):
            continue

        # Get the party field in the Doctype
        party_field = get_party_field_in_doctype(d)
        fetch_from = f"doc.{party_field}.party_master"
        mandatory_depends_on = "eval:frm.is_new()===1"
        # Determine where to insert the field
        insert_after = (
            "naming_series"
            if frappe.get_meta(d).has_field("naming_series")
            else party_field
        )
        if doctype == "Journal Entry Account":
            insert_after = "bank_account"
            mandatory_depends_on = mandatory_depends_on + "doc.party_type && doc.party"
        if doctype == "Payment Reconciliation":
            insert_after = "company"

        # Add field definition to dictionary
        dt_df.update(
            {
                doctype: frappe._dict(
                    fieldname="party_master",
                    fieldtype="Link",
                    options="Party Master",
                    fetch_if_empty=1,
                    fetch_from=fetch_from,
                    allow_on_submit=1,
                    mandatory_depends_on="'{0}'".format(mandatory_depends_on),
                    in_list_view=1,
                    in_standard_filter=1,
                    bold=1,
                    read_only_depends_on="eval:doc.docstatus==1",
                    label="Party Master",
                    insert_after=insert_after,
                )
            }
        )

    # Create custom fields
    for dt, df in dt_df.items():
        try:
            if cf := frappe.get_list(
                "Custom Field",
                filters={"dt": dt, "fieldname": "party_master"},
                fields=["name"],
            ):
                dfdoc = frappe.get_doc("Custom Field", cf[0].get("name"))
                for key, value in df.items():
                    dfdoc.set(key, value)
                dfdoc.save()
                continue
            create_custom_field(dt, dt_df.get(dt))
        except Exception as e:
            frappe.log_error(e)
            frappe.db.rollback()
            raise e
        finally:
            frappe.db.commit()


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_party_master_list(doctype, txt, searchfield, start, page_len, filters):
    doctype = "Party Master"
    meta = frappe.get_meta(doctype)
    party_type_cond = ""
    and_cond = ["docstatus < 2"]
    fields = ["name"]
    searchfield = meta.get_search_fields()

    if meta.get("show_title_field_in_link") and meta.get("title_field"):
        tf = meta.get("title_field")
        if tf not in searchfield:
            searchfield.insert(1, tf)
        fields.append(meta.get("title_field"))
    if len(searchfield) > 0:
        fields.extend(searchfield)
    fields = unique(fields)
    if pt := filters.get("party_type"):
        parent_party_role = frappe.db.get_all(
            "Party Master Role", filters={"party_type_role": pt}, pluck="parent"
        )
        parent_party_role = tuple(parent_party_role)
        party_type_cond = f" and (party_type = '{pt}' OR name IN {parent_party_role})"
    elif not filters.get("party_type") and filters.get("on_doctype"):
        pt = get_party_type_from_doctype(filters.get("on_doctype"))
        parent_party_role = frappe.db.get_all(
            "Party Master Role", filters={"party_type_role": pt}, pluck="parent"
        )
        party_type_cond = " and (party_type ={0} OR name in {1})".format(
            pt, set(parent_party_role)
        )

    if isinstance(filters, dict):
        filters_items = filters.items()
        for key, value in filters_items:
            if key != "party_type" and key != "on_doctype":
                if meta.has_field(key):
                    and_cond.append(
                        "{key} = {value}".format(key=key, value=filters.get(key))
                    )

    elif isinstance(filters, list):
        for f in filters:
            if meta.has_field(f[1]):
                if isinstance(f[3], list):
                    and_cond += f" and {f[1]} {f[2]} {tuple(f[3])}"
                else:
                    and_cond += f" and {f[1]} {f[2]} {f[3]}"
    search_parm = ""
    if len(searchfield) > 0:
        txt_parm = " or ".join(field + " like %(txt)s" for field in searchfield)
        search_parm = f"and ({txt_parm})"

    query = frappe.db.sql(
        f"""
                        select {fields} from `tabParty Master`
                        where {and_cond} {party_type_cond} {key} 
                        order by
			(case when locate(%(_txt)s, name) > 0 then locate(%(_txt)s, name) else 99999 end),
			(case when locate(%(_txt)s, party_name) > 0 then locate(%(_txt)s, party_name) else 99999 end),
			idx desc,
			name, party_name
		limit {page_len} offset {start}""".format(
            fields=", ".join(fields),
            key=search_parm,
            and_cond=" and ".join(and_cond),
            party_type_cond=party_type_cond,
            start=start,
            page_len=page_len,
            txt="%(txt)s",
        ),
        {
            "txt": "%%%s%%" % txt,
            "_txt": txt.replace("%", ""),
            "start": start,
            "page_len": page_len,
        },
    )

    return query
