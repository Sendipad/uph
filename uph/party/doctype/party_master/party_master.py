# Copyright (c) 2024, Abdo Ruzaqi and contributors
# For license information, please see license.txt
from frappe.query_builder.functions import Coalesce
from frappe.query_builder import Order

import frappe
import redis
from frappe.utils.caching import redis_cache
from pypika.functions import Sum
from frappe.utils import nowdate, add_months
from frappe.query_builder.functions import Count

from frappe.model.naming import set_name_by_naming_series, set_name_from_naming_options
import re
from frappe import _, scrub
from frappe.utils.nestedset import NestedSet
from frappe.contacts.address_and_contact import (
    delete_contact_and_address,
    load_address_and_contact,
)
from frappe.utils import cint, cstr, flt, get_formatted_email, today

from erpnext.accounts.party import (
    get_dashboard_info,
    validate_party_accounts,
    add_party_account,
    get_party_gle_account,
    get_party_gle_currency,
    get_party_account,
)  # noqa
from frappe import qb, scrub
from frappe.query_builder import Criterion, DocType, Case
from frappe.query_builder.functions import Concat, Locate, Sum
from pypika import CustomFunction

from functools import reduce
from frappe.query_builder.custom import ConstantColumn
from uph.party.utils import get_mapped_fieldnames
from uph.party.controllers.party import (
    get_party_type_validation_rule,
    update_linked_party_to_party_master_count,
)
import uph
from uph.party.controllers.queries import (
    get_party_master_parties,
    get_party_master_parties_db,
)


