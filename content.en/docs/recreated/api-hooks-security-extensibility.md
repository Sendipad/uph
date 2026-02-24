---
title: "APIs, Hooks, Security, Extensibility, and Limitations"
weight: 4
---

# API and callable surface (source-inferred)

## Boot/session helpers

- `uph.party.boot.add_pm_doctypes`
- `uph.party.boot.get_pm_doctypes`
- `uph.party.boot.get_party_master_depends_on_fields`

## Party and query controllers

- `uph.party.controllers.queries.party_master_link_query`
- `uph.party.controllers.queries.get_party_master`
- `uph.party.doctype.party_master.party_master.create_party_master`
- `uph.party.doctype.party_master.party_master.create_party_from_party_master`
- `uph.party.doctype.party_master.party_master.map_party_to_target`
- `uph.party.doctype.party_master.party_master.assign_party_master_for_selection`

## Data quality / MDM controllers

- `uph.party.controllers.mdm.normalize_text`
- `uph.party.controllers.mdm.validate_document_quality`

## Regional helper

- `uph.regional.arabic.money_in_words`

# Hooks and events

Hooks indicate:

- app include JS bundle (`uph.bundle.js` + rule builder js)
- treeview support for `Party Master`
- boot hook for injecting Party Master metadata
- document event handlers on validate/update/change/trash/before_validate for mapped doctypes

These events enforce role compatibility, required party master rules, and transactional consistency.

# Background jobs and heavy operations

From controller behavior and constants, UPH supports large-scale update patterns:

- recount linked-party totals,
- update existing mapped transaction rows,
- optional queued updates for changed party assignments,
- cache invalidation after mapping/settings changes.

# Caching model

UPH uses Redis/local cache helpers for:

- party type list,
- party-master-to-party mappings,
- role lists,
- doctype field maps,
- usage-based link-search acceleration.

# Permissions and security model

## What is visible in code

- Validation routines frequently bypass during patch/install/import contexts.
- Settings operations include privileged checks (e.g., System Manager guardrails).
- Duplicate actions are designed to warn/throw based on configured policy.

## Operational guidance

- Restrict Settings and merge-sensitive actions to governance/admin roles.
- Treat whitelisted methods as authenticated business APIs.
- Audit bulk reassignments and duplicate resolution actions.

# Integration points

- ERPNext party doctypes (Customer, Supplier, Employee, Shareholder support inferred in mappings)
- Sales/Purchase and accounting transactional doctypes
- Frappe reports and dashboard components
- Multi-currency account behavior and Arabic number-to-words localization

# Extensibility and customization

- Add new party doctypes via Party Master Settings mappings.
- Extend duplicate detection by adding conditions/weights/check types.
- Extend transaction propagation by defining additional mapped doctypes.
- Build custom reports by reusing party-master and linked-party query helpers.

# Known limitations and assumptions

1. The repository currently ships Python bytecode (`.pyc`) rather than editable `.py` source for app logic; this documentation is reconstructed from static bytecode inspection.
2. Bytecode analysis reveals callable names, constants, and structure, but not all comments/type hints.
3. External behavior still depends on runtime metadata, custom fields, and live ERPNext data.
4. AI-assistant URL prefill support may vary by provider and browser.

# Developer notes

- The docs site is Hugo-based (Book theme overrides in `layouts/`).
- UPH-specific docs UI customizations are in custom layouts/partials and custom CSS.
- For app code maintenance, restore tracked `.py` sources alongside `.pyc` artifacts to improve traceability and reviewability.
