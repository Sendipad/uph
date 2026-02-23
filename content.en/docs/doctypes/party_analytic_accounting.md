---
title: "Party Analytic Accounting"
weight: 10
description: "This record enforces the principle of Accounting Non-Duplication for the Party Master. It eliminates the need to create redundant accounts for the same customer or supplier (e.g., customer branches) solely for segmented reporting or financial data separation. Instead, it is used to define and assign unique Analytical Accounting Dimensions to each related entity of the Party Master. This approach maintains a single, unified Party record while enabling detailed financial segmentation and reporting through customized analytical dimensions (PAA), significantly boosting accounting governance efficiency and reducing Chart of Accounts complexity."
---

# Party Analytic Accounting

**Module:** Party

## Overview
This record enforces the principle of Accounting Non-Duplication for the Party Master. It eliminates the need to create redundant accounts for the same customer or supplier (e.g., customer branches) solely for segmented reporting or financial data separation. Instead, it is used to define and assign unique Analytical Accounting Dimensions to each related entity of the Party Master. This approach maintains a single, unified Party record while enabling detailed financial segmentation and reporting through customized analytical dimensions (PAA), significantly boosting accounting governance efficiency and reducing Chart of Accounts complexity.

## Fields
| Label | Fieldname | Type | Mandatory |
|-------|-----------|------|-----------|
| Enabled | enabled | Check | No |
| Display Name | analytic_name | Data | Yes |
| Party Master | party_master | Link | Yes |
|  | column_break_uxoa | Column Break | No |
| Is Default | is_default | Check | No |
| Details | details_section | Section Break | No |
| Type | type | Select | Yes |
| Status | status | Select | No |
| Validaty | validaty_section | Section Break | No |
| Effective From | effective_from | Date | No |
|  | column_break_jufz | Column Break | No |
| Effective To | effective_to | Date | No |
| Title | title | Data | No |
| Rule Applied | section_break_fana | Section Break | No |
|  | column_break_grmf | Column Break | No |
| Applicable For Parties | parties | Table | No |
| Applicable On Companies | companies | Table | No |
| Allowed or Restrict to Below Rule  | allow_or_restrict | Select | Yes |

## Permissions
| Role | Read | Write | Create | Delete | Submit | Cancel | Amend |
|------|------|-------|--------|--------|--------|--------|-------|
| System Manager | ✓ | ✓ | ✓ | ✓ |  |  |  |
| Party Manager | ✓ | ✓ | ✓ | ✓ |  |  |  |