class PartyMaster(NestedSet):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from erpnext.accounts.doctype.allowed_to_transact_with.allowed_to_transact_with import AllowedToTransactWith
        from erpnext.selling.doctype.customer_credit_limit.customer_credit_limit import CustomerCreditLimit
        from erpnext.utilities.doctype.portal_user.portal_user import PortalUser
        from frappe.types import DF
        from uph.party.doctype.party_master_accounts.party_master_accounts import PartyMasterAccounts
        from uph.party.doctype.party_master_parties.party_master_parties import PartyMasterParties
        from uph.party.doctype.party_master_role.party_master_role import PartyMasterRole

        account_manager: DF.Link | None
        accounts: DF.Table[PartyMasterAccounts]
        business_registration_number: DF.Data | None
        companies: DF.Table[AllowedToTransactWith]
        credit_limits: DF.Table[CustomerCreditLimit]
        date_of_establishment: DF.Date | None
        default_currency: DF.Link | None
        default_price_list: DF.Link | None
        disabled: DF.Check
        disputed_reasons: DF.Text | None
        email_id: DF.ReadOnly | None
        enable_buying: DF.Check
        enable_selling: DF.Check
        enforce_party_analaytic_accounting_selection: DF.Check
        gender: DF.Link | None
        group_type: DF.Link | None
        has_secondary_role_party: DF.Check
        image: DF.AttachImage | None
        industry: DF.Link | None
        is_frozen: DF.Check
        is_group: DF.Check
        is_internal_party: DF.Check
        is_primary_role: DF.Check
        language: DF.Link | None
        legal_entity_type: DF.Literal["", "Sole Proprietor", "Partnership", "Corporation", "LLC", "NGO", "Freelancer", "Government", "Individual", "Other"]
        lft: DF.Int
        market_segment: DF.Link | None
        mobile_no: DF.ReadOnly | None
        naming_series: DF.Literal["{party_number}", ".{parent_party_master}.", "PM-{party_name}"]
        national_id: DF.Data | None
        old_parent: DF.Link | None
        parent_party_master: DF.Link | None
        parties: DF.Table[PartyMasterParties]
        party_details: DF.Text | None
        party_name: DF.Data
        party_number: DF.Data | None
        party_primary_address: DF.Link | None
        party_primary_contact: DF.Link | None
        party_type: DF.Link | None
        party_type_group: DF.DynamicLink | None
        passport_number: DF.Data | None
        payment_terms: DF.Link | None
        portal_users: DF.Table[PortalUser]
        primary_address: DF.Text | None
        primary_party_master: DF.Link | None
        represents_company: DF.Link | None
        rgt: DF.Int
        roles: DF.TableMultiSelect[PartyMasterRole]
        salutation: DF.Link | None
        status: DF.Literal["Active", "Disabled", "Closed", "Credit Hold", "Delinquent", "Disputed", "Dormant", "Write-Off", "Approved", "On Hold", "Under Review", "Terminated", "Suspended"]
        tax_category: DF.Link | None
        tax_id: DF.Data | None
        tax_withholding_category: DF.Link | None
        territory: DF.Link | None
        title: DF.Data | None
        total_linked_party: DF.Int
        type: DF.Literal["", "Company", "Individual", "Partnership"]
    # end: auto-generated types
    def onload(self):
        self.set("parties", get_party_master_parties(self.name))

    def autoname(self):
        if not self.party_number:
            self.numbering()
        self.name = self.party_number

    def numbering(self):
        if not self.flags.update_party_number:
            return

        if not self.parent_party_master and not self.party_number:
            frappe.throw(_("Party Number is Mandatory for Root Group Node"))

        number = get_next_party_master_number(self.parent_party_master, self.is_group)
        self.party_number = number

    def validate(self):
        self.validate_roles()

        if self.status == "Disputed" and not self.disputed_reasons:
            frappe.throw(
                _("Must Mention Reason to put This Party {0} as Disputed").format(
                    self.name
                )
            )
        if frappe.db.exists(
            "Party Master", {"party_name": self.party_name, "name": ["!=", self.name]}
        ):
            frappe.throw(_("Party Name {0} already exists").format(self.party_name))
        self.validate_roles()

    def validate_roles(self):
        exist_role = {self.party_type}
        if self.has_secondary_role_party or len(self.roles) > 0:
            roles = []
            for ptype in self.roles:
                if ptype.party_type_role not in exist_role:
                    exist_role.add(ptype.party_type_role)
                    roles.append(ptype)
                else:
                    frappe.msgprint(
                        _("Party Type {0} can not be duplicate").format(ptype), alert=1
                    )
            self.roles = roles

    def before_insert(self):
        self.set("parties", [])
        self.set_missing_value()
        self.party_name = self.party_name.strip()
        if self.is_group == 1 and not self.party_number:
            frappe.throw(_("Party Number is Mandatory for Group Node"))
        if not self.is_group and not self.party_number:
            self.party_number = self.name
        if not self.party_type:
            frappe.throw(_("Party Type is Mandatory"))

    def before_save(self):
        frappe.cache.hdel(uph.make_key("Party Master.parties"), self.name)
        old = self.get_doc_before_save()
        if old and self.parent_party_master != old.parent_party_master:
            self.flags.update_party_number = True
        if self.flags.update_party_number:
            self.numbering()
        if (
            old
            and self.party_number != old.party_number
            and not self.flags.update_party_number
        ):
            frappe.throw(_("You are not allowed to Change Party Number"))
        if len(self.roles) > 0 and self.has_secondary_role_party == 0:
            self.has_secondary_role_party = 1
        title = "{0}".format(self.party_name)
        duplicate_title = frappe.db.get_list(
            "Party Master", filters={"title": title, "name": ["!=", self.name]}
        )
        if duplicate_title:
            title = title + "({0})".format(_(self.party_type))
        self.title = title
        self.set_total_linked_party()
        self.set_missing_values()

    def set_missing_value(self):
        if (
            self.party_type in ("Customer", "Supplier")
            and not self.is_group
            and self.party_type_group is None
        ):
            # fetch Party group Type as Default in Parents
            self.group_type = "{0} Group".format(self.party_type)
            parent_group = self.get_parent()
            if parent_group and parent_group.get("party_type_group"):
                self.party_type_group = parent_group.party_type_group
        if self.is_group:
            self.salutation = ""
            self.gender = ""
            self.phone = ""
            self.type = ""
            self.territory = ""
            self.language = ""
            self.tax_id = ""
            self.tax_category = ""
            self.tax_withholding_category = ""
            self.represents_company = ""
            self.portal_users = []

    def set_total_linked_party(self):
        return update_linked_party_to_party_master_count(self)

    def set_missing_values(self):
        if not self.is_primary_role and not self.primary_party_master:
            self.set("is_primary_role", 1)
        elif not self.is_primary_role and self.primary_party_master:
            primary_role = frappe.get_doc("Party Master", self.primary_party_master)
            if self.party_type == primary_role.get("party_type"):
                return frappe.throw(
                    _("Setting Primary role of same Party Type is Not Allowed")
                )
            else:
                if not primary_role.has_accounting_dimension:
                    primary_role.has_accounting_dimension = 1
                    primary_role.save()

    def on_update(self):
        self.create_primary_contact()
        self.create_primary_address()
        key = "pm_parties_{0}".format(self.name)
        if frappe.cache.get_value(key):
            frappe.cache.delete_value(key)

        self.set_total_linked_party()

    def create_primary_contact(self):
        if not self.party_primary_contact and (self.mobile_no or self.email_id):
            contact = make_contact(self)
            self.db_set("party_primary_contact", contact.name)
            self.db_set("mobile_no", self.mobile_no)
            self.db_set("email_id", self.email_id)

    def create_primary_address(self):
        from frappe.contacts.doctype.address.address import get_address_display

        if self.flags.is_new_doc and self.get("address_line1"):
            address = make_address(self)
            address_display = get_address_display(address.name)

            self.db_set("party_primary_address", address.name)
            self.db_set("primary_address", address_display)

    def on_trash(self):
        if self.total_linked_party > 0 or get_party_master_parties(self.name):
            frappe.throw(
                _("Cannot delete Party Master that is linked to other Parties")
            )

    def after_rename(self, olddn, newdn, merge=False):
        if olddn == self.party_number:
            self.party_number = newdn
            self.db_set("party_number", newdn)

    @frappe.whitelist()
    def update_linked_parties_details(self):
        party_details = self.get_mapped_to_link_party()
        for p in self.get("linked_party"):
            changed = False
            party_doc = frappe.get_doc(p.party_type, p.party)
            for k, v in party_details.items():
                if v != party_doc.get(k):
                    changed = True
                    party_doc.set(k, v)
            if changed:
                party_doc.save()
                frappe.msgprint(
                    _("{0} Named {1}'s details have been updated").format(
                        _(self.party_type), p.party
                    ),
                    alert=1,
                )

    @frappe.whitelist()
    def set_party_master(self, selection):
        if not selection:
            frappe.throw(_("Must Select at least one Party"))
        if selection:
            for p in selection:
                party = frappe.get_doc(p.party_type, p.name)
                if party.get("party_master") is None or party.get("party_master") == "":
                    party.set("party_master", self.name)
                    party.save()
                    self.add_comment(
                        "Comment",
                        _("{0} has linked {1} {2}").format(
                            user, _(party.doctype), party.name
                        ),
                    )
            self.set_total_linked_party()
            self.save()
            self.reload()

    """ This Will Fetch simarlarty Parties(Customer ,Supplier or Employee) Based on party_type and Roles
        And for Unset party Master from the Parties and will order Return Result based On party
    """

    @frappe.whitelist()
    def fetch_parties_list(self, filters):
        unlinked = True
        search_text = self.party_name
        words = list(set(filter(None, search_text.split())))
        pt = []

        # Check if filters contain '=' (disables unlinked filter)
        if isinstance(filters, list) and filters[0][1] == "=":
            unlinked = False

        # Collect Party Types
        if self.party_type:
            pt.append(self.party_type)
        if self.roles and len(self.roles) > 0:
            for p in self.roles:
                pt.append(p.get("party_type_role"))

        queries = []
        for p in pt:
            doctype = DocType(p)
            party_name_field = f"{p.lower()}_name"

            # Set currency field based on Doctype
            if p in ("Customer", "Supplier"):
                currency = doctype.default_currency.as_("currency")
            elif p == "Employee":
                currency = doctype.salary_currency.as_("currency")
            else:
                currency = ConstantColumn("").as_(
                    "currency"
                )  # No currency for other doctypes

            # Ensure `LOCATE()` is properly formatted
            conditions = []
            # Define selected fields
            fields = [
                doctype.name.as_("name").as_("party"),
                getattr(doctype, party_name_field).as_("party_name"),
                currency,
                ConstantColumn(p).as_("party_type"),
            ]
            if unlinked:
                conditions = [
                    Case()
                    .when(getattr(doctype, party_name_field).like(f"%{word}%"), 1)
                    .else_(0)
                    for word in words
                ]
                fields.append(
                    sum(conditions).as_("match_count"),
                )
            # Build query
            q = frappe.qb.from_(doctype).select(*fields)

            # Add condition for unlinked records
            if unlinked:
                q = q.where(doctype.party_master.isnull())
            elif not unlinked:
                q = q.where(doctype.party_master == filters[0][2])
            # Add search condition for party_name
            similarty = False
            if similarty:
                conditions = [
                    getattr(doctype, party_name_field).like(f"%{w}%") for w in words
                ]
                q = q.where(reduce(lambda a, b: a | b, conditions))  # OR condition

            queries.append(q)

        # Combine queries using .union()
        final_query = queries[0]
        for q in queries[1:]:
            final_query = final_query.union(q)

        # Order by similarity score
        if len(conditions) > 0:
            final_query = final_query.orderby("match_count", order=frappe.qb.desc)

        # Execute Query
        results = final_query.run(as_dict=True)

        return results

    @frappe.whitelist()
    def assign_new_party_master_for_parties(self, selections):
        if not selections:
            frappe.throw(_("Must Select at Least One Party"))
        assign_parties = []
        for s in selections:
            new = s.get("new_party_master")
            party = s.get("party")
            ptype = s.get("party_type")

            pdict = frappe._dict(
                new_party_master=new,
                party=party,
                party_type=ptype,
            )
            if s.get("new_party_master") != self.name:
                pdict.update({"old_party_master": self.name})
            assign_parties.append(pdict)
        # frappe.throw("To Assign Parties: {0}".format(assign_parties))
        assign_party_master_for_selections_list(assign_parties)

    @frappe.whitelist()
    def set_secondary_party_roles(self, role):
        if not role:
            frappe.throw(_("Must Set at least One Secondary Role"))
        self.append("roles", {"party_type_role": role})
        if self.has_secondary_role_party == 0:
            self.has_secondary_role_party = 1
        self.save()

    @frappe.whitelist()
    def create_new_linked_party(self, currency):
        if self.party_type in ["Customer", "Supplier"] and currency is not None:
            if self.linked_party:
                exist_currency = [x.default_currency for x in self.linked_party]
                if currency in exist_currency:
                    return frappe.throw(
                        _("Party {0} Already has a {1} with this {2}").format(
                            self.party_name, _(self.party_type), currency
                        )
                    )
                self.flags.in_creating_new_link_party = True
                if currency not in exist_currency:
                    party_doc = self.get_mapped_to_link_party()
                    party_doc.update(
                        {
                            "default_currency": currency,
                            "doctype": self.party_type,
                        }
                    )
                    if naming := frappe.db.get_value(
                        "Party Settings", None, scrub(self.party_type + " Naming Rule")
                    ) in ["Party Master", "Party Master-Default Currency"]:
                        name = self.name
                        if naming == "Party Master-Default Currency":
                            name = name + "-{0}".format(currency)
                        party_doc.update(
                            {
                                "name": name,
                            }
                        )
                    new_party = frappe.get_doc(party_doc)
                    new_party.flags.in_creating_new_link_party = (
                        self.flags.in_creating_new_link_party
                    )
                    new_party.insert(ignore_permissions=True)
                    new_party.save()
                    frappe.msgprint(
                        _("New {0} Has Created been Inserted {1}").format(
                            _(self.party_type), new_party.name
                        ),
                        alert=1,
                    )


