# UPH v3 Architecture Guide

## Overview
Unified Party Hub (UPH) v3 is an enterprise-grade Master Data Management (MDM) extension for ERPNext. It centralizes business roles (Customer, Supplier, Employee) into a single canonical identity—the **Party Master**—organized in a hierarchical tree.

This architecture is designed for **robustness**, **performance** (O(1) dashboard reads), and **scalability**.

---

## 1. Core Data Model

### 1.1 Party Master (`Party Master`)
The central entity representing a unique business identity.
- **Tree Structure**: Uses Nested Set (via `is_group`, `parent_party_master`) for hierarchy.
- **Numbering**: Configurable (e.g., `1000-000001` or `1000000001`).
- **Identity**: Holds the [party_name](file:///home/erpnext/frappe-bench/apps/uph/uph/party/doctype/party_master/party_master.py#237-241), [party_type](file:///home/erpnext/frappe-bench/apps/uph/uph/party/doctype/party_master_settings/party_master_settings.py#598-609) (primary role), and links to secondary roles.

### 1.2 Party Master Role (`Party Master Role`)
A child table on `Party Master` that allows a single entity to hold multiple ERPNext roles (e.g., a Company can be both a Customer and a Supplier).
- **Fields**: `party_type_role` (Link to DocType), [party](file:///home/erpnext/frappe-bench/apps/uph/uph/party/controllers/queries.py#125-220) (Dynamic Link).

### 1.3 Party Master Settings (`Party Master Settings`)
Singleton configuration for:
- **Numbering**: Format, digits count.
- **Governance**: Uniqueness enforcement, parent prefix validation.
- **Naming Sync**: Syncing ERPNext record names with Party Master numbers.
- **Setup**: Tracks `setup_finished` state.

---

## 2. Key Engines & Logic

### 2.1 Synchronization Engine
**Path**: `uph.party.controllers.party`
**Path**: `uph.party.controllers.queries`

- **Name Sync**: [sync_party_name_from_party_master](file:///home/erpnext/frappe-bench/apps/uph/uph/party/controllers/party.py#806-862) keeps ERPNext party names aligned with `Party Master` numbering (Prefix/Suffix modes).
- **Link Query**: [party_master_link_query](file:///home/erpnext/frappe-bench/apps/uph/uph/party/controllers/queries.py#18-122) provides optimized search filtering by role and group status.
- **Smart Cache**: `uph.party.controllers.cache_utils.SmartCache` manages high-performance caching for heavy queries.

### 2.2 Data Quality & Deduplication
**Path**: `uph.party.controllers.normalization`
**Path**: `uph.party.page.data_quality_dashboard`

- **Duplicate Detection**:
    - **Blocking**: Groups parties by name prefix/blocking key to minimize comparisons.
    - **Scoring**: Uses `rapidfuzz` (if available) for fuzzy string matching.
    - **Storage**: Detected pairs stored in `Potential Duplicate` DocType.
    - **Exclusion**: False positives managed via `Duplicate Exclusion` DocType.
- **Dashboard**:
    - **Stats**: Fetched from Redis Cache (updated via background jobs).
    - **Metrics**: Total Parties, Groups, Unlinked, Incomplete, Duplicates, Transaction Health.
    - **Incomplete Parties**: Tracks Party Masters with no assigned [party_type](file:///home/erpnext/frappe-bench/apps/uph/uph/party/doctype/party_master_settings/party_master_settings.py#598-609).

### 2.3 Setup & Onboarding
**Path**: `uph.party.page.uph_setup_wizard`
**Path**: `uph.setup.install`

- **Setup Wizard**: SPA (Single Page Application) for initial configuration.
    - **Templates**: JSON-based industry templates for tree structure.
    - **Seeder**: [PartyMasterSeeder](file:///home/erpnext/frappe-bench/apps/uph/uph/setup/install.py#11-171) builds the tree from templates efficiently.
- **Installation**:
    - **Root Seeding**: Creates only the root node (`1000 All Party Masters`) during app install.
    - **Deferral**: Full tree construction is deferred to the Setup Wizard or Test Runner.

### 2.4 Transactional Integrity
**Path**: `uph.tasks.refresh_dashboard_stats`

- **Health Checks**: Monitors for:
    - Draft Vouchers linked to Party Masters.
    - Cancelled Vouchers that haven't been amended.
- **Indexes**: Custom database indices on [(party_master, docstatus)](file:///home/erpnext/frappe-bench/apps/uph/uph/setup/install.py#17-27) for `Sales Invoice`, `Purchase Invoice`, etc., ensure O(1) health checks.

---

## 3. Data Flow

1.  **Creation**: User creates a `Party Master` (or it's auto-created from a specific Party Type if configured).
2.  **Numbering**: System assigns a unique ID based on the parent block and configured format.
3.  **Synchronization**: If Sync Enabled, the linked ERPNext record (e.g., Customer) is renamed to match the Party Master ID (e.g., `CUST-1000001`).
4.  **Validation**:
    - **Uniqueness**: Prevents linking the same Customer to multiple Party Masters.
    - **Parent Prefix**: Ensures child nodes follow the parent's numbering block (e.g., `1100` -> `1100-00001`).

---

## 4. Background Jobs

- **Hourly**: `uph.tasks.refresh_dashboard_stats`
    - Recalculates dashboard metrics (Unlinked, Health, Incomplete) and updates Redis cache keys (`uph:stats:*`).
- **Daily**: `uph.tasks.run_full_duplicate_scan`
    - Runs the heavy fuzzy matching process to populate `Potential Duplicate`.

---

## 5. Testing Strategy

- **Test Seeding**: `uph.tests.test_utils.before_tests` explicitly seeds a full Party Master structure (`party_master_structure.json`) because the standard install only creates the root.
- **Isolation**: Tests use `SmartCache.clear()` to ensure query tests don't hit stale data.

---

## 6. Future Extension Guidelines

- **New Party Roles**: Add to `Party Type` list and ensuring [get_party_master_parties_db](file:///home/erpnext/frappe-bench/apps/uph/uph/party/controllers/queries.py#454-570) handles the new DocType.
- **New Metrics**: Add calculation in `uph.tasks.refresh_dashboard_stats` and expose in [data_quality_dashboard.py](file:///home/erpnext/frappe-bench/apps/uph/uph/tests/test_data_quality_dashboard.py).
- **Performance**: Always use `SmartCache` for frequent read-heavy operations.
