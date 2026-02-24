---
title: "Party Issue"
weight: 10
description: "No description provided."
---

# Party Issue

**Module:** Party

## Overview
No description provided.

## Fields
| Label | Fieldname | Type | Mandatory |
|-------|-----------|------|-----------|
| Details | details_section | Section Break | No |
| Issue Type | issue_type | Select | Yes |
| Severity | severity | Select | Yes |
| Status | status | Select | Yes |
|  | column_break_core | Column Break | No |
| Party | party | Link | Yes |
| Secondary Party | party_secondary | Link | No |
| Score | score | Float | No |
| Reference | section_break_reference | Section Break | No |
| Reference DocType | reference_doctype | Link | No |
| Reference Name | reference_name | Dynamic Link | No |
| Details HTML | details_html | HTML | No |
| Details JSON | details_json | Long Text | No |
| Metadata | section_break_meta | Section Break | No |
| Source Engine | source_engine | Data | No |
| Detected On | detected_on | Datetime | No |
| Resolved On | resolved_on | Datetime | No |
| Resolved By | resolved_by | Link | No |
| Dismiss Reason | dismiss_reason | Small Text | No |

## Permissions
| Role | Read | Write | Create | Delete | Submit | Cancel | Amend |
|------|------|-------|--------|--------|--------|--------|-------|
| System Manager | ✓ | ✓ | ✓ |  |  |  |  |
| Party Manager | ✓ | ✓ | ✓ |  |  |  |  |