@frappe.whitelist()
def get_party_master_balances(company):
    from collections import defaultdict
    from frappe.query_builder import DocType, functions as fn

    cache_key = f"UPH:Party Master Tree Balances::{company}"

    # Use cache if available
    if cached := frappe.cache.get_value(cache_key):
        return cached

    GL = DocType("GL Entry")
    parties = get_party_master_parties_db(party_master=None)
    # Get (party_type, party) -> party_master map
    party_map = {(p["party_type"], p["party"]): p["party_master"] for p in parties}

    balances = (
        frappe.qb.from_(GL)
        .select(
            GL.party,
            GL.party_type,
            GL.account_currency.as_("currency"),
            (
                fn.Sum(GL.debit_in_account_currency)
                - fn.Sum(GL.credit_in_account_currency)
            ).as_("balance"),
        )
        .where((GL.company == company) & GL.party.isnotnull())
        .groupby(GL.party, GL.party_type)
    ).run(as_dict=True)

    party_balances = defaultdict(list)

    for entry in balances:
        key = (entry["party_type"], entry["party"])
        party_master = party_map.get(key)
        if not party_master or not entry["balance"]:
            continue
        party_balances[party_master].append(
            {"currency": entry["currency"], "amount": entry["balance"]}
        )

    result = [{"name": k, "balances": v} for k, v in party_balances.items()]
    frappe.cache.set_value(cache_key, result, expires_in_sec=300)
    return result


