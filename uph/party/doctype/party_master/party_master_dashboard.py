from frappe import _
import frappe

def get_data():
    #doc=frappe.get_doc("Party Master","name")
    #Parties=[x.get("party") for x in doc.linked_party]
    return {
        "fieldname": "party_master",
       
        
		"transactions": [
            {
                "label": "Transactional Document",
                "items": ["Sales Invoice", "Purchase Invoice", "Payment Entry","Journal Entry"]
            },{
                "label": "Pre-Transactional",
                "items": ["Sales Order", "Purchase Order", "Delivery Note","Purchase Receipt"]
            },
            {
                "label": "Base",
                "items": ["Party Analytic Accounting", "Customer","Supplier","Employee"]
            }
        ],
          "reports": [
            {
                'label': 'Reports',
                'items': ['Party Account Statement','Party Account Balances','Chronological Party Ledger'],
            }
        ]
           
        }
    
    
