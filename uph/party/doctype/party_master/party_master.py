# Copyright (c) 2024, Abdo Ruzaqi and contributors
# For license information, please see license.txt

import frappe

from frappe import _
from frappe.utils.nestedset import NestedSet

from frappe.query_builder import DocType, Case

from functools import reduce
from frappe.query_builder.custom import ConstantColumn
from uph.party.utils import get_mapped_fieldnames
from uph.party.controllers.party import (
    get_party_type_validation_rule,
    update_linked_party_to_party_master_count,
)
from uph.party.controllers.queries import (
    get_party_master_parties,
    get_party_master_parties_db,
)
from uph.party.controllers.normalization import NormalizationUtils


class PartyMaster(NestedSet):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from erpnext.accounts.doctype.allowed_to_transact_with.allowed_to_transact_with import (
            AllowedToTransactWith,
        )
        from erpnext.selling.doctype.customer_credit_limit.customer_credit_limit import (
            CustomerCreditLimit,
        )
        from erpnext.utilities.doctype.portal_user.portal_user import PortalUser
        from frappe.types import DF
        from uph.party.doctype.party_master_accounts.party_master_accounts import (
            PartyMasterAccounts,
        )
        from uph.party.doctype.party_master_parties.party_master_parties import (
            PartyMasterParties,
        )
        from uph.party.doctype.party_master_role.party_master_role import (
            PartyMasterRole,
        )

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
        legal_entity_type: DF.Literal[
            "",
            "Sole Proprietor",
            "Partnership",
            "Corporation",
            "LLC",
            "NGO",
            "Freelancer",
            "Government",
            "Individual",
            "Other",
        ]
        lft: DF.Int
        market_segment: DF.Link | None
        mobile_no: DF.ReadOnly | None
        naming_series: DF.Literal[
            "{party_number}", ".{parent_party_master}.", "PM-{party_name}"
        ]
        national_id: DF.Data | None
        normalized_party_name: DF.Data | None
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
        status: DF.Literal[
            "Active",
            "Disabled",
            "Closed",
            "Credit Hold",
            "Delinquent",
            "Disputed",
            "Dormant",
            "Write-Off",
            "Approved",
            "On Hold",
            "Under Review",
            "Terminated",
            "Suspended",
        ]
        tax_category: DF.Link | None
        tax_id: DF.Data | None
        tax_withholding_category: DF.Link | None
        territory: DF.Link | None
        title: DF.Data | None
        total_linked_party: DF.Int
        type: DF.Literal["", "Company", "Individual", "Partnership"]
    # end: auto-generated types

    # =========================================================================
    # Lifecycle Hooks
    # =========================================================================

    def onload(self):
        self.set("parties", get_party_master_parties(self.name))
        self.load_dashboard_info()

    def load_dashboard_info(self):
        from uph.party.controllers.queries import get_party_master_dashboard_info

        info = get_party_master_dashboard_info(self.name)
        self.set_onload("dashboard_info", info)

    def autoname(self):
        if not self.party_number:
            self.numbering()
        self.name = self.party_number

    def numbering(self):
        """Generate the next party number based on hierarchy."""
        # Skip if party_number is already set and not flagged for update
        if (
            not self.flags.update_party_number
            and self.party_number
            and not frappe.db.exists(self.doctype, {"party_number": self.party_number})
        ):
            return

        number = get_next_party_master_number(self.parent_party_master, self.is_group)
        if number:
            self.party_number = number
            return number

    # =========================================================================
    # Validation Methods (Refactored)
    # =========================================================================

    def validate(self):
        """Main validation entry point - delegates to focused validators."""
        self._validate_status_reasons()
        self._validate_party_name_uniqueness()
        self.validate_roles()
        self._validate_accounts_uniqueness()

    def _validate_accounts_uniqueness(self):
        """Ensure (company, currency) is unique in the accounts table."""
        seen = set()
        for row in self.accounts:
            key = (row.company, row.currency)
            if key in seen:
                frappe.throw(
                    _(
                        "Duplicate account configuration for Company {0} and Currency {1}"
                    ).format(row.company, row.currency or _("Any"))
                )
            seen.add(key)

    def _validate_status_reasons(self):
        """Validate that disputed parties have reasons."""
        if self.status == "Disputed" and not self.disputed_reasons:
            frappe.throw(
                _("Must Mention Reason to put This Party {0} as Disputed").format(
                    self.name
                )
            )

    def _validate_party_name_uniqueness(self):
        """Validate party name is unique."""
        if frappe.db.exists(
            "Party Master", {"party_name": self.party_name, "name": ["!=", self.name]}
        ):
            frappe.throw(_("Party Name {0} already exists").format(self.party_name))

    def validate_roles(self):
        """Validate that secondary roles don't have duplicates."""
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

    # =========================================================================
    # Before Save/Insert Hooks
    # =========================================================================

    def before_insert(self):
        self.set("parties", [])  # Ensure child table is initialized
        self.set_missing_value()
        self._prepare_party_name()
        self._prepare_party_number()
        self._validate_party_type_requirement()

    def _prepare_party_name(self):
        """Clean and normalize party name."""
        if self.party_name:
            self.party_name = self.party_name.strip()

    def _prepare_party_number(self):
        """Generate party number if not exists."""
        if not self.party_number:
            self.party_number = self.numbering()

    def _validate_party_type_requirement(self):
        """Validate party type is set when parent exists."""
        if self.flags.ignore_validate:
            return

        if not self.party_type and self.parent_party_master and not self.is_group:
            frappe.throw(_("Default Party Type is Mandatory"))

    def before_save(self):
        """Main before_save hook - delegates to focused methods."""
        self._update_normalized_name()
        self._invalidate_cache()
        self._handle_parent_change()
        self._validate_number_change()
        self._update_secondary_role_flag()
        self._generate_title()
        self._update_linked_count()
        self.set_missing_values()

    def _update_normalized_name(self):
        """Update normalized party name for deduplication."""
        if self.party_name:
            # Use consolidated normalization
            self.normalized_party_name = NormalizationUtils.normalize(self.party_name)

    def _invalidate_cache(self):
        """Invalidate relevant caches."""
        from uph.party.controllers.cache_utils import SmartCache

        SmartCache.invalidate_party_master_parties(self.name)

    def _handle_parent_change(self):
        """Handle parent party master changes."""
        old = self.get_doc_before_save()
        if old and self.parent_party_master != old.parent_party_master:
            self.flags.update_party_number = True
        if self.flags.update_party_number:
            self.numbering()

    def _validate_number_change(self):
        """Validate party number changes."""
        old = self.get_doc_before_save()
        if (
            old
            and self.party_number != old.party_number
            and not self.flags.update_party_number
        ):
            frappe.throw(_("You are not allowed to Change Party Number"))

    def _update_secondary_role_flag(self):
        """Update secondary role flag based on roles."""
        if len(self.roles) > 0 and self.has_secondary_role_party == 0:
            self.has_secondary_role_party = 1

    def _generate_title(self):
        """Generate title from party name."""
        self.title = self.party_name

    def _update_linked_count(self):
        """Update total linked party count."""
        self.set_total_linked_party()

    # =========================================================================
    # Missing Values & Defaults
    # =========================================================================

    def set_missing_value(self):
        """Set default values for new records."""
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
        """Set values that depend on other fields."""
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

    # =========================================================================
    # After Update Hooks
    # =========================================================================

    def on_update(self):
        self.create_primary_contact()
        self.create_primary_address()

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

    # =========================================================================
    # Delete & Rename
    # =========================================================================

    def on_trash(self):
        # Skip linked party check during merge operations
        if self.flags.get("in_merge"):
            return

        if self.total_linked_party > 0 or get_party_master_parties(self.name):
            frappe.throw(
                _("Cannot delete Party Master that is linked to other Parties")
            )

    def after_rename(self, olddn, newdn, merge=False):
        if olddn == self.party_number:
            self.party_number = newdn
            self.db_set("party_number", newdn)

    # =========================================================================
    # Party Linking Methods (with Permission Checks)
    # =========================================================================

    @frappe.whitelist()
    def update_linked_parties_details(self):
        """Update details of all linked parties."""
        _check_permission(self.doctype, self.name, "write")
        party_details = self.get_mapped_to_link_party()
        for p in self.get("parties"):
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
    def set_party_master(self, selection=None, **kwargs):
        """
        Link selected parties to this Party Master.
        Requires write permission on Party Master.
        """
        _check_permission(self.doctype, self.name, "write")

        if not selection and kwargs.get("data"):
            selection = kwargs.get("data")

        if not selection:
            frappe.throw(_("Must Select at least one Party"))

        for p in selection:
            party = frappe.get_doc(p.get("party_type"), p.get("name"))
            if party.get("party_master") is None or party.get("party_master") == "":
                party.set("party_master", self.name)
                party.save()
                self.add_comment(
                    "Comment",
                    _("{0} has linked {1} {2}").format(
                        frappe.session.user, _(party.doctype), party.name
                    ),
                )
        self.reload()
        self.save()

    @frappe.whitelist()
    def fetch_parties_list(self, filters):
        """
        Fetch similar parties for linking.
        Returns list of parties based on filters.
        """
        return self._build_parties_query(filters)

    def _build_parties_query(self, filters):
        """Build and execute query to fetch parties."""
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
                currency = ConstantColumn("").as_("currency")

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
                fields.append(sum(conditions).as_("match_count"))

            # Build query
            q = frappe.qb.from_(doctype).select(*fields)

            # Add condition for unlinked records
            if unlinked:
                q = q.where(doctype.party_master.isnull())
            elif not unlinked:
                q = q.where(doctype.party_master == filters[0][2])

            queries.append(q)

        # Combine queries using .union()
        final_query = queries[0]
        for q in queries[1:]:
            final_query = final_query.union(q)

        # Order by similarity score
        if len(fields) > 0 and unlinked:
            final_query = final_query.orderby("match_count", order=frappe.qb.desc)

        return final_query.run(as_dict=True)

    @frappe.whitelist()
    def assign_new_party_master_for_parties(self, selections):
        """
        Assign new Party Master to selected parties.
        Requires write permission on current Party Master.
        """
        _check_permission(self.doctype, self.name, "write")

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

        assign_party_master_for_selections_list(assign_parties)

    @frappe.whitelist()
    def set_secondary_party_roles(self, role):
        """Add secondary role to this Party Master."""
        _check_permission(self.doctype, self.name, "write")

        if not role:
            frappe.throw(_("Must Set at least One Secondary Role"))
        self.append("roles", {"party_type_role": role})
        if self.has_secondary_role_party == 0:
            self.has_secondary_role_party = 1
        self.save()


