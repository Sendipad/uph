# UPH v3 Party Master Blueprint

## Overview

UPH v3 introduces a fully enterprise-grade Party Master system with configurable numbering, role-based ERPNext synchronization, setup wizard, and multi-language support.

The Party Master remains the canonical identity, structured as a tree for hierarchical organization, while ERPNext Customer, Supplier, Employee, and Bank records are projections (roles) with configurable names.

---

## 1. Core Layer: Party Master Tree

* **Party Master** = canonical identity
* **Tree Structure Example:**

```
1000  All Party Masters
 ├─ 1100 Commercial
 ├─ 1200 Internal
 ├─ 1300 Public/Non-Commercial
 ├─ 1400 Financial
 ├─ 1500 Strategic
 └─ 1900 Uncategorized
```

* **Recommended Numbering Model**

  Use 4-digit base blocks with expansion capacity inside each block.

  | Level | Format |

  | --- | --- |

  | 1xxx | Root scope |

  | 11xx | Domain category |

  | 111x | Sub-category |

  | 1111 | Leaf category |
* **Node Fields:**

  * `party_number` (block-based, configurable)
  * `party_name` (translatable)
  * `parent_party_master`
  * `party_type` / `group_type`
  * Optional `secondary_role(s)`

---

## 2. Numbering & Naming Layer

* **Party Numbering Engine**

  * Formats: `####-######` or `##########`
  * Block-based with gaps for expansion
  * Optional child prefix enforcement
* **ERPNext Role Record Naming**

  * Prefix/suffix mode (`role` + `party_number` + `rulefield`)
  * Examples:

    * Customer: `1112000001-SAR`
    * Supplier: `SUP-1112000001-SAR`
* **Configurable Digits Count** (default = 6)

---

## 3. ERPNext Role Layer

* Roles linked to Party Master:

  * Customer
  * Supplier
  * Employee
  * Bank / Financial
* Optional sync with Party Master:

  * ERPNext DocType record names follow numbering
  * Cross-party-type uniqueness enforcement

---

## 4. Setup & Governance Layer

### Party Master Settings Fields