@frappe.whitelist()
def get_children(doctype, parent=None, company=None, **filters):
    filters = filters or {}

    # Remove frontend-added keys that don't exist in the DocType
    for key in ["cmd", "is_root"]:
        filters.pop(key, None)

    if parent:
        filters["parent_party_master"] = parent
    else:
        filters["parent_party_master"] = ""

    party_masters = frappe.get_all(
        "Party Master",
        filters=filters,
        fields=["name", "is_group", "party_type", "party_name"],
        order_by="name",
    )

    return [
        {
            "value": d.name,
            "title": d.party_name or d.name,
            "expandable": d.is_group,
            "is_group": d.is_group,
            "party_type": d.party_type,
            "party_name": d.party_name,
        }
        for d in party_masters
    ]


@frappe.whitelist()
def get_next_party_master_number(parent=None, is_group=0):
    """
    Generate the next party master number based on the parent party master and group status.
    """
    if not parent and not is_group:
        return

    # Fetch the parent party master document
    parent_doc = frappe.get_doc("Party Master", parent)
    parent_number = parent_doc.party_number

    # Group logic
    if is_group:

        def get_tree_level(pname):
            level = 0
            while pname:
                pdoc = frappe.get_doc("Party Master", pname)
                pname = pdoc.parent_party_master
                level += 1
            return level

        level = get_tree_level(parent)
        increment = (
            1000 if level == 0 else 100 if level == 1 else 10 if level == 2 else 1
        )

        number = frappe.db.sql(
            """
            SELECT IFNULL(MAX(CAST(SUBSTRING_INDEX(party_number, ' ', -1) AS UNSIGNED)), 0)
            FROM `tabParty Master`
            WHERE parent_party_master = %(parent)s AND is_group = 1
            """,
            {"parent": parent},
            as_list=1,
        )[0][0]

        return str(cint(parent_number) + increment).zfill(4)

    # Non-group logic

    max_suffix = frappe.db.sql(
        """
            SELECT IFNULL(MAX(CAST(SUBSTRING(party_number, %(start)s) AS UNSIGNED)), 0)
            FROM `tabParty Master`
            WHERE parent_party_master = %(parent)s AND is_group = 0 AND party_number LIKE %(prefix)s
            """,
        {
            "parent": parent,
            "prefix": parent_number + "%",
            "start": len(parent_number) + 1,  # 1-based indexing in SQL
        },
    )[0][0]
    new_suffix = cint(max_suffix) + 1
    return parent_number + str(new_suffix).zfill(5)


