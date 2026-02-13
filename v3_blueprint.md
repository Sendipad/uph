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
* After completion, `setup_finished` = 1

### Validator Hooks

* Immutable party_number
* Reserved range enforcement
* Parent-child prefix enforcement (optional)
* Cross-role uniqueness enforcement
* DB-level unique index for collision prevention

---

## 5. Optional Extensions

* Multi-company: Party Master global, company stored separately
* Accounting dimension alignment: `Party Analytic Accounting`
* Reserved blocks for future expansion
* Multi-role secondary projection
* Audit-ready: historical numbers never reused

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

* `party_name` and tree labels are translatable
* Setup wizard allows admin to select preferred language for the tree
* All child nodes inherit translation unless overridden

---

## 8. Enterprise Safeguards

| Feature                         | Enforcement                 |
| ------------------------------- | --------------------------- |
| Duplicate numbers               | Validator + DB unique index |
| Number reuse                    | Optional registry table     |
| Reserved misuse                 | Validator checks            |
| Changing number after creation  | Validator checks            |
| Cross-role uniqueness           | Validator checks            |
| Parent-child prefix enforcement | Optional based on settings  |
| ERPNext role naming sync        | Optional based on settings  |

---

## 9. Notes

* Party Master remains independent from Chart of Accounts
* ERPNext role records link to Party Master identity
* Reserved ranges must never be used manually
* Once `setup_finished` = 1, core numbering and format settings cannot be changed
* Prefix/suffix logic allows multiple roles without identity collision

---

## 10. Data Quality Dashboard (Enhanced v3)

The Data Quality Dashboard becomes a modular governance center responsible for identity integrity, linkage completeness, and transactional consistency.

### 10.1 Architecture Overview

The dashboard is divided into three engines:

1. **Duplicate Detection Engine**
2. **Unlinked Party Resolver Engine**
3. **Transactional Integrity Monitor**

Each engine is optimized for performance and designed to operate independently with caching and background processing.

---

### 10.2 Duplicate Detection Engine (Improved)

Enhancements over current version:

* Blocking strategy (prefix-based + optional phonetic key)
* Cached similarity index table (materialized results)
* Background scheduled recalculation
* Merge workflow with transactional safety
* Exclusion registry with indexed lookup

#### Performance Optimizations

* Maintain indexed column: `normalized_party_name`
* Add DB index on first N characters (computed prefix field)
* Maintain `duplicate_candidate` table updated async
* Use sampling only for preview; full scan runs in background job
* Store similarity score and last-evaluated timestamp

#### New Optional Improvements

* Add phonetic normalization (Soundex/Metaphone) field
* Add language-aware normalization rules
* Add configurable similarity scorer (ratio, token_set_ratio)

---

### 10.3 Unlinked Party Resolver Engine

Purpose: Detect ERPNext role records (Customer, Supplier, Employee, etc.) that are not linked to a Party Master.

#### Detection Logic

* Scan configured role DocTypes
* Find records where `party_master` is NULL or empty
* Batch process to avoid memory spikes

#### Resolver Capabilities

For each unlinked record:

1. Suggest existing Party Master using similarity search
2. Show top-N match candidates with score
3. Allow:

   * Link to existing Party Master
   * Create new Party Master from role record
   * Dismiss suggestion

#### Optimization Strategy

* Cache normalized names for role records
* Use prefix blocking before similarity scoring
* Use background indexing job
* Paginated server-side queries only

#### Governance Rules

* Prevent linking if rule_field mismatch (if enforced)
* Enforce cross-type uniqueness if enabled
* Log linkage actions in audit trail

---

### 10.4 Transactional Integrity Monitor

Purpose: Detect Party Masters with problematic transactional states.

#### Conditions Checked

* Draft vouchers linked to party
* Cancelled vouchers not amended
* Inconsistent voucher status chains
* Unsubmitted financial documents

#### View Features

* Group by Party Master
* Show count of problematic vouchers
* Drill-down per DocType
* Quick actions:

  * Open voucher
  * Exclude voucher from check
  * Mark as reviewed

#### Optimization Strategy

* Maintain aggregated summary table updated via hooks
* Use DB-level filtered indexes on:

  * docstatus
  * party_master
