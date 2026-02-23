---
title: "Party Master Settings DocType"
weight: 10
description: "No description provided."
---

# Party Master Settings DocType

**Module:** Party

## Overview
No description provided.

## Fields
| Label | Fieldname | Type | Mandatory |
|-------|-----------|------|-----------|
| Document Type | document_type | Link | Yes |
| Parent DocType | parent_doctype | Link | No |
| Track Transaction Health | track_transaction_health | Select | No |
| Severity | transaction_health_severity | Select | No |
| Is Dynamic Party Type | is_dynamic_party_type | Check | No |
| Party FieldName | party_fieldname | Select | Yes |
| Party Type | party_type | Link | No |
| Party Type Fieldname | party_type_fieldname | Select | No |
| Mandatory | reqd | Check | No |
| Client Script | client_script | Link | No |
| Is System generated | is_system_generated | Check | No |
| Document Categories | document_categories | Select | No |
| Party Master Custom Field | party_master_custom_field | Link | No |
| Enabled | enabled | Check | No |
|  | column_break_brmi | Column Break | No |
| Warn If Un-Submitted Documents | warn_not_submitted_document | Check | No |

## Permissions
| Role | Read | Write | Create | Delete | Submit | Cancel | Amend |
|------|------|-------|--------|--------|--------|--------|-------|
