# Party Master Settings DocType: Design & Usage
## 1. Problem Statement
In a complex ERP environment, "Parties" (Customers, Suppliers, Employees, etc.) interact with numerous transactional documents (Sales Invoices, Payment Entries, Journals, etc.). 
Hardcoding the logic to link these documents to a central `Party Master` is brittle and difficult to maintain. 
- **Inconsistency:** Different DocTypes use different field names (e.g., `customer` vs `supplier` vs `party`).
- **Rigidity:** Adding support for a new custom DocType requires code changes.
- **Maintenance:** Updates to logic need to be replicated across multiple controllers.
## 2. The Solution: `Party Master Settings DocType`
The `Party Master Settings DocType` acts as a **dynamic configuration layer** that maps standard and custom ERPNext DocTypes to the `Party Master` system. Instead of hardcoding rules, the system reads this configuration to understand how to extract "Party" information from any document and how to link it to a `Party Master`.
### Key Goals
- **Abstraction:** Decouple the `Party Master` logic from specific DocType implementations.
- **Automation:** Automatically inject necessary fields (`party_master`) into configured DocTypes.
- **Flexibility:** Support both **Static** (e.g., Sales Invoice -> Customer) and **Dynamic** (e.g., Payment Entry -> Party Type + Party) relationships.
## 3. Key Features
### A. Dynamic Field Mapping
It allows defining exactly how to find the party in a target document:
- **Static Party Type:** For documents like `Sales Invoice`, the party type is always `Customer`. The mapping defines `party_fieldname = "customer"`.
- **Dynamic Party Type:** For documents like `Payment Entry`, the party type varies. The mapping defines `party_fieldname = "party"` AND `party_type_fieldname = "party_type"`.
### B. Automated Custom Field Creation
When a DocType is added to the settings, the system (via `party_master_settings.py`) automatically creates:
1.  `party_master` (Link to Party Master): To store the resolved central party.
2.  `is_default_for_party_master` (Check): To mark a specific party record as the default for that master.
### C. Centralized Validation & Fetching
The `party.py` controller uses this configuration to:
-   **Validate:** Ensure the `Party Master` set on a document matches the `Party Master` of the linked Party.
-   **Auto-Fetch:** Automatically set the `Party Master` on a transaction based on the selected Party.
-   **Update:** Propagate changes when a Party's master is changed.
## 4. Technical Implementation
### Data Structure
-   **Parent:** `Party Master Settings` (Singleton)
-   **Child Table:** `Party Master Settings DocType`
    -   `document_type`: The target DocType (e.g., Sales Invoice).
    -   `party_fieldname`: The field holding the party link (e.g., `customer`).
    -   `is_dynamic_party_type`: Boolean flag.
    -   `party_type_fieldname`: Field holding the type (if dynamic).
### Controller Logic (`party.py` & `party_master_settings.py`)
1.  **Caching:** The mappings are cached (`get_doctypes_functional_fields_mapping_as_dict`) to ensure high performance during transaction processing.
2.  **Hooks:** Global hooks (or specific controller calls) use `validate_party_master_on_document_types(doc)` which looks up the `doc.doctype` in the cached settings to apply logic.
## 5. Usage Guide
### Adding a New DocType Support
To make a new DocType "Party Master Aware":
1.  Go to **Party Master Settings**.
2.  In the **Document Types** table, add a row.
3.  Select the **Document Type** (e.g., `Custom Transaction`).
4.  Specify the **Party Fieldname** (e.g., `client`).
5.  If the document supports multiple party types (like Journal Entry), check **Is Dynamic Party Type** and specify the **Party Type Fieldname**.
6.  Save. The system will automatically add the `Party Master` field to your DocType.
