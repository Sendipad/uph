from frappe import _


def get_data():
    """Dashboard configuration for Party Master DocType."""
    return {
        "fieldname": "party_master",
        "transactions": [
            {
                "label": _("Linked Documents"),
                "items": [
                    "Customer",
                    "Supplier",
                    "Employee",
                    "Expense Claim",
                    "Sales Order",
                    "Delivery Note",
                    "Sales Invoice",
                    "Purchase Order",
                    "Purchase Receipt",
                    "Purchase Invoice",
                    "Payment Entry",
                    "Journal Entry",
                    "Party Analytic Accounting",
                    "Party Issue",
                    {
                        "doctype": "Party Relationship",
                        "fieldname": "subject_party",
                    },
                    {
                        "doctype": "Party Relationship",
                        "fieldname": "object_party",
                    },
                ],
            },
        ],
        "reports": [
            {
                "label": _("Reports"),
                "items": [
                    "Party Account Statement",
                    "Party Account Balances",
                    "Chronological Party Ledger",
                    "General Ledger",
                ],
            }
        ],
    }
