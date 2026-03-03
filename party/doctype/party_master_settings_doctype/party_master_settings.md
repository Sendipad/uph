# Party Master Settings and DocType Mapping

This document describes all fields in:

1. `Party Master Settings` (parent singleton)
2. `Party Master Settings DocType` (child table that maps transactional DocTypes)

It is intended as a clear, field-by-field reference for implementers.

---

## Party Master Settings (Parent Doctype)

**Purpose:** Global configuration for UPH governance, numbering, validation, and UI behavior.

| Fieldname | Label | Type | Purpose / Behavior | Default / Depends On |
| --- | --- | --- | --- | --- |
| `configuration_tab` | Configuration | Tab Break | UI tab marker. | — |
| `general_configuration_section` | General Configuration | Section Break | UI section marker. | — |
| `override_party_details_api` | Override Party Details API | Check | If enabled, UPH overrides ERPNext party details API to inject Party Master data into transactions. | Default: `1` |
| `enforce_strict_currency` | Enforce Strict Currency Accounting | Check | Enforces strict currency matching between document and account currencies. | Default: `1` |
| `column_break_qzjp` | — | Column Break | UI column marker. | — |
| `setup_section` | Setup Status | Section Break | UI section marker. | — |
| `setup_finished` | Setup Finished | Check | Locks core governance settings once initial setup is complete. Read-only. | Default: `0` |
| `role_mapping_tab` | Role Mapping | Tab Break | UI tab marker. | — |
| `party_type_rules_section` | Party Type Rules | Section Break | UI section marker. | — |
| `party_types` | Party Types | Table | Child table: defines which Party Types are governed and their rules. | Options: `Party Master Settings Party Type` |
| `doctype_fields_mapping_section` | DocType Field Mappings | Section Break | UI section marker. | — |
| `document_types` | Document Types Mapping | Table | Child table: maps transactional DocTypes to Party Master. | Options: `Party Master Settings DocType` |
| `party_master_to_party_sync_fields_section` | Field Synchronization | Section Break | UI section marker. | — |
| `party_master_fields` | Sync Fields | Table | Child table: fields synced from Party Master to ERP Party records. | Options: `Party Master Settings DocField` |
| `governance_tab` | Governance | Tab Break | UI tab marker. | — |
| `governance_rules_section` | Naming & Uniqueness | Section Break | UI section marker. | — |
| `enforce_cross_type_uniqueness` | Enforce Cross-Type Naming Uniqueness | Check | Prevents identical names across different Party Types. | Default: `0` |
| `sync_erp_party_naming` | Sync ERP Party Naming | Check | If enabled, ERP Party names are synced to Party Master numbering. | Default: `0` |
| `role_prefix_mode` | Role Naming Mode | Select | How to apply role prefixes/suffixes when syncing names. | Default: `Prefix for All Role` |
| `column_break_gov2` | — | Column Break | UI column marker. | — |
| `numbering_section` | Numbering Rules | Section Break | UI section marker. | — |
| `numbering_format` | Numbering Format | Select | Party number format. | Default: `Concatenated` |
| `enforce_parent_numbering` | Enforce Parent Numbering Prefix | Check | Enforces child numbers to share parent prefix. | Default: `0` |
| `column_break_gov1` | — | Column Break | UI column marker. | — |
| `digits_count` | Leaf Digits Count | Int | Number of digits for leaf nodes in numbering. | Default: `6` |
| `group_digits` | Group Digits Count | Int | Number of digits for group nodes in numbering. | Default: `4` |
| `transaction_policy_tab` | Transaction Policy | Tab Break | UI tab marker. | — |
| `transaction_policy_section` | Policy Thresholds | Section Break | UI section marker. | — |
| `transaction_policy_draft_days` | Draft Issue Threshold (Days) | Int | Draft voucher age threshold before flagging. | Default: `30` |
| `column_break_policy` | — | Column Break | UI column marker. | — |
| `transaction_policy_cancelled_reference_days` | Cancelled Reference Grace (Days) | Int | Grace period before cancelled reference flags. | Default: `0` |
| `ui_settings_tab` | UI & Analytics | Tab Break | UI tab marker. | — |
| `tree_view_section` | Tree View Configuration | Section Break | UI section marker. | — |
| `auto_expand_levels` | Tree Auto-Expand Levels | Int | Initial tree depth expansion. | Default: `4` |
| `column_break_jote` | — | Column Break | UI column marker. | — |
| `hide_balance` | Hide Balance in Tree | Check | Hides balance totals in tree view. | Default: `1` |
| `paa_tab` | Analytic Accounting | Tab Break | UI tab marker. | — |
| `enable_party_analytic_accounting` | Enable Analytics | Check | Enables Party Analytic Accounting dimension rules. | Default: `0` |
| `duplicate_voucher_tab` | Duplicate Vouchers | Tab Break | UI tab marker. | — |
| `duplicate_check_section` | Duplicate Prevention | Section Break | UI section marker. | — |
| `check_party_master_duplicate_vouchers` | Check Duplicate Vouchers | Check | Enables duplicate voucher checking across Party Master. | Default: `1` |
| `duplicate_voucher_action` | Duplicate Action | Select | Action when duplicates are found. | Default: `Warn` |
| `role_to_bypass_duplicate_voucher` | Bypass Role | Link | Role that can bypass duplicate checks. | Depends on: `check_party_master_duplicate_vouchers` |

