---
title: "Core DocTypes"
weight: 5
---

# Core DocTypes Reference

This section provides detailed documentation for all DocTypes introduced by Unified Party Hub (UPH).

---

## Party Master

**Table:** `tabParty Master`

The central hub DocType for all party entities. It serves as the single source of truth for legal entities.

### Key Features

- **Tree-based Hierarchy**: Supports parent-child relationships for organizational structures
- **Hierarchical Numbering**: Automatic numbering based on parent node (e.g., `PM-001`, `PM-001-001`)
- **Multi-Role Support**: Link Customers, Suppliers, Employees under one entity
- **Primary/Secondary Roles**: Define primary role and link secondary roles

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `party_name` | Data | Name of the party (searchable) |
| `party_number` | Data | Hierarchical party number (unique) |
| `parent_party_master` | Link | Parent Party Master (for hierarchy) |
| `is_group` | Check | Whether this is a group node |
| `party_type` | Link | Party Type (Customer, Supplier, Employee) |
| `group_type` | Link | Customer/Supplier Group |
| `party_type_group` | Dynamic Link | Dynamic link to group type |
| `territory` | Link | Territory assignment |
| `default_currency` | Link | Default currency for transactions |
| `tax_id` | Data | Tax identification number |
| `national_id` | Data | National ID number |
| `passport_number` | Data | Passport number |
| `business_registration_number` | Data | Business registration number |
| `legal_entity_type` | Link | Type of legal entity |
| `date_of_establishment` | Date | Date of establishment |
| `total_linked_party` | Int | Count of linked parties (read-only) |
| `has_secondary_role_party` | Check | Indicates if secondary roles exist |
| `primary_party_master` | Link | Primary Party Master for secondary roles |
| `is_internal_party` | Check | Mark as internal party |
| `represents_company` | Link | Company for inter-company transactions |
| `is_primary_role` | Check | Whether this is the primary role |
| `is_frozen` | Check | Freeze the party master |
| `disabled` | Check | Disable the party master |
| `status` | Select | Status (Active, Inactive) |
| `enforce_party_analaytic_accounting_selection` | Check | Enforce PAA selection |

### Child Tables

- `Party Master Parties`: Links to Customers, Suppliers, Employees
- `Party Master Accounts`: Account mappings per currency
- `Party Master Role`: Role definitions

---

## Party Analytic Accounting

**Table:** `tabParty Analytic Accounting`

Enables Oracle TCA-like site accounting for party-level financial segmentation.

### Key Features

- **Accounting Non-Duplication**: Eliminates redundant accounts for branches
- **Multiple Dimension Types**: Site, Business Unit, Branch, Territory, Cost Center, Factory/Plant
- **Company-Specific Rules**: Configure rules per company
- **Effective Dating**: Track validity periods

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `party_master` | Link | Associated Party Master |
| `analytic_name` | Data | Display name for the dimension |
| `type` | Select | Dimension type (Site, Business Unit, etc.) |
| `enabled` | Check | Enable this dimension |
| `is_default` | Check | Default dimension for the party |
| `status` | Select | Status (Active, Inactive, Archived) |
| `allow_or_restrict` | Select | Allow or restrict rule |
| `effective_from` | Date | Effective start date |
| `effective_to` | Date | Effective end date |

### Child Tables

- `Party Analytic Accounting Party`: Applicable parties
- `Party Analytic Accounting Allowed Company`: Applicable companies

### Dimension Types

1. **Site**: Physical locations (warehouses, offices)
2. **Business Unit**: Strategic business divisions
3. **Branch**: Operational branches
4. **Territory**: Geographic territories
5. **Cost Center**: Cost allocation centers
6. **Factory / Plant**: Manufacturing facilities

---

## Party Master Parties

**Table:** `tabParty Master Parties` (Child Table)

Junction table linking Party Master to ERPNext party records.

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `party_type` | Select | Type (Customer, Supplier, Employee, Shareholder) |
| `party` | Dynamic Link | Dynamic link to the party record |
| `party_name` | Data | Reference party name |
| `currency` | Link | Currency for this link |

### Usage

This child table allows a single Party Master to be linked to multiple party records of different types. For example:
- Party Master "ABC Corp" can link to Customer "ABC Corp" and Supplier "ABC Corp (International)"
- Each link can have a different currency for multi-currency support