@frappe.whitelist()
def create_party_from_party_master(
    source_name, target_doctype, save=None, target_doc=None, rule_field_value=None
):
    from frappe.model.mapper import get_mapped_doc

    update = True if target_doc else False
    target_doc = frappe.get_doc(target_doctype, target_doc) if target_doc else None
    rules = get_party_type_validation_rule(target_doctype)
    rule_fieldname = rules.rule_fieldname if rules.allowed else None

    def set_missing_values(source, target):
        target.party_master = source.name  # back-reference
        # target.party_name = source.party_name

        # Optional: more logic based on doctype
        if target_doctype == "Customer":
            target.customer_name = source.party_name
            target.is_internal_customer = source.is_internal_party
            if source.party_type == "Customer":
                target.customer_group = source.party_type_group
            target.customer_details = source.party_details
            target.customer_type = (
                source.type
            )  # Assuming "type" is 'Company' or 'Individual'
        elif target_doctype == "Supplier":
            target.supplier_name = source.party_name
            if source.party_type == "Supplier":
                target.supplier_group = source.party_type_group
            target.supplier_type = source.type
        elif target_doctype == "Employee":
            target.employee_name = source.party_name
            target.gender = source.gender
            target.date_of_birth = (source.date_of_establishment,)
            target.salary_currency = source.default_currency
        if update and rule_fieldname and not rule_field_value:
            value = target_doc.get(rule_fieldname)
            target.set(rule_fieldname, value)
        if rule_fieldname and not update:
            target.set(rule_fieldname, rule_field_value)

    doc = get_mapped_doc(
        "Party Master",  # Source doctype
        source_name,  # Source docname
        {
            "Party Master": {
                "doctype": target_doctype,
                "validation": {"disabled": ["=", 0], "is_group": ["!=", 0]},
                "fieldmap": {
                    "name": "party_master",
                },
            }
        },
        target_doc,
        set_missing_values,
    )
    if save:
        doc.save()
    return doc


