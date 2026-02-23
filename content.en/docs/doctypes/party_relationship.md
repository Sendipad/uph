---
title: "Party Relationship"
weight: 10
description: "No description provided."
---

# Party Relationship

**Module:** Party

## Overview
No description provided.

## Fields
| Label | Fieldname | Type | Mandatory |
|-------|-----------|------|-----------|
| Relationship | section_parties | Section Break | No |
| Subject Party | subject_party | Link | Yes |
| Relationship Type | relationship_type | Link | Yes |
| Object Party | object_party | Link | Yes |
|  | column_break_1 | Column Break | No |
| Status | status | Select | No |
| Start Date | start_date | Date | No |
| End Date | end_date | Date | No |
| Details | section_details | Section Break | No |
| Ownership Percentage | ownership_percentage | Percent | No |
|  | column_break_2 | Column Break | No |
| Notes | notes | Small Text | No |
| Hierarchy Controls | section_hierarchy | Section Break | No |
| Primary Relationship | is_primary | Check | No |
|  | column_break_hierarchy | Column Break | No |
| Financial & Risk | section_financial | Section Break | No |
| Consolidate Financials | consolidate_financials | Check | No |
| Is Guarantor | is_guarantor | Check | No |
|  | column_break_financial | Column Break | No |
| Credit Allocation | credit_allocation | Currency | No |
| Governance | section_governance | Section Break | No |
| Termination Reason | termination_reason | Data | No |
| Authority Document Ref | authority_ref | Data | No |

## Permissions
| Role | Read | Write | Create | Delete | Submit | Cancel | Amend |
|------|------|-------|--------|--------|--------|--------|-------|
| System Manager | ✓ | ✓ | ✓ | ✓ |  |  |  |
| Accounts Manager | ✓ | ✓ | ✓ | ✓ |  |  |  |
| All | ✓ | ✓ | ✓ |  |  |  |  |
| Party Manager | ✓ | ✓ | ✓ | ✓ |  |  |  |