# =========================================================================
# Module-Level Functions
# =========================================================================


@frappe.whitelist()
def get_party_master_balances(company, name=None):
    _ensure_party_balance_permission(company)
    from collections import defaultdict
    from frappe.query_builder import DocType, functions as fn

    # Use cache only for full company balances (no specific names) or hashed batches
    import json
    import hashlib

    if isinstance(name, str):
        try:
            name = json.loads(name)
        except Exception:
            name = [name]

    # Generate a deterministic cache key for the set of names
    if name:
        sorted_names = sorted(name) if isinstance(name, list) else [name]
        name_hash = hashlib.md5(json.dumps(sorted_names).encode()).hexdigest()
        cache_key = f"UPH:Party Master Tree Balances::{company}::{name_hash}"
    else:
        cache_key = f"UPH:Party Master Tree Balances::{company}::ALL"

    if cached := frappe.cache.get_value(cache_key):
        return cached

    GL = DocType("GL Entry")

    # 1. Fetch all non-zero balance parties for this company once
    # This is much faster than querying level by level or for thousands of specific nodes
    gl_entries = frappe.db.sql(
        """
        SELECT 
            party, party_type, account_currency as currency,
            SUM(debit_in_account_currency - credit_in_account_currency) as balance
        FROM `tabGL Entry`
        WHERE company = %(company)s AND party IS NOT NULL AND is_cancelled = 0
        GROUP BY party, party_type, account_currency
        HAVING balance != 0
    """,
        {"company": company},
        as_dict=True,
    )

    if not gl_entries:
        return []

    # 2. Map (party_type, party) back to their Party Master
    # Group by party_type for batch fetching
    pt_to_parties = defaultdict(list)
    for entry in gl_entries:
        pt_to_parties[entry.party_type].append(entry.party)

    party_to_pm = {}
    for pt, p_names in pt_to_parties.items():
        if not frappe.db.exists("DocType", pt):
            continue

        # Check if party_master field exists in this doctype
        if not frappe.get_meta(pt).has_field("party_master"):
            continue

        pm_map = frappe.db.get_all(
            pt, filters={"name": ["in", p_names]}, fields=["name", "party_master"]
        )
        for m in pm_map:
            if m.party_master:
                party_to_pm[(pt, m.name)] = m.party_master

    if not party_to_pm:
        return []

    # 3. Handle Hierarchical Aggregation
    party_balances = defaultdict(list)
    if name:
        if isinstance(name, str):
            name = [name]

        # Map leaf PMs to requested PMs (self + ancestors)
        leaf_to_req = defaultdict(list)
        pm_names_in_gl = list(set(party_to_pm.values()))

        map_query = """
            SELECT leaf.name as leaf_name, req.name as req_name
            FROM `tabParty Master` leaf
            JOIN `tabParty Master` req ON leaf.lft >= req.lft AND leaf.rgt <= req.rgt
            WHERE req.name IN %(req_names)s 
              AND leaf.name IN %(leaf_names)s
              AND leaf.lft > 0 
              AND req.lft > 0
        """
        mappings = frappe.db.sql(
            map_query, {"req_names": name, "leaf_names": pm_names_in_gl}, as_dict=True
        )
        for m in mappings:
            leaf_to_req[m.leaf_name].append(m.req_name)

        # Init result for all requested names to avoid them "disappearing"
        for n in name:
            party_balances[n] = []
    else:
        # Full company: just map each party to its PM
        leaf_to_req = {pm: [pm] for pm in set(party_to_pm.values())}

    # 4. Final Summation
    for entry in gl_entries:
        pm_name = party_to_pm.get((entry.party_type, entry.party))
        if not pm_name:
            continue

        target_req_pms = leaf_to_req.get(pm_name, [])
        for req_pm in target_req_pms:
            # Sum by currency
            found = False
            for existing in party_balances[req_pm]:
                if existing["currency"] == entry.currency:
                    existing["amount"] += entry.balance
                    found = True
                    break
            if not found:
                party_balances[req_pm].append(
                    {"currency": entry.currency, "amount": entry.balance}
                )

    result = [{"name": k, "balances": v} for k, v in party_balances.items()]

    # Cache the result for 5 minutes
    frappe.cache.set_value(cache_key, result, expires_in_sec=300)

    return result


