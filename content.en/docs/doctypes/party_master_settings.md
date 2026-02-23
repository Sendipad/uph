---
title: "Party Master Settings"
weight: 10
description: "No description provided."
---

# Party Master Settings

**Module:** Party

## Overview
No description provided.

## Fields
| Label | Fieldname | Type | Mandatory |
|-------|-----------|------|-----------|
| Configuration | configuration_tab | Tab Break | No |
| General Configuration | general_configuration_section | Section Break | No |
| Override Party Details API | override_party_details_api | Check | No |
| Enforce Strict Currency Accounting | enforce_strict_currency | Check | No |
|  | column_break_qzjp | Column Break | No |
| Setup Status | setup_section | Section Break | No |
| Setup Finished | setup_finished | Check | No |
| Role Mapping | role_mapping_tab | Tab Break | No |
| Party Type Rules | party_type_rules_section | Section Break | No |
| Party Types | party_types | Table | No |
| DocType Field Mappings | doctype_fields_mapping_section | Section Break | No |
| Document Types Mapping | document_types | Table | No |
| Field Synchronization | party_master_to_party_sync_fields_section | Section Break | No |
| Sync Fields | party_master_fields | Table | No |
| Governance | governance_tab | Tab Break | No |
| Naming & Uniqueness | governance_rules_section | Section Break | No |
| Enforce Cross-Type Naming Uniqueness | enforce_cross_type_uniqueness | Check | No |
| Sync ERP Party Naming | sync_erp_party_naming | Check | No |
| Role Naming Mode | role_prefix_mode | Select | No |
|  | column_break_gov2 | Column Break | No |
| Numbering Rules | numbering_section | Section Break | No |
| Numbering Format | numbering_format | Select | No |
| Enforce Parent Numbering Prefix | enforce_parent_numbering | Check | No |
|  | column_break_gov1 | Column Break | No |
| Leaf Digits Count | digits_count | Int | No |
| Group Digits Count | group_digits | Int | No |
| Transaction Policy | transaction_policy_tab | Tab Break | No |
| Policy Thresholds | transaction_policy_section | Section Break | No |
| Draft Issue Threshold (Days) | transaction_policy_draft_days | Int | No |
|  | column_break_policy | Column Break | No |
| Cancelled Reference Grace (Days) | transaction_policy_cancelled_reference_days | Int | No |
| UI & Analytics | ui_settings_tab | Tab Break | No |
| Tree View Configuration | tree_view_section | Section Break | No |
| Tree Auto-Expand Levels | auto_expand_levels | Int | No |
|  | column_break_jote | Column Break | No |
| Hide Balance in Tree | hide_balance | Check | No |
| Analytic Accounting | paa_tab | Tab Break | No |
| Enable Analytics | enable_party_analytic_accounting | Check | No |
| Duplicate Vouchers | duplicate_voucher_tab | Tab Break | No |
| Duplicate Prevention | duplicate_check_section | Section Break | No |
| Check Duplicate Vouchers | check_party_master_duplicate_vouchers | Check | No |
| Duplicate Action | duplicate_voucher_action | Select | No |
| Bypass Role | role_to_bypass_duplicate_voucher | Link | No |

## Permissions
| Role | Read | Write | Create | Delete | Submit | Cancel | Amend |
|------|------|-------|--------|--------|--------|--------|-------|
| System Manager | ✓ | ✓ | ✓ | ✓ |  |  |  |
| Party Manager | ✓ | ✓ | ✓ | ✓ |  |  |  |
