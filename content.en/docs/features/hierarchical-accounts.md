---
title: "Hierarchical Account Lookup"
weight: 8
---

# Hierarchical Account Lookup

UPH provides an intelligent, currency-aware account resolution system that traverses the Party Master hierarchy to find the most appropriate accounting link for a transaction.

## Overview

In traditional ERPNext, accounts are usually linked directly to a Customer or Supplier. In UPH, you can centralize account management at any level of the Party Master tree, allowing for:
- **Centralized Group Accounts**: Link a group account to a Parent PM, and all children will automatically resolve to correct currency-specific leaf accounts under that group.
- **Specific Leaf Overrides**: Link a specific leaf account to a Child PM for precise control.
- **Currency Strictness**: Ensure that transactions only use accounts matching the transaction currency.

---

## How it Works

When selecting a Party Master in a transaction (e.g., Sales Invoice), UPH performs the following steps:

1.  **Direct Match**: Checks the selected Party Master for an account mapping matching the **Company** and **Currency**.
2.  **Breadcrumb Traversal**: If no match is found, it moves up to the **Parent Party Master** and repeats the search.
3.  **Generic Fallback**: If "Enforce Strict Currency" is disabled, it also looks for mappings with NO currency specified as a global fallback.
4.  **Group Expansion**: If a matched account is a **Group Account**, UPH automatically searches for a **Leaf Account** under that group that matches the target currency.

---

## Configuration

### 1. Account Mapping

Mappings are defined in the **Accounts** table of the **Party Master** Doctype.

| Field | Description |
|-------|-------------|
| **Company** | The company this mapping applies to. |
| **Currency** | (Optional) The currency for this mapping. Leave empty for a generic fallback. |
| **Account** | The Group or Leaf account to use. |

### 2. Strict Currency Enforcement

In **Party Master Settings**, you can enable **Enforce Strict Currency**. 

- **Enabled**: Only accounts with an exact currency match will be resolved. If no specific currency match is found in the hierarchy, no account will be auto-filled.
- **Disabled**: UPH will fallback to generic account mappings (where currency is empty) if no specific currency match is found.

---

## Best Practices

### Multi-Currency Parent
If you have a global parent company with multiple local branches (Child PMs), link a **Group Receivable/Payable Account** to the Parent PM. Ensure that the Group Account contains child accounts for each required currency (USD, SAR, etc.). UPH will automatically pick the correct child account based on the invoice currency.

### Local Overrides
If one specific Child PM uses a completely different bank or account structure, link that specific account directly to the Child PM. It will take precedence over any hierarchical settings.