def get_party_key_fields(party_type):
    pt_dict = {
        "Customer": {
            "field": "customer",
            "party_name": "customer_name",
            "currency": "default_currency",
        },
        "Supplier": {
            "field": "supplier",
            "party_name": "supplier_name",
            "currency": "default_currency",
        },
        "Employee": {
            "field": "employee",
            "party_name": "employee_name",
            "currency": "salary_currency",
        },
        "Shareholder": "shareholder",
    }
    return pt_dict.get(party_type)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_unset_parties_list(
    doctype, txt, searchfield, start, page_len, filters, as_dict
):
    party_master = filters.get("party_master")
    unset = False
    if filters.get("unset_name") == 1:
        unset = True
    doc = frappe.get_cached_doc("Party Master", party_master)
    filter = [["party_master", "is", "not set"]]
    words = doc.party_name.split()
    ptype = [doc.party_type]

    if doc.has_secondary_role_party or len(doc.roles) > 0:
        for pt in doc.roles:
            ptype.append(pt.party_type_role)
    result = []
    for pt in ptype:
        pt_key_field = get_party_key_fields(pt)
        fields = ["name", pt_key_field.get("party_name"), pt_key_field.get("currency")]
        or_filters = []
        if unset:
            or_filters = [
                [pt_key_field.get("party_name"), "like", f"%{x}%"] for x in words
            ]

        r = frappe.db.get_all(pt, filters=filter, or_filters=or_filters, fields=fields)

        for row in r:
            row.update({"party_type": pt})
            result.append(row)
    return result