def _ensure_party_balance_permission(company=None):
    if not frappe.has_permission("Party Master", "read"):
        frappe.throw(_("Not permitted to read Party Master"), frappe.PermissionError)
    if not frappe.has_permission("GL Entry", "read"):
        frappe.throw(_("Not permitted to read GL Entry"), frappe.PermissionError)
    if company and not frappe.has_permission("Company", "read", doc=company):
        frappe.throw(
            _("Not permitted to read Company {0}").format(company),
            frappe.PermissionError,
        )
    if not frappe.get_single_value("Accounts Settings", "show_party_balance"):
        frappe.throw(
            _("Party balance visibility is disabled in Accounts Settings"),
            frappe.PermissionError,
        )


@frappe.whitelist()
def get_next_party_master_number(parent=None, is_group=0):
    """Hierarchical numbering with proper padding and sibling checks."""
    import traceback

    try:
        if not parent and not is_group:
            frappe.throw("Cannot create a leaf Party Master without a parent group")

        # Read configurable digits_count from settings (default 6)
        digits_count = (
            frappe.db.get_single_value("Party Master Settings", "digits_count") or 6
        )
        digits_count = int(digits_count)

        # ROOT GROUP
        if not parent and is_group:
            last_root = frappe.db.sql(
                """
                SELECT MAX(CAST(party_number AS UNSIGNED))
                FROM `tabParty Master`
                WHERE parent_party_master IS NULL AND is_group=1
            """
            )[0][0]
            return str(int(last_root or 0) + 1000).zfill(4)

        # SUBGROUPS
        if parent and is_group:
            parent_number = frappe.db.get_value("Party Master", parent, "party_number")
            if not parent_number:
                frappe.throw(f"Parent {parent} has no party number")

            last_sibling = frappe.db.sql(
                """
                SELECT MAX(CAST(party_number AS UNSIGNED))
                FROM `tabParty Master`
                WHERE parent_party_master=%s AND is_group=1
            """,
                (parent,),
            )[0][0]

            base = int(last_sibling or parent_number)
            return str(base + 100).zfill(len(parent_number))

        # LEAVES
        if parent and not is_group:
            parent_number = frappe.db.get_value("Party Master", parent, "party_number")
            if not parent_number:
                frappe.throw(f"Parent {parent} has no party number")

            last_leaf = frappe.db.sql(
                """
                SELECT MAX(CAST(party_number AS UNSIGNED))
                FROM `tabParty Master`
                WHERE parent_party_master=%s AND is_group=0
            """,
                (parent,),
            )[0][0]

            suffix = int(str(last_leaf)[-digits_count:] if last_leaf else 0) + 1
            return f"{parent_number}{suffix:0{digits_count}d}"

    except Exception as e:
        frappe.log_error(
            "Party Number Generation Error", f"{e}\n{traceback.format_exc()}"
        )
        raise


