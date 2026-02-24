---
title: "Architecture, Domain Model, and Workflows"
weight: 2
---

# Architecture overview

UPH is implemented as a Frappe app (`uph`) with these primary layers:

1. **Domain layer** (`party_master`, role child tables, party analytic accounting).
2. **Controller layer** (`party.py`, `queries.py`, `mdm.py`, `field.py`).
3. **Settings and schema orchestration** (`party_master_settings.py`).
4. **Caching and boot helpers** (`uph.__init__`, `party.boot`).
5. **Reporting layer** (party account statement/balances, chronological ledger, health report).

## Domain model (inferred from doctype modules)

### Primary Doctypes

- **Party Master**
  - Tree/nested-set behavior, hierarchical numbering, lifecycle hooks.
  - Child tables include roles and linked parties.

- **Party Master Role**
  - Defines allowed roles (`party_type_role`) for a Party Master.

- **Party Master Parties**
  - Links Party Master to concrete party documents with `party_type`, `party`, `party_name`, `currency`.

- **Party Master Settings**
  - Governs target doctypes, mapping rules, required/allowed policies, and auto-creation of `party_master` fields.

- **Data Quality Rule / Data Quality Rule Condition**
  - Configures duplicate matching criteria (exact/fuzzy/date range), weights, similarity, and filter expressions.

- **Party Analytic Accounting**
  - Assigns analytics to Party Master/parties with allow/restrict company controls and effective date windows.

### Key relationships

- One Party Master can map to many party records across multiple roles.
- A party record maps to one Party Master (enforced/validated by rules).
- Transactional doctypes can carry an auto-managed `party_master` field.

## Business workflows

## 1) Party Master lifecycle

- Create Party Master with hierarchical constraints.
- Validate role consistency.
- Auto-generate numbering and maintain linked-party counters.
- Create primary contact/address helpers.

## 2) Rule-based party linking

- `validate_party_master_on_target_party_type` enforces required/allowed logic.
- `validate_party_master_on_document_types` sets or validates `party_master` on mapped documents.
- Duplicate checks prevent conflicting party-to-master assignments.

## 3) Transactional synchronization

When a party's master changes, UPH can:

- scan configured doctypes,
- count/update historical rows,
- optionally run queued/background update flows,
- leave audit comments on Party Master.

## 4) Duplicate governance workflow

`mdm.validate_document_quality` loads active quality rules and:

- evaluates optional filter conditions,
- detects potential duplicates by weighted criteria,
- triggers configured action (warn/block) with scored records.

## 5) Reporting workflow

Reports aggregate by Party Master and linked parties to produce:

- chronological movement,
- account balances,
- statement with opening/current logic,
- health metrics (linked vs unlinked records).
