from frappe import _
def get_data():
    # doc=frappe.get_doc("Party Master","name")
    # Parties=[x.get("party") for x in doc.linked_party]
    return {
        "fieldname": "party_master",
        "transactions": [
            {
                "label": "Transactional Document",
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
                "label": "Pre-Transactional",
                "label": _("Selling"),
                "items": [
                    "Customer",
                    "Sales Order",
                    "Purchase Order",
                    "Delivery Note",
                    "Purchase Receipt",
                    # "Quotation", # Uncomment if needed
                ],
            },
            {
                "label": "Base",
                "label": _("Buying"),
                "items": [
                    "Party Analytic Accounting",
                    "Customer",
                    "Supplier",
                    "Purchase Order",
                    "Purchase Receipt",
                    # "Request for Quotation", # Uncomment if needed
                ],
            },
            {
                "label": _("Human Resources"),
                "items": [
                    "Employee",
                    "Expense Claim",
                    # "Salary Slip", # Uncomment if needed
                ],
            },
        ],
        "reports": [
            {
                "label": "Reports",
                "label": _("Reports"),
                "items": [
                    "Party Account Statement",
                    _("Party Account Balances"),
                    "Chronological Party Ledger",
                    "General Ledger",
                ],
            }
        ],
    }