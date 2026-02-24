---
title: "Architecture"
weight: 3
---

# Architecture Summary

## Runtime layers

1. **Hook layer (`uph/hooks`)**
   - Registers app metadata, JS assets, tree view DocType, boot session extension, install hook, and global doc events.
2. **Domain layer (`uph/party/doctype/*`)**
   - `PartyMaster` (`NestedSet`) as identity backbone and hierarchy root/leaf model.
   - Settings DocTypes for mapping transactional doctypes and party rules.
3. **Controller/query layer (`uph/party/controllers/*`)**
   - Validation and synchronization logic for `party_master` across doctypes.
   - Query builders for linked parties, unlinked parties, usage counts, duplicate checks, and warnings.
4. **Reporting layer (`uph/party/report/*`)**
   - Script reports for account statement, account balances, chronological ledger, and master health.
5. **Utility/caching layer (`uph/__init__`, `uph/party/utils`, `uph/party/boot`)**
   - Redis hash caches and boot-time metadata hydration.

## Data model primitives observed

- `Party Master` with tree fields (`lft/rgt`) and hierarchical numbering.
- Child tables and supporting DocTypes:
  - `Party Master Role`
  - `Party Master Parties`
  - `Party Master Accounts`
  - `Party Master Settings`
  - `Party Master Settings DocType`
  - `Party Master Settings DocField`
  - `Party Master Settings Party Type`
  - `Party Analytic Accounting`
  - `Party Analytic Accounting Party`
  - `Party Analytic Accounting Allowed Company`
  - `Data Quality Rule`
  - `Data Quality Rule Condition`

## Lifecycle and enforcement

Global `doc_events` attach validators to all doctypes for:

- `before_validate` and `on_change`: document-type mapping validation + auto-set path.
- `validate`, `on_update`, `on_trash`: target role/party-master consistency checks.

This enables consistent party identity controls without per-doctype custom scripting.
