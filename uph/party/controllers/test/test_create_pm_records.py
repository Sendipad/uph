import frappe
from frappe import _


def create_initial_records():
    """
    Create initial Party Master records for demonstration/testing purposes.
    Creates a hierarchy of party masters with different types.
    """
    try:
        # Check if sample records already exist
        if frappe.db.exists("Party Master", {"party_name": "Ruzaqi"}):
            frappe.msgprint(_("Sample Party Master records already exist"))
            return

        # Create parent groups
        parent = create_party_master(
            party_name="Debitors",
            is_group=1,
            party_type="Customer",
        )

        customer_parent = create_party_master(
            party_name="Customer", is_group=1, parent_party_master=parent.name
        )

        create_party_master(
            party_name="Customer2", is_group=1, parent_party_master=parent.name
        )

        create_party_master(
            party_name="Creditor",
            is_group=1,
            parent_party_master=None,
            party_type="Supplier",
        )

        # Create sample customer
        create_party_master(
            party_name="Ruzaqi",
            parent_party_master=customer_parent.name,
            party_type="Customer",
        )

        frappe.db.commit()
        frappe.msgprint(_("Successfully created sample Party Master records"))

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(_("Error creating Party Master records"), str(e))
        raise


def create_party_master(
    party_name, is_group=0, parent_party_master=None, party_type="Customer", **kwargs
):
    """
    Create a new Party Master record

    Args:
        party_name (str): Name of the party
        is_group (int): Whether this is a group (1) or individual (0)
        parent_party_master (str): Name of parent Party Master
        party_type (str): Type of party (Customer, Supplier, etc.)
        **kwargs: Additional fields to set on the Party Master

    Returns:
        Party Master document object
    """
    try:
        # Check if party already exists
        existing = frappe.db.exists("Party Master", {"party_name": party_name})
        if existing:
            return frappe.get_doc("Party Master", existing)

        # Validate parent exists if specified
        if parent_party_master and not frappe.db.exists(
            "Party Master", parent_party_master
        ):
            frappe.throw(
                _("Parent Party Master {0} does not exist").format(parent_party_master)
            )

        # Create new Party Master
        party = frappe.get_doc(
            {
                "doctype": "Party Master",
                "party_name": party_name,
                "is_group": is_group,
                "parent_party_master": parent_party_master,
                "party_type": party_type,
                **kwargs,
            }
        )

        party.insert(ignore_permissions=True, ignore_links=True)
        frappe.db.commit()

        return party

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(
            _("Error creating Party Master {0}").format(party_name), str(e)
        )
        raise
