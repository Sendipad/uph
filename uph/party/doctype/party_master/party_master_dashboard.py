from frappe import _


def get_data():
    """Dashboard configuration for Party Master DocType."""
    return {
        "fieldname": "party_master",
        "transactions": [
            {
                "label": _("Accounting & Compliance"),
                "items": [
                    "Payment Entry",
                    "Journal Entry",
                    "Party Analytic Accounting",
                    "Party Issue",
                ],
            },
            {
                "label": _("Sales & Buying"),
                "items": [
                    "Customer",
                    "Supplier",
                    "Sales Order",
                    "Delivery Note",
                    "Sales Invoice",
                    "Purchase Order",
                    "Purchase Receipt",
                    "Purchase Invoice",
                ],
            },
            {
                "label": _("People & Relationships"),
                "items": [
                    "Employee",
                    "Expense Claim",
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
