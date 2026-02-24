---
title: "Operations"
weight: 6
---

# Operations, Permissions, and Jobs

## Permissions and role controls observed

- `Party Master Settings.validate_document_types` enforces System Manager-level control for settings mutations.
- Party/role consistency checks enforce that selected `party_master` contains allowed role and valid state (exists, not group, enabled path).
- Default-party toggling logic ensures one default mapping per party type scope.

## Background/update behaviors

No dedicated async worker module was discovered in this snapshot, but background-like batch update behavior exists in synchronous update routines:

- Existing voucher/document updates when new mapping entries are configured.
- Cross-doctype propagation when a party is moved between party masters.
- Cache invalidation/reset helpers tied to configuration updates.

## Installation / setup behaviors

- App requires ERPNext (`required_apps`).
- Setup utilities in `Party Master Settings` bootstrap base document-type mappings and party-type rows.
- Boot extension adds dynamic metadata for frontend form behavior.

## Known repository limitation

Current branch includes compiled Python bytecode (`*.pyc`) without corresponding `.py` source files under `uph/`. Documentation is intentionally constrained to verified symbols/constants from this implementation form.
