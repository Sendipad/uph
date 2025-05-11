import frappe


def create_initial_records():
    if frappe.db.exists("Party Master", {"party_name": "Ruzaqi"}):
        return
    parent = create_party_master(
        "Debitors",
        is_group=1,
        party_type="Customer",
        party_group="Customer Group",
        territory="_Test Territory",
    )
    customer_parent = create_party_master(
        "Customer", is_group=1, parent_party_master=parent
    )
    create_party_master("Customer2", is_group=1, parent_party_master=parent)
    create_party_master(
        "Creditor",
        is_group=1,
        parent_party_master=None,
        party_type="Supplier",
        party_group="Supplier Group",
        territory="_Test Territory",
    )
    create_party_master(
        "Ruzaqi",
        parent_party_master=customer_parent,
        party_type="Customer",
        party_group="Customer Group",
        territory="_Test Territory",
    )

    return


def create_party_master(
    party_name,
    is_group=0,
    parent_party_master=None,
    party_type="Customer",
    party_group="Customer Group",
    territory="_Test Territory",
):
    if frappe.db.exists("Party Master", {"party_name": party_name}):
        return frappe.get_doc("Party Master", {"party_name": party_name})
    test_record = frappe.get_doc(
        {
            "doctype": "Party Master",
            "party_name": party_name,
            "is_group": is_group,
            "parent_party_master": parent_party_master,
            "party_type": party_type,
            "party_group": party_group,
            "territory": territory,
        }
    )

    return test_record.insert()