def make_contact(args, is_primary_contact=1):
    # Support both object and dict access for backward compatibility and internal calls
    if hasattr(args, "get"):
        get_val = args.get
    else:
        get_val = lambda k, default=None: getattr(args, k, default)

    values = {
        "doctype": "Contact",
        "is_primary_contact": is_primary_contact,
        "links": [{"link_doctype": "Party Master", "link_name": get_val("name")}],
    }

    if get_val("type") == "Individual":
        first, middle, last = parse_full_name(get_val("party_name"))
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
                "company_name": get_val("party_name"),
            }
        )

    contact = frappe.get_doc(values)

    if get_val("email_id"):
        contact.add_email(get_val("email_id"), is_primary=True)
    if get_val("mobile_no"):
        contact.add_phone(get_val("mobile_no"), is_primary_mobile_no=True)

    # Check for flags if it's a dict, otherwise assume standard insert
    if isinstance(args, dict) and (flags := args.get("flags")):
        contact.insert(ignore_permissions=flags.get("ignore_permissions"))
    else:
        contact.insert(ignore_permissions=True)

    return contact


def make_address(args, is_primary_address=1, is_shipping_address=1):
    # Support both object and dict access
    if hasattr(args, "get"):
        get_val = args.get
        doctype_val = args.get("doctype", "Party Master")
    else:
        get_val = lambda k, default=None: getattr(args, k, default)
        doctype_val = args.doctype

    reqd_fields = []
    for field in ["city", "country"]:
        if not get_val(field):
            reqd_fields.append("<li>" + field.title() + "</li>")

    # Only validate if explicit fields are missing (optional for quick creation)
    # Copied logic from git history but being lenient to avoid breaking existing flows

    party_name_key = "customer_name" if doctype_val == "Customer" else "supplier_name"
    # Fallback to party_name if customer/supplier name not found
    party_title = get_val(party_name_key) or get_val("party_name")

    address = frappe.get_doc(
        {
            "doctype": "Address",
            "address_title": party_title,
            "address_line1": get_val("address_line1"),
            "address_line2": get_val("address_line2"),
            "city": get_val("city"),
            "state": get_val("state"),
            "pincode": get_val("pincode"),
            "country": get_val("country"),
            "is_primary_address": is_primary_address,
            "is_shipping_address": is_shipping_address,
            "links": [{"link_doctype": doctype_val, "link_name": get_val("name")}],
        }
    )

    if isinstance(args, dict) and (flags := args.get("flags")):
        address.insert(ignore_permissions=flags.get("ignore_permissions"))
    else:
        address.insert(ignore_permissions=True)

    return address


