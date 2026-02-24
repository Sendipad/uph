---
title: "Module Breakdown"
weight: 4
---

# Module Breakdown

## `uph/__init__`

- Defines UPH-level Redis cache key map and helpers:
  - `get_cached`, `update_cached`, `delete_cached`
  - party-type list and party-to-party-master mapping caches.

## `uph/party/boot`

- Extends boot payload (`add_pm_doctypes`) with:
  - configured party-master-enabled doctypes.
  - depends-on fields metadata cache.

## `uph/party/controllers/party`

- Core transactional enforcement:
  - `validate_party_master_on_document_types`
  - `validate_party_master_on_target_party_type`
- Synchronization and updates on existing records:
  - `on_change_party_master_update_transactional_document_types`
  - `update_exists_docs_on_new_document_type_insert`
- Utilities:
  - role validation, duplicate voucher checks, default-party toggling.

## `uph/party/controllers/queries`

- Query APIs and report helpers:
  - link-field query (`party_master_link_query`, `get_party_master`)
  - unlinked/linked party fetch (`get_unlinked_party`, `get_linked_parties_list`)
  - hierarchy flattening (`get_leaf_party_master_list_from_any_node`)
  - mapping dictionaries and cache-backed lookups.

## `uph/party/controllers/mdm`

- Data quality subsystem:
  - text normalization (`normalize_text`)
  - quality validation entrypoint (`validate_document_quality`)
  - duplicate detection (`find_potential_duplicates`)
  - policy execution (`handle_rule_action`)

## `uph/party/doctype/party_master`

- `NestedSet` identity model implementation:
  - autoname/numbering.
  - role validation and primary-role safety.
  - create contact/address helpers.
  - party assignment/reassignment utilities.
  - link to target party document creation (`create_party_from_party_master`, `map_party_to_target`).

## Reports

- `party_account_statement`
- `party_account_balances`
- `chronological_party_ledger`
- `party_master_health_report`

Each exposes `execute(filters)` and supporting chart/column/data builders.