* `setup_finished` (Check, default = 0)
* `numbering_format` (Select: ####-digits, ##########)
* `digits_count` (Int, default = 6)
* `enforce_parent_numbering` (Check)
* `sync_erp_party_naming` (Check)
* `enforce_cross_type_uniqueness` (Check)
* `role_prefix_mode` (Select: Prefix / Suffix)
* `language` (Select / Multi-language support)

### Setup Wizard Flow

* Administrator must run setup wizard if `setup_finished` = 0
* Wizard allows:

  * Selection of preferred tree structure (language-specific labels)
  * Configuration of numbering format and digits
  * Enabling/disabling governance rules
*   Administrator must run setup wizard if `setup_finished` = 0
*   Wizard allows:

    *   Selection of preferred tree structure (language-specific labels)
    *   Configuration of numbering format and digits
    *   Enabling/disabling governance rules
*   After completion, `setup_finished` = 1

### Validator Hooks

*   Immutable party_number
*   Reserved range enforcement
*   Parent-child prefix
# 12. Technical Implementation Specification (Frappe-Native)

This section defines the technical architecture using standard Frappe patterns, avoiding over-engineering and data duplication.

---

## 12.1 Core Principle: "Single Source of Truth"

We will avoid creating "Shadow Tables" (copies of data) for Unlinked Records or Transaction Health. Instead, we will rely on **Database Indices** and **Redis Caching** to ensure performance without synchronization complexity.

| Feature | Old Approaches (Antipattern) | Frappe-Native Approach |
| :--- | :--- | :--- |
| **Unlinked Records** | Sync to `Unlinked Role Index` table | Query `tabCustomer` directly with Index on `party_master` |
| **Transaction Health** | Sync to `Party Transaction Health` table | Query `docstatus` Index + Redis Cache for Dashboard Stats |
| **Duplicate Checking** | Complex Service Layer | Standard Controller Logic + `Potential Duplicate` DocType |

---

## 12.2 Database Schema Enhancements

To make real-time queries fast (O(1) or O(log n)), we will add the following **Database Indices** via `hooks.py`:

1.  **Party Master Link Fields**:
    *   `tabCustomer` -> `party_master`
    *   `tabSupplier` -> `party_master`
    *   `tabEmployee` -> `party_master`
    *   *Reason*: Allows instant count/fetch of `WHERE party_master IS NULL`.

2.  **Transaction Fields**:
    *   `tabSales Invoice` -> (`party_master`, `docstatus`)
    *   `tabPurchase Invoice` -> (`party_master`, `docstatus`)
    *   *Reason*: Allows "Covering Index" speed for health checks.

3.  **Party Master**:
    *   `normalized_party_name`: Ensure standard index exists.

---

## 12.3 New DocType: `Potential Duplicate`

Unlike unlinked records, Duplicate Detection requires storing *new* information (similarity score, status) that doesn't exist on the party record.

*   **DocType**: `Potential Duplicate`
*   **Fields**:
    *   `party_1` (Link: Party Master)
    *   `party_2` (Link: Party Master)
    *   `score` (Float)
    *   `status` (Selet: Detected, Dismissed, Merged)
    *   `checks_hash` (Data: Hash of names to detect changes)
*   **Logic**:
    *   Generated via background job.
    *   "Dismiss" action simply updates `status` (no separate Exclusion Registry needed, can be combined).

---

## 12.4 Dashboard Architecture (Caching Strategy)

The Dashboard will **never** run `COUNT(*)` on large tables during the HTTP Request.

1.  **Cache Keys**:
    *   `uph:stats:unlinked_count`
    *   `uph:stats:health_issues`
    *   `uph:stats:duplicate_count`

2.  **Update Mechanism**:
    *   **Lazy Loading**: If cache missing, compute and set (5 min TTL).
    *   **Background Refresh**: Hourly job forces refresh of these keys.
    *   **Event-Driven Invalidation**:
        *   On `Customer` save (if `party_master` changed) -> Clear `unlinked_count`.
        *   On `Duplicate` action -> Clear `duplicate_count`.

---

## 12.5 Background Jobs

Standard `scheduler_events` in `hooks.py`:

*   **`daily`**:
    *   `uph.tasks.daily.run_full_duplicate_scan`: Full re-scan of duplicates.
*   **`hourly`**:
    *   `uph.tasks.hourly.refresh_dashboard_stats`: Re-warm the dashboard cache.

---

## 12.6 API Layer (Controllers)

Logic resides in standard modules, not "Service" classes.

*   `uph.party.doctype.party_master.party_master.py`: Core logic.
*   `uph.party.api.dashboard.py`: Dashboard endpoints (reading Cache).
*   `uph.party.api.duplicates.py`: Duplicate detection logic.
*   Cross-role uniqueness enforcement
*   DB-level unique index for collision prevention

---

## 5. Optional Extensions

*   Multi-company: Party Master global, company stored separately
*   Accounting dimension alignment: `Party Analytic Accounting`
*   Reserved blocks for future expansion
*   Multi-role secondary projection
*   Audit-ready: historical numbers never reused

---

## 6. Data Flow

```
User/Admin -> Setup Wizard -> Party Master Tree Creation
     |
     v
Numbering Engine assigns party_number
     |
     v
ERPNext DocType (Customer/Supplier/Employee) auto-created if enabled
     |
     v
Validators enforce: uniqueness, parent prefix, role-based naming
     |
     v
Reporting / Accounting / BI -> aligned with Party Master hierarchy
```

---

## 7. Multi-Language Support

*   `party_name` and tree labels are translatable
*   Setup wizard allows admin to select preferred language for the tree
*   All child nodes inherit translation unless overridden

---

## 8. Enterprise Safeguards

| Feature | Enforcement |
| ------------------------------- | --------------------------- |
| Duplicate numbers | Validator + DB unique index |
| Number reuse | Optional registry table |
| Reserved misuse | Validator checks |
| Changing number after creation | Validator checks |
| Cross-role uniqueness | Validator checks |
| Parent-child prefix enforcement | Optional based on settings |
| ERPNext role naming sync | Optional based on settings |

---

## 9. Notes

*   Party Master remains independent from Chart of Accounts
*   ERPNext role records link to Party Master identity
*   Reserved ranges must never be used manually
*   Once `setup_finished` = 1, core numbering and format settings cannot be changed
*   Prefix/suffix logic allows multiple roles without identity collision

---

## 10. Data Quality Dashboard (Enhanced v3)

The Data Quality Dashboard becomes a modular governance center responsible for identity integrity, linkage completeness, and transactional consistency.

### 10.1 Architecture Overview

The dashboard is divided into three engines:

1.  **Duplicate Detection Engine**
2.  **Unlinked Party Resolver Engine**
3.  **Transactional Integrity Monitor**

Each engine is optimized for performance and designed to operate independently with caching and background processing.

---

### 10.2 Duplicate Detection Engine (Improved)

Enhancements over current version:

*   Blocking strategy (prefix-based + optional phonetic key)
*   Cached similarity index table (materialized results)
*   Background scheduled recalculation
*   Merge workflow with transactional safety
*   Exclusion registry with indexed lookup

#### Performance Optimizations

*   Maintain indexed column: `normalized_party_name`
*   Add DB index on first N characters (computed prefix field)
*   Maintain `duplicate_candidate` table updated async
*   Use sampling only for preview; full scan runs in background job
*   Store similarity score and last-evaluated timestamp

#### New Optional Improvements

*   Add phonetic normalization (Soundex/Metaphone) field
*   Add language-aware normalization rules
*   Add configurable similarity scorer (ratio, token_set_ratio)

---

### 10.3 Unlinked Party Resolver Engine

Purpose: Detect ERPNext role records (Customer, Supplier, Employee, etc.) that are not linked to a Party Master.

#### Detection Logic

*   Scan configured role DocTypes
*   Find records where `party_master` is NULL or empty
*   Batch process to avoid memory spikes

#### Resolver Capabilities

For each unlinked record:

1.  Suggest existing Party Master using similarity search
2.  Show top-N match candidates with score
3.  Allow:

    *   Link to existing Party Master
    *   Create new Party Master from role record
    *   Dismiss suggestion

#### Optimization Strategy

*   Cache normalized names for role records
*   Use prefix blocking before similarity scoring
*   Use background indexing job
*   Paginated server-side queries only

#### Governance Rules

*   Prevent linking if rule_field mismatch (if enforced)
*   Enforce cross-type uniqueness if enabled
*   Log linkage actions in audit trail

---

### 10.4 Transactional Integrity Monitor

Purpose: Detect Party Masters with problematic transactional states.

#### Conditions Checked

*   Draft vouchers linked to party
*   Cancelled vouchers not amended
*   Inconsistent voucher status chains
*   Unsubmitted financial documents

#### View Features

*   Group by Party Master
*   Show count of problematic vouchers
*   Drill-down per DocType
*   Quick actions:

    *   Open voucher
    *   Exclude voucher from check
    *   Mark as reviewed

#### Optimization Strategy

*   Maintain aggregated summary table updated via hooks
*   Use DB-level filtered indexes on:

    *   docstatus
    *   party_master
*   Avoid scanning large transaction tables on each request
*   Use scheduled background refresh

---

### 10.5 Dashboard Statistics Expansion

Replace simple sampling counter with structured metrics:

*   Total Party Masters
*   Total Groups
*   Total Exclusions
*   Incomplete Party Numbers
*   Duplicate Candidates (cached table)
*   Unlinked Role Records
*   Parties With Draft Transactions
*   Parties With Cancelled-Unamended Transactions

All metrics retrieved from cached aggregate table for O(1) reads.

---

### 10.6 Background Jobs & Caching Model

Introduce scheduler events:

* `rebuild_duplicate_index`
* `rebuild_unlinked_index`
* `rebuild_transaction_health_index`

Each job:

* Processes in batches
* Commits incrementally
* Updates summary tables
* Stores last execution timestamp

Dashboard reads only from:

* `duplicate_candidate`
* `unlinked_role_index`
* `party_transaction_health`
* `data_quality_summary`

This ensures constant-time dashboard rendering.

---

### 10.7 Data Quality Governance Policies

| Policy                           | Enforcement                       |
| -------------------------------- | --------------------------------- |
| No duplicate active identity     | Duplicate engine + merge workflow |
| No orphan role record            | Unlinked resolver                 |
| No unresolved draft transactions | Transaction monitor               |
| Audit trail on merge/link        | Version log + custom audit table  |
| Exclusion persistence            | Duplicate Exclusion registry      |

---

### 10.8 UI Design Principles

* Server-side pagination only
* No full-table loads
* Lazy scoring
* Color-coded severity levels
* Bulk actions with confirmation
* Background refresh indicator

---

### 10.9 Enterprise-Grade Safeguards

* All merge operations wrapped in DB transaction
* Rollback on failure
* Immutable historical references
* Exclusion registry protected by permission layer
* Heavy jobs rate-limited
* Indexed frequently queried fields

---