# =========================================================================
# Module-Level Functions (for API compatibility)
# =========================================================================


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


@frappe.whitelist()
def create_party_master(doc):
    """Create new Party Master with validation"""
    if not frappe.has_permission("Party Master", "create"):
        frappe.throw(_("Not permitted to create Party Master"), frappe.PermissionError)
    doc = frappe._dict(doc)

    party = frappe.new_doc("Party Master")
    party.update(doc)

    if frappe.db.exists("Party Master", {"party_name": party.party_name}):
        frappe.throw(_("Party with this name already exists"))

    party.insert()
    return party.name


@frappe.whitelist()
def get_linked_parties_with_analytic_list(
    party_master, party=None, party_type="Customer", doctype=None, party_field=None
):
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


def parse_full_name(full_name: str) -> tuple[str, str | None, str | None]:
    """Parse full name into first name, middle name and last name"""
    names = full_name.split()
    first_name = names[0]
    middle_name = " ".join(names[1:-1]) if len(names) > 2 else None
    last_name = names[-1] if len(names) > 1 else None

    return first_name, middle_name, last_name


def get_set_cached_pm_list(reference_doctype, action="get", value=None):
    key = "_pm_list{0}".format(frappe.scrub(reference_doctype))
    cache = frappe.cache()
    if action == "get":
        return cache.get_value(key)
    if value:
        cache.set_value(key, value, expires_in_sec=3600)