* Avoid scanning large transaction tables on each request
* Use scheduled background refresh

---

### 10.5 Dashboard Statistics Expansion

Replace simple sampling counter with structured metrics:

* Total Party Masters
* Total Groups
* Total Exclusions
* Incomplete Party Numbers
* Duplicate Candidates (cached table)
* Unlinked Role Records
* Parties With Draft Transactions
* Parties With Cancelled-Unamended Transactions

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


# 12. Technical Implementation Specification (Production-Grade)

This section defines concrete database schema, services, hooks, background jobs, APIs, and permission layers required to implement the enhanced Data Quality Dashboard.

---

## 12.1 New DocTypes (Tables)

### 1️⃣ Duplicate Candidate (Indexed Materialized Table)

Purpose: Store precomputed similarity results.

⚠ Note: This does NOT replace the existing **Duplicate Exclusion** DocType.

* **Duplicate Exclusion** = manual governance registry (already implemented).
* **Duplicate Candidate** = system-generated similarity index (new, materialized table).

They serve different purposes and must coexist.

Fields:

* `party_1` (Link → Party Master, indexed)
* `party_2` (Link → Party Master, indexed)
* `similarity_score` (Float, indexed)
* `status` (Select: Open, Merged, Excluded)
* `last_evaluated_on` (Datetime, indexed)
* `blocking_key` (Data, indexed)  # prefix or phonetic key

Indexes:

* Unique composite index on (`party_1`, `party_2`)
* Index on (`similarity_score`)
* Index on (`blocking_key`)

Workflow Integration with Existing Duplicate Exclusion:

* When user dismisses a duplicate:

  * Insert record in **Duplicate Exclusion** (existing DocType)
  * Update corresponding Duplicate Candidate.status = "Excluded"

* During duplicate rebuild:

  * Load Duplicate Exclusion pairs into memory
  * Skip generating candidates for excluded pairs

This preserves backward compatibility with your current implementation.

---

### Enhancement to Existing Duplicate Exclusion DocType

Your current schema is structurally correct and production-safe.

Recommended improvements (non-breaking):

1. Add DB-level unique constraint on sorted pair:

   * Prevent duplicate exclusion records for same pair

2. Add composite index:

   * (`party_1`, `party_2`)

3. Optional computed helper field:

   * `pair_key` (Data, indexed)
   * Value = sorted(party_1, party_2)
   * Ensures O(1) lookup without Python sorting

4. Add optional field:

   * `is_system_generated` (Check)
   * Future-proof if system auto-excludes low-confidence pairs

These changes optimize performance without altering your current dismissal API.

---

### 2️⃣ Unlinked Role Index

Purpose: Store ERP role records without Party Master link.

Fields:

* `role_doctype` (Data, indexed)
* `role_name` (Data, indexed)
* `party_master` (Link → Party Master, nullable)
* `normalized_name` (Data, indexed)
* `suggested_party_master` (Link → Party Master)
* `suggestion_score` (Float)
* `status` (Select: Open, Linked, Dismissed)
* `last_checked_on` (Datetime)

Indexes:

* Composite index (`role_doctype`, `status`)
* Index (`normalized_name`)

---

### 3️⃣ Party Transaction Health

Purpose: Aggregated transactional integrity state per party.

Fields:

* `party_master` (Link → Party Master, unique)
* `draft_count` (Int)
* `cancelled_unamended_count` (Int)
* `inconsistent_chain_count` (Int)
* `severity_level` (Select: Low, Medium, High)
* `last_updated_on` (Datetime)

Index:

* Unique index on `party_master`

---

### 4️⃣ Data Quality Summary (Singleton)

Purpose: O(1) dashboard metrics retrieval.

Fields:

* `total_parties`
* `total_groups`
* `duplicate_open_count`
* `unlinked_role_count`
* `parties_with_drafts`
* `parties_with_cancelled_unamended`
* `last_refreshed_on`

---

## 12.2 Service Layer Architecture

Create service modules under:

```
uph/party/services/
    duplicate_service.py
    unlinked_service.py
    transaction_health_service.py
    dashboard_service.py
```

### DuplicateService Responsibilities

