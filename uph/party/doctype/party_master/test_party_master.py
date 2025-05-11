# Copyright (c) 2024, Abdo Ruzaqi and Contributors
# See license.txt
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime
from uph.party.controllers.test.test_create_pm_records import (
    create_initial_records,
    create_party_master,
)


# Please Check test in /uph/party/controllers/test for All test methods
def unique_party_name(base="Test Party"):
    return f"{base} {now_datetime().strftime('%H%M%S%f')}"


class TestPartyMaster(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_initial_records()

    def setUp(self):
        self.parent_party_master = create_party_master(
            party_name=unique_party_name("Parent PM"), is_group=1, party_type="Customer"
        )
        self.child_party_master = create_party_master(
            party_name=unique_party_name("Child PM"),
            is_group=0,
            party_type="Customer",
            parent_party_master=self.parent_party_master.name,
        )

    def tearDown(self):
        frappe.db.rollback()

    def test_duplicate_party_name_should_raise_error(self):
        parent = frappe.get_doc("Party Master", {"party_name": "Debitor"})
        with self.assertRaises(frappe.UniqueValidationError):
            create_party_master(
                party_name="Debitor",  # Same name triggers unique constraint
                is_group=1,
                parent_party_master=parent.name,
                party_type="Customer",
            )

    def test_party_number_should_start_with_parent_number(self):
        child = frappe.get_doc("Party Master", self.child_party_master.name)
        parent = frappe.get_doc("Party Master", child.parent_party_master)
        self.assertTrue(child.party_number.startswith(parent.party_number))

    def test_party_number_changes_when_parent_changes(self):
        new_parent = create_party_master(
            party_name=unique_party_name("New Parent"),
            is_group=1,
            party_type="Customer",
        )

        old_number = self.child_party_master.party_number
        self.child_party_master.parent_party_master = new_parent.name
        self.child_party_master.save()

        self.assertNotEqual(self.child_party_master.party_number, old_number)
        self.assertTrue(
            self.child_party_master.party_number.startswith(new_parent.party_number)
        )

    def test_parent_change_updates_existing_party_number_reference(self):
        existing = frappe.get_doc("Party Master", {"party_name": "Ruzaqi"})
        old_parent = frappe.get_doc("Party Master", existing.parent_party_master)

        new_parent = create_party_master(
            party_name=unique_party_name("Alt Parent"),
            is_group=1,
            parent_party_master="Debitor",
            party_type="Customer",
        )

        new_child = create_party_master(
            party_name=unique_party_name("Swappable Child"),
            is_group=0,
            parent_party_master=new_parent.name,
            party_type="Customer",
        )

        new_child.parent_party_master = old_parent.name
        new_child.save()

        self.assertTrue(new_child.party_number.startswith(old_parent.party_number))

    def test_rename_party_master_with_merge_should_fail_if_linked(self):
        # Create another Party Master to be target of merge
        target_pm = create_party_master(
            party_name=unique_party_name("Target PM"),
            is_group=0,
            party_type="Customer",
            parent_party_master=self.parent_party_master.name,
        )

        # Link current child PM to a Customer
        frappe.get_doc(
            {
                "doctype": "Customer",
                "default_currency": "USD",
                "customer_name": unique_party_name("Customer"),
                "party_master": self.child_party_master.name,
            }
        ).insert()

        # Attempt to rename with merge=True → should fail
        with self.assertRaises(frappe.ValidationError):
            frappe.rename_doc(
                doctype="Party Master",
                old=self.child_party_master.name,
                new=target_pm.name,
                merge=True,
                force=True,  # usually needed in tests
            )

    def test_delete_party_master_fails_if_linked_to_customer(self):
        frappe.get_doc(
            {
                "doctype": "Customer",
                "default_currency": "USD",
                "customer_name": unique_party_name("Delete Test Customer"),
                "party_master": self.child_party_master.name,
            }
        ).insert()

        with self.assertRaises(frappe.LinkExistsError):
            frappe.delete_doc("Party Master", self.child_party_master.name)


"""
def test_get_parties():
    party_master='131000004'
    return get_parties(party_master,fromdb=True)

def test_cached_parties():
    cache=frappe.cache()
    key='pm_parties_131000004'
    if cache.get_value(key):
        return cache.get_value(key)
    return test_get_parties()

def test_check_similar_party_name():
    pn='علي احم'
    return check_similar_party_name(pn)

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_query(doctype, txt, searchfield, start, page_len, filters):
    from frappe.query_builder import DocType, Order, Case
    from frappe.query_builder.functions import Coalesce
    from frappe.query_builder.functions import Concat, Locate, Sum
    #from frappe.query_builder import and_, or_

    PartyMaster = DocType("Party Master")
    PartyMasterRole = DocType("Party Master Role")
    reference_doctype = filters.get("reference_doctype") or filters.get("on_doctype")
    meta = frappe.get_meta(doctype)
    if not  reference_doctype and on_doctype:
        reference_doctype=on_doctype
    result=None
    meta = frappe.get_meta(doctype)
    fields = ["name"]
    if (not txt or txt == '') and reference_doctype:
        result=get_set_cached_pm_list(reference_doctype)
        if result:
            return result
    # Get search fields
    search_fields = meta.get_search_fields()
    if meta.get("show_title_field_in_link") and meta.get("title_field"):
        title_field = meta.get("title_field")
        if title_field not in search_fields:
            search_fields.insert(1, title_field)
        fields.append(title_field)
    fields.extend(search_fields)
    fields = list(set(fields))  # Ensure unique fields

    # Base condition: Exclude deleted documents
    combined_conditions = and_(
        PartyMaster.docstatus < 2,
        PartyMaster.disabled == 0,
        PartyMaster.is_group == 0
    )

    # Party Type Filtering using LEFT JOIN Subquery
    party_type = filters.get("party_type") if isinstance(filters, dict) else None
    on_doctype = filters.get("on_doctype") if isinstance(filters, dict) else None

    if not party_type and on_doctype:
        party_type = get_party_type_from_doctype(on_doctype)

     # Party Type Filtering
    if party_type:
        role_subquery = (
            frappe.qb.from_(PartyMasterRole)
            .select(PartyMasterRole.parent)
            .where(PartyMasterRole.party_type_role == party_type)
            .where(PartyMasterRole.parent == PartyMaster.name)
        )
        combined_conditions = combined_conditions & (
            (PartyMaster.party_type == party_type) | 
            Exists(role_subquery)
        )

    # Handle Filters (Supports both Dict and List of Lists)
    if isinstance(filters, dict):
        for key, value in filters.items():
            if key not in ["party_type", "on_doctype", "reference_doctype"] and meta.has_field(key):
                combined_conditions = combined_conditions & (PartyMaster[key] == value)

    elif isinstance(filters, list):
        for f in filters:
            if len(f) != 3:
                continue  # Ignore malformed filters

            field, operator, value = f
            if not meta.has_field(field):
                continue  # Ignore invalid fields

            if operator.lower() in ["=", "!=", ">", "<", ">=", "<="]:
                conditions.append(getattr(PartyMaster[field], operator)(value))
            elif operator.lower() == "like":
                conditions.append(PartyMaster[field].like(f"%{value}%"))
            elif operator.lower() == "in" and isinstance(value, (list, tuple)):
                conditions.append(PartyMaster[field].isin(value))
            elif operator.lower() == "between" and isinstance(value, (list, tuple)) and len(value) == 2:
                conditions.append((PartyMaster[field] >= value[0]) & (PartyMaster[field] <= value[1]))

    # Search Condition
    search_conditions = [
        PartyMaster[field].like(f"%{txt}%") for field in search_fields
    ]
    if search_conditions and txt:
        combined_conditions = combined_conditions & or_(*search_conditions)
    # **Usage Count Subquery (Only If reference_doctype is Provided)**
    usage_count_field = None
    if reference_doctype:
        ReferenceDoc = DocType(reference_doctype)
        three_months_ago = add_months(nowdate(), -3)

        usage_subquery = (
            frappe.qb.from_(ReferenceDoc)
            .select(Count(ReferenceDoc.name))
            .where(ReferenceDoc.party_master == PartyMaster.name)
            .where(ReferenceDoc.creation >= three_months_ago)
        )

        usage_count_field = Coalesce(usage_subquery, 0).as_("usage_count")

    # [Previous code remains the same until order_by section]

    # Corrected order_by configuration
    order_by = []

    # Add usage count ordering if exists
    if usage_count_field:
        order_by.append((usage_count_field, Order.desc))

    # Add case statements
    order_by.extend([
        Case().when(Locate(txt, PartyMaster.name) > 0, Locate(txt, PartyMaster.name)).else_(99999),
        Case().when(Locate(txt, PartyMaster.party_name) > 0, Locate(txt, PartyMaster.party_name)).else_(99999)
    ])

    # Add regular fields with proper tuple syntax
    order_by.extend([
        (PartyMaster.idx, Order.desc),
        (PartyMaster.name, Order.asc),
        (PartyMaster.party_name, Order.asc)
    ])

    # Filter out None values
    order_by = [o for o in order_by if o is not None]

    # Build final query
    select_fields = fields.copy()
    if usage_count_field:
        select_fields.append(usage_count_field)
    query = (
        frappe.qb.from_(PartyMaster)
        .select(*select_fields)
        .where(combined_conditions)  # Pass single combined condition
        .orderby(*order_by)
        .limit(page_len)
        .offset(start)
        )

    result = query.run(as_dict=True)
    if (not txt or txt == '') and filters.get('reference_doctype'):
        get_set_cached_pm_list(reference_doctype,action='set',value=result)
    return result
"""