@frappe.whitelist()
def get_parties(party_master, fromdb=False, party_type=None):
    pm = frappe.get_doc("Party Master", party_master)
    key = f"pm_parties_{pm.name}"
    cache = frappe.cache()

    if cache.get_value(key) and not fromdb:
        return cache.get_value(key)

    parties = []
    party_type = party_type or frappe.db.get_all("Party Type", pluck="name")
    party_type = [p for p in party_type if frappe.get_meta(p).has_field("party_master")]

    queries = []

    for p in party_type:
        # Skip unmapped party_types
        result = get_mapped_fieldnames(p, ["party_fieldname", "currency_fieldname"])
        if not result:
            continue  # 🚫 Skip this party_type

        pnf, cf = result
        ptDocType = DocType(p)
        fields = [ptDocType.name, ConstantColumn(p).as_("party_type")]

        if pnf:
            fields.extend(
                [getattr(ptDocType, pnf), getattr(ptDocType, pnf).as_("party_name")]
            )
        if cf:
            fields.extend(
                [getattr(ptDocType, cf), getattr(ptDocType, cf).as_("currency")]
            )

        query = (
            frappe.qb.from_(ptDocType)
            .select(*fields)
            .where(ptDocType.party_master == pm.name)
        )
        queries.append(query)

    if queries:
        final_query = queries[0]
        for q in queries[1:]:
            final_query = final_query.union(q)
        parties = final_query.run(as_dict=True)

    cache.set_value(key, parties, expires_in_sec=3600)
    return {"parties": parties}


# OKKKKKKKK


@frappe.whitelist()
def create_party_master(doc):
    # party_name,is_group,party_type,phone_number=None,parent_party_master=None,party_number=None,details=None
    """Create new Party Master with validation"""
    doc = frappe._dict(doc)

    party = frappe.new_doc("Party Master")
    party.update(doc)

    if frappe.db.exists("Party Master", {"party_name": party.party_name}):
        frappe.throw(_("Party with this name already exists"))

    party.insert(ignore_permissions=True)
    return party.nam


@frappe.whitelist()
def check_similar_party_name(party_name, doctype="Party Master", start=0, page_len=5):
    party_name = party_name.split()
    PartyMaster = frappe.qb.DocType(doctype)

    if not party_name:  # Handle empty input
        return []

    # Build OR conditions using the | operator
    conditions = None
    for word in party_name:
        like_condition = PartyMaster.party_name.like(f"%{word}%")
        if conditions is None:
            conditions = like_condition
        else:
            conditions |= like_condition  # Combine with OR

    query = (
        frappe.qb.from_(PartyMaster)
        .select(PartyMaster.name, PartyMaster.party_name)
        .where(conditions)
        .limit(page_len)
        .offset(start)
    )

    return query.run(as_dict=True)


# @redis_cache
@frappe.whitelist()
def get_linked_parties_with_analytic_list(
    party_master, party=None, party_type="Customer", doctype=None, party_field=None
):
    # from uph.party.utils import get_party_type_from_doctype

    result = frappe._dict()

    if not party_master and not party:
        frappe.throw(_("Must Set Party Master"))

    filters = {"party_master": party_master}

    # Correctly map the field name
    party_field_name = frappe.scrub(f"{party_type}_name")
    fields = ["name", party_field_name]

    if party_type in ("Customer", "Supplier"):
        fields.append("default_currency")

    # Fetch parties
    parties = frappe.db.get_list(party_type, filters=filters, fields=fields)

    # Fetch related analytic accounting entries
    party_analytic_accountings = frappe.db.get_list(
        "Party Analytic Accounting",
        filters=filters,
        fields=["name as party_analytic_accounting", "analytic_name"],
    )

    # Process party data
    if parties:
        for p in parties:
            currency = p.get("default_currency", p.get("currency", ""))
            p.update({party_type.lower(): p.get("name"), "currency": currency})
        result["parties"] = parties

    # Add analytic accounting data
    if party_analytic_accountings:
        result["party_analytic_accountings"] = party_analytic_accountings
    return result