---

## Party Master Settings DocType (Child Table)

**Purpose:** Defines how each ERPNext DocType maps to Party Master logic.

| Fieldname | Label | Type | Purpose / Behavior | Default / Depends On |
| --- | --- | --- | --- | --- |
| `document_type` | Document Type | Link | Target DocType to integrate with Party Master. | Required |
| `parent_doctype` | Parent DocType | Link | Parent DocType if the row is for a child table. | Optional |
| `document_categories` | Document Categories | Select | Categorizes the DocType (Selling, Purchasing, Dynamic, Employee). | Options list |
| `enabled` | Enabled | Check | Master toggle for the mapping. | Default: `1` |
| `reqd` | Mandatory | Check | Marks Party field as required. | Default: `1` |
| `column_break_brmi` | — | Column Break | UI column marker. | — |
| `track_transaction_health` | Track Transaction Health | Select | Include or ignore this DocType in transaction health scans. | Default: `Include` |
| `transaction_health_severity` | Severity | Select | Severity for health issues on this DocType. | Default: `High`, depends on `track_transaction_health=Include` |
| `is_dynamic_party_type` | Is Dynamic Party Type | Check | If checked, party type comes from another field. | Default: `0` |
| `party_fieldname` | Party FieldName | Select | Fieldname containing the Party value. | Required |
| `party_type` | Party Type | Link | Fixed Party Type (Customer/Supplier/etc). | Required when `is_dynamic_party_type=0` |
| `party_type_fieldname` | Party Type Fieldname | Select | Fieldname holding Party Type if dynamic. | Required when `is_dynamic_party_type=1` |
| `party_master_custom_field` | Party Master Custom Field | Link | Custom field on Party Master for correlation. | Optional |
| `warn_not_submitted_document` | Warn If Un-Submitted Documents | Check | Warn if draft/unsaved docs exist for the party. | Default: `0` |
| `is_system_generated` | Is System generated | Check | System-managed row, read-only and hidden. | Default: `0` |
| `client_script` | Client Script | Link | Script for custom DocType logic (enabled when mapping is disabled). | Depends on `enabled=0` |

---

## Notes

1. `Party Master Settings DocType` is a child table of `Party Master Settings`.
2. UI-only fields (`Tab Break`, `Section Break`, `Column Break`) exist to structure the form but do not store business logic.
3. If you toggle `enabled` or `reqd` values, clear UPH caches to ensure runtime logic picks up the changes.
