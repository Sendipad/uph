from frappe import _


def get_data():
    """Dashboard configuration for Party Master DocType."""
    return {
        "fieldname": "party_master",
        "transactions": [
            {
                "label": _("Accounting"),
                "items": [
                    "Sales Invoice",
                    "Purchase Invoice",
                    "Payment Entry",
                    "Journal Entry",
                    "Party Analytic Accounting",
                ],
            },
            {
                "label": _("Selling"),
                "items": [
                    "Customer",
                    "Sales Order",
                    "Delivery Note",
                ],
            },
            {
                "label": _("Buying"),
                "items": [
                    "Supplier",
                    "Purchase Order",
                    "Purchase Receipt",
                ],
            },
            {
                "label": _("Human Resources"),
                "items": [
                    "Employee",
                    "Expense Claim",
                ],
            },
            {
                "label": _("Relationships"),
                "items": [
                    {
                        "doctype": "Party Relationship",
                        "fieldname": "subject_party",
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