# It is better to create a report to get all static
@frappe.whitelist()
def get_totals_number_unlinked_parties(filters=None):
    ptype = frappe.get_all("Party Type")
    result = frappe._dict({})
    for p in ptype:
        if frappe.get_meta(p.get("name")).has_field("party_master"):
            result.update(
                {
                    p.get("name"): frappe.db.count(
                        p.get("name"), filters={"party_master": ["is", "not set"]}
                    )
                }
            )
    frappe.response["message"] = result
    return frappe.response["message"]


def assign_party_master_for_selections_list(assign_parties):
    for p in assign_parties:

        party_type, party = p.get("party_type"), p.get(
            "party"
        )  # Extract values from list

        doc = frappe.get_doc(party_type, party)
        doc.set("party_master", p.get("new_party_master"))
        doc.save()


@frappe.whitelist()
def assign_party_master_for_selection(old_party_master, new_party_master, selections):
    comments = []

    for p in selections:
        if not isinstance(p, list) or len(p) != 2:
            frappe.throw(
                _("Invalid data format for selection. Expected list of lists.")
            )

        party_type, party = p  # Extract values from list

        doc = frappe.get_doc(party_type, party)
        doc.set("party_master", new_party_master)
        doc.save()


def make_contact(args, is_primary_contact=1):
    values = {
        "doctype": "Contact",
        "is_primary_contact": is_primary_contact,
        "links": [{"link_doctype": "Party Master", "link_name": args.get("name")}],
    }

    if args.get("type") == "Individual":
        first, middle, last = parse_full_name(args.get("party_name"))
        values.update(
            {
                "first_name": first,
                "middle_name": middle,
                "last_name": last,
            }
        )
    else:
        values.update(
            {
                "company_name": args.get("party_name"),
            }
        )

    contact = frappe.get_doc(values)

    if args.get("email_id"):
        contact.add_email(args.get("email_id"), is_primary=True)
    if args.get("mobile_no"):
        contact.add_phone(args.get("mobile_no"), is_primary_mobile_no=True)

    if flags := args.get("flags"):
        contact.insert(ignore_permissions=flags.get("ignore_permissions"))
    else:
        contact.insert()

    return contact


def make_address(args, is_primary_address=1, is_shipping_address=1):
    reqd_fields = []
    for field in ["city", "country"]:
        if not args.get(field):
            reqd_fields.append("<li>" + field.title() + "</li>")

    if reqd_fields:
        msg = _("Following fields are mandatory to create address:")
        frappe.throw(
            "{} <br><br> <ul>{}</ul>".format(msg, "\n".join(reqd_fields)),
            title=_("Missing Values Required"),
        )

    party_name_key = "party_name"

    address = frappe.get_doc(
        {
            "doctype": "Address",
            "address_title": args.get(party_name_key),
            "address_line1": args.get("address_line1"),
            "address_line2": args.get("address_line2"),
            "city": args.get("city"),
            "state": args.get("state"),
            "pincode": args.get("pincode"),
            "country": args.get("country"),
            "is_primary_address": is_primary_address,
            "is_shipping_address": is_shipping_address,
            "links": [
                {"link_doctype": args.get("doctype"), "link_name": args.get("name")}
            ],
        }
    )

    if flags := args.get("flags"):
        address.insert(ignore_permissions=flags.get("ignore_permissions"))
    else:
        address.insert()

    return address


def parse_full_name(full_name: str) -> tuple[str, str | None, str | None]:
    """Parse full name into first name, middle name and last name"""
    names = full_name.split()
    first_name = names[0]
    middle_name = " ".join(names[1:-1]) if len(names) > 2 else None
    last_name = names[-1] if len(names) > 1 else None

    return first_name, middle_name, last_name
