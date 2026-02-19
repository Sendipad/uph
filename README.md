<div align="center">
  <a href="https://github.com/Sendipad/uph">
    <img src="https://github.com/user-attachments/assets/424defe6-b5cc-4f77-aa94-7d74c67ff7cc" alt="UPH Logo" height="100px" width="100px"/>
  </a>
  <h2>Unified Party Hub (UPH)</h2>
  <p><b>Enterprise Party Master Data Governance for Frappe / ERPNext</b></p>

  [![Test v15](https://github.com/Sendipad/uph/actions/workflows/test_v15.yml/badge.svg)](https://github.com/Sendipad/uph/actions/workflows/test_v15.yml)
  [![Test Develop (v16)](https://github.com/Sendipad/uph/actions/workflows/test_develop.yml/badge.svg)](https://github.com/Sendipad/uph/actions/workflows/test_develop.yml)
</div>

---

## Overview

UPH centralizes party identity across ERPNext roles (Customer, Supplier, Employee, and related transaction contexts) using **Party Master** as the canonical record. It adds governance workflows, issue tracking, duplicate detection, setup onboarding, and data-quality monitoring.

In v3, UPH moved from isolated “alerts” patterns to a unified issue-driven governance model using **Party Issue** records and scheduled scans.

---

## What’s New in v3

### 1) Setup Wizard Onboarding

A guided `uph-setup-wizard` page now handles first-time configuration:

- setup status detection (`setup_finished` + data presence)
- language-aware template selection from `uph/setup/data/templates`
- numbering configuration (format, leaf/group digits)
- governance toggles (cross-type uniqueness, ERP naming sync)
- safe data-seeding choices when existing Party Master data already exists

If setup is incomplete, admins are automatically redirected from UPH core forms/tree to the wizard.

### 2) Data Quality Dashboard UX Upgrade

`data-quality-dashboard` now exposes multi-tab governance operations:

- **Duplicate Issues**
- **Unlinked Roles**
- **Unlinked Vouchers**
- **Transaction Health**

with stat cards, badges, refresh actions, and background scan triggers.

### 3) Party Issue Governance Layer

New doctype: **Party Issue**

- Supports issue classes: `Duplicate`, `Unlinked`, `Health`, `Transaction Policy`
- Workflow states: `Open`, `Under Review`, `Resolved`, `Ignored`
- Stores metadata and references (`reference_doctype`, `reference_name`, `details_json`)
- Used by dashboard actions (dismiss, merge, resolve) and all scanner pipelines

### 4) Scanner & Monitoring Enhancements

- Duplicate scan with block-based name grouping + fuzzy matching (RapidFuzz)
- Unlinked role and unlinked transaction detection with suggestion-based linking
- Transaction policy scans for:
  - draft aging
  - cancelled but unamended vouchers
  - party-master mismatch between vouchers and linked party records
- Scheduled jobs refresh and re-open caches to keep dashboard responsive

---

## Migration Notes (v3 Merge)

✅ **Yes — v3 includes a migration patch.**

`uph/patches.txt` registers:

- `uph.patches.migrate_duplicate_exclusion_to_party_issue`

This patch migrates legacy **Duplicate Exclusion** records into **Party Issue** entries, maps old statuses to new workflow statuses, preserves historical metadata, and avoids duplicate issue creation.

### Status mapping used by migration

- `Detected` → `Open`
- `Dismissed` → `Ignored`
- `Merged` → `Resolved`

---

## Installation

```bash
bench get-app https://github.com/Sendipad/uph
bench --site {your-site} install-app uph
bench --site {your-site} migrate
```

After install/migrate:

1. Login as Administrator/System Manager.
2. Complete **UPH Setup Wizard**.
3. Open **Data Quality Dashboard** to run first scans.

---

## Core Modules

### Core DocTypes

- `Party Master`
- `Party Master Settings`
- `Party Issue`
- `Party Relationship`
- `Party Analytic Accounting` (+ child doctypes)

### Pages

- `uph-setup-wizard`
- `data-quality-dashboard`

### Controllers / Services

- `duplicate_scanner.py`
- `unlinked_resolver.py`
- `transaction_health.py`
- `party_merge_service.py`

---

## Operational Model

### Scheduled jobs

- **Hourly**
  - dashboard stats refresh
  - unlinked issue scan enqueue
  - transaction policy scan enqueue
- **Daily**
  - duplicate scan enqueue

### Caching

Dashboard stats and health summaries are cache-backed (Redis via `frappe.cache`) to reduce expensive live aggregation during requests.

---

## Testing

Representative tests exist for:

- merge behavior
- dashboard data quality responses
- cache behavior
- query helpers
- normalization
- API endpoints
- party master validations

Run project tests with your bench/site test pipeline as appropriate for your environment.

---

## License

GPL-3.0