@frappe.whitelist()
def get_children(doctype, parent=None, company=None, name=None, is_root=False):
    """Get child nodes with support for focused leaf view"""
    filters = [["docstatus", "<", 2]]

    # Handle focused leaf view
    if name and not parent:
        party = frappe.get_value(
            "Party Master",
            name,
            ["is_group", "parent_party_master", "party_name", "title"],
            as_dict=1,
        )
        if not party or not party.is_group:
            # Return parent's children but only include this leaf
            return [
                {
                    "value": name,
                    "title": party.title,
                    "party_name": party.party_name,
                    "expandable": 0,
                    "parent": party.parent_party_master,
                }
            ]

    # Normal parent-child relationship
    if parent:
        filters.append(["parent_party_master", "=", parent])
    else:
        filters.append(["parent_party_master", "=", ""])

    return frappe.get_all(
        "Party Master",
        fields=[
            "name as value",
            "title",
            "party_name",
            "is_group as expandable",
            "parent_party_master as parent",
        ],
        filters=filters,
        order_by="name",
    )


@frappe.whitelist()
def get_parents(doctype, name):
    """
    Get parent chain for a party master.
    """
    parents = []
    current = frappe.get_cached_doc("Party Master", name)

    while current and current.parent_party_master:
        parent = frappe.get_cached_doc("Party Master", current.parent_party_master)
        parents.append({"name": parent.name, "party_name": parent.party_name})
        current = parent

    return parents


@frappe.whitelist()
def get_party_master_details_with_parties(party_master_name):
    """
    Get party master details with all linked parties.
    """
    pm = frappe.get_cached_doc("Party Master", party_master_name)

    result = pm.as_dict()
    result["parties"] = get_party_master_parties(party_master_name)

    return result


# =========================================================================
# Permission Helpers
# =========================================================================