---

## Party Master Settings

**Table:** `tabParty Master Settings` (Single DocType)

Central configuration DocType for UPH.

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `override_party_details_api` | Check | Override ERPNext party details API |
| `enforce_strict_currency` | Check | Enforce strict currency mapping |
| `enable_party_analytic_accounting` | Check | Enable PAA functionality |
| `auto_expand_levels` | Int | Tree view auto-expand levels |
| `hide_balance` | Check | Hide balance in tree view |
| `check_party_master_duplicate_vouchers` | Check | Check for duplicate vouchers |
| `duplicate_voucher_action` | Select | Action for duplicate (Warn/Stop) |
| `role_to_bypass_duplicate_voucher` | Link | Role to bypass duplicate check |

### Child Tables

- `Party Master Settings Party Type`: Party type rules
- `Party Master Settings DocType`: Document type configuration
- `Party Master Settings DocField`: Field mapping configuration

---

## Party Relationship

**Table:** `tabParty Relationship`

Define N-to-N relationships between parties.

### Key Features

- **Relationship Types**: Parent/Subsidiary, Ownership, Management
- **Ownership Percentages**: Track ownership stakes
- **Validity Periods**: Define relationship effective dates

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `from_party` | Link | First party in relationship |
| `to_party` | Link | Second party in relationship |
| `relationship_type` | Link | Type of relationship |
| `ownership_percentage` | Percent | Ownership percentage |
| `effective_from` | Date | Start of validity |
| `effective_to` | Date | End of validity |
| `description` | Text | Relationship description |

### Relationship Types

1. **Parent/Subsidiary**: Corporate hierarchy
2. **Ownership**: Shareholder relationships
3. **Management**: Management/leadership relationships
4. **Partnership**: Business partnerships
5. **Alliance**: Strategic alliances

---

## Duplicate Exclusion

**Table:** `tabDuplicate Exclusion`

Rules for excluding certain records from duplicate detection.

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `party` | Dynamic Link | Party to exclude |
| `reason` | Text | Reason for exclusion |
| `valid_from` | Date | Exclusion start date |
| `valid_to` | Date | Exclusion end date |

---

## Supporting DocTypes

### Party Master Accounts

**Table:** `tabParty Master Accounts`

Account mappings per currency for Party Master.

| Field | Type | Description |
|-------|------|-------------|
| `company` | Link | Company |
| `currency` | Link | Currency |
| `receivable_account` | Link | Receivable account |
| `payable_account` | Link | Payable account |

### Party Master Role

**Table:** `tabParty Master Role` (Child Table)

Role definitions for Party Master.

| Field | Type | Description |
|-------|------|-------------|
| `party_type_role` | Link | Party Type role |

### Party Master Settings Party Type

**Table:** `tabParty Master Settings Party Type`

Party type rules configuration.

| Field | Type | Description |
|-------|------|-------------|
| `party_type` | Select | Party type |
| `required` | Check | Party Master required |
| `allowed` | Check | Party type allowed |
| `rule_fieldname` | Data | Field for uniqueness rule |

### Party Master Settings DocType

**Table:** `tabParty Master Settings DocType`

Document type configuration for Party Master injection.

| Field | Type | Description |
|-------|------|-------------|
| `parent_doctype` | Link | Parent document type |
| `document_type` | Link | Child document type |
| `party_fieldname` | Data | Party field name |
| `party_type_fieldname` | Data | Party type field name |
| `required` | Check | Party Master required |

---

## API Integration Points

UPH injects Party Master into the following transaction types:

- Sales Invoice / Sales Invoice Item
- Purchase Invoice / Purchase Invoice Item
- Journal Entry / Journal Entry Account
- Payment Entry
- Sales Order / Sales Order Item
- Purchase Order / Purchase Order Item
- Delivery Note / Delivery Note Item
- Purchase Receipt / Purchase Receipt Item
- Expense Claim

---

## Related Documentation

- [Data Quality Dashboard](../features/data-quality-dashboard.md)
- [Configuration](../features/configuration.md)
- [Hierarchical Numbering](../features/hierarchical-numbering.md)
- [Relationship Management](../features/relationship-management.md)