* Build blocking keys (prefix + optional phonetic)
* Batch similarity scoring
* Update Duplicate Candidate table
* Handle merge workflow (delegating to PartyMergeService)
* Maintain exclusion logic

Public Methods:

* `rebuild_index(batch_size=500)`
* `get_candidates(limit, offset, filters)`
* `mark_excluded(p1, p2)`
* `merge(p1, p2)`

---

### UnlinkedService Responsibilities

* Scan configured role DocTypes
* Normalize role names
* Suggest Party Master using similarity engine
* Persist suggestions
* Handle linking operations

Public Methods:

* `rebuild_unlinked_index()`
* `suggest_matches(role_doctype, role_name)`
* `link(role_doctype, role_name, party_master)`

---

### TransactionHealthService Responsibilities

* Aggregate voucher state per party
* Update Party Transaction Health table
* Provide drill-down queries

Public Methods:

* `rebuild_health_index()`
* `get_party_health(party_master)`
* `exclude_voucher(doctype, name)`

---

### DashboardService Responsibilities

* Read-only access to summary tables
* No heavy computations

Public Methods:

* `get_summary()`
* `get_severity_distribution()`

---

## 12.3 Background Jobs (Scheduler Events)

In `hooks.py`:

```
scheduler_events = {
    "hourly": [
        "uph.party.services.duplicate_service.rebuild_index",
        "uph.party.services.unlinked_service.rebuild_unlinked_index",
    ],
    "daily": [
        "uph.party.services.transaction_health_service.rebuild_health_index",
        "uph.party.services.dashboard_service.refresh_summary",
    ]
}
```

Rules:

* Batch commits every N records
* Use savepoints for rollback safety
* Log execution time
* Skip execution if previous job still running (locking flag)

---

## 12.4 Hook Integration

### On Party Master Insert/Update

* Update normalized name
* Re-evaluate blocking key
* Schedule lightweight duplicate check for affected block

### On Role DocType Insert

* If `party_master` empty → enqueue unlinked index update

### On Voucher Submit/Cancel

* Incrementally update Party Transaction Health record

---

## 12.5 API Layer (Whitelisted Endpoints)

Replace heavy runtime computations with indexed reads.

### Examples

* `get_duplicate_candidates(limit, offset, filters)`
* `get_unlinked_roles(limit, offset)`
* `get_party_transaction_health(party_master)`
* `resolve_unlinked(role_doctype, role_name, action)`
* `resolve_transaction_issue(party_master, voucher)`

All APIs must:

* Enforce permission checks
* Use server-side pagination
* Avoid full-table scans

---

## 12.6 Performance & Index Strategy

Mandatory DB indexes:

Party Master:

* `normalized_party_name`
* `party_number`

Transaction tables:

* `party_master`
* `docstatus`
* Composite (`party_master`, `docstatus`)

Duplicate Candidate:

* (`party_1`, `party_2`)
* `similarity_score`

Unlinked Role Index:

* (`role_doctype`, `status`)

---

## 12.7 Concurrency & Safety

* Use explicit DB transactions during merges
* Use row-level locking for merge pairs
* Prevent concurrent merge of same party
* Use advisory lock pattern during background jobs

---

## 12.8 Permission Model

Duplicate View:

* Read: Party Master permission
* Merge: Data Quality Manager role

Unlinked Resolver:

* Link/Create: Party Manager role

Transaction Monitor:

* View: Accounting Manager
* Exclude Voucher: Restricted role

---

## 12.9 Logging & Audit

Create `Data Quality Audit Log` DocType:

Fields:

* `action_type` (Merge, Link, Exclude, Resolve)
* `reference_1`
* `reference_2`
* `performed_by`
* `performed_on`
* `details`

All state-changing operations must log entry.

---

## 12.10 Deployment Strategy

1. Add new DocTypes and indexes
2. Backfill normalized names
3. Run initial index build in background
4. Enable dashboard to read from cached tables
5. Deprecate runtime duplicate scanning endpoint

---

This specification ensures:

* Constant-time dashboard rendering
* No large runtime scans
* Scalable similarity indexing
* Clear separation of computation and presentation
* Enterprise-grade safety and auditability