def _check_permission(doctype, name, permission="read"):
    """
    Check if user has permission on document.
    Raises frappe.PermissionError if not.
    """
    if not frappe.has_permission(doctype, permission, doc=name):
        frappe.throw(
            _("You don't have permission to {0} {1} {2}").format(
                permission, _(doctype), name
            ),
            frappe.PermissionError,
        )


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
            continue

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

    if filters.get("party_type"):
        ptype = [filters.get("party_type")]
    else:
        ptype = [doc.party_type]

        if doc.has_secondary_role_party or len(doc.roles) > 0:
            for pt in doc.roles:
                ptype.append(pt.party_type_role)
    result = []
    for pt in ptype:
        pt_key_field = get_party_key_fields(pt)
        if not pt_key_field:
            continue

    result = []
    for pt in ptype:
        pt_key_field = get_party_key_fields(pt)
        if not pt_key_field:
            continue

        name_field = pt_key_field.get("party_name")
        curr_field = pt_key_field.get("currency")

        fields = ["name", name_field, curr_field]

        or_filters = []
        if unset:
            or_filters = [[name_field, "like", f"%{x}%"] for x in words]

        r = frappe.db.get_all(
            pt,
            filters=filter,
            or_filters=or_filters,
            fields=fields,
            order_by=name_field,
        )

        for row in r:
            row.update(
                {
                    "party_type": pt,
                    "party_name": row.get(name_field),
                    "currency": row.get(curr_field),
                }
            )
            result.append(row)

    # Global sort by party_name
    result.sort(key=lambda x: x.get("party_name") or "")
    return result


@frappe.whitelist()
def create_party_from_party_master(
    source_name, target_doctype, rule_field_value=None, save=False
):
    import json
    from uph.party.utils import get_party_type_currency_field, get_party_type_name_field

    if save and isinstance(save, str):
        save = json.loads(save)

    pm = frappe.get_doc("Party Master", source_name)

    doc = frappe.new_doc(target_doctype)
    doc.party_master = pm.name

    # Map Name
    # Map Name
    name_field = get_party_type_name_field(target_doctype)
    if name_field:
        doc.set(name_field, pm.party_name)

    if rule_field_value:
        doc.set("name", f"{pm.name}-{rule_field_value}")

    # Map Currency / Rule Value
    # If rule_field_value is provided, it typically comes from the dialog (often currency)
    # But it could be a dynamic rule field. The JS logic handles the "which field" part by passing it as rule_field_value.
    # However, for currency specifically, we know the field name.
    # For dynamic rules, we might need to rely on the fact that the JS logic in 'create_party_for_party_master_dialog_from_doc'
    # sets 'rule_field_value' to the selected currency or rule link.
    # If it is currency, we set it to the currency field.

    currency_field = get_party_type_currency_field(target_doctype)
    if rule_field_value and currency_field:
        # Simple heuristic: if it looks like a currency or if we assume the dialog passed currency
        # The JS passes "rule_field_value: values.default_currency || values.rule_field_value"
        # If it was a dynamic rule field, we might need more context, but typically it is currency.
        # Let's check if the target has a specific field for this rule.
        # For now, we assume it maps to the currency field if one exists and rule_field_value is passed.
        # Or if the rule matches a specific fieldname.
        # But here we only receive the value.
        # Standard implementation assumes it is likely the currency.
        doc.set(currency_field, rule_field_value)

    # Map Group
    if target_doctype == "Customer" and pm.party_type_group:
        doc.customer_group = pm.party_type_group
    elif target_doctype == "Supplier" and pm.party_type_group:
        doc.supplier_group = pm.party_type_group

    # Fallback for currency if not passed but exists in PM
    if pm.default_currency and not doc.get(currency_field):
        if doc.meta.has_field(currency_field):
            doc.set(currency_field, pm.default_currency)

    # Basic fields
    common_map = {
        "mobile_no": "mobile_no",
        "email_id": "email_id",
        "tax_id": "tax_id",
        "territory": "territory",
    }
    for pm_field, target_field in common_map.items():
        if pm.get(pm_field) and doc.meta.has_field(target_field):
            doc.set(target_field, pm.get(pm_field))
    doc.flags.name_set = True
    if save:
        doc.insert()
        return doc

    return doc


@frappe.whitelist()
def map_party_to_target(source_name, target_doctype, rule_field_value=None, save=False):
    return create_party_from_party_master(
        source_name, target_doctype, rule_field_value, save
    )
