---
title: "Configuration"
weight: 3
---

# Configuration Guide

Configure Unified Party Hub (UPH) to match your organization's requirements using Party Master Settings.

## Accessing Party Master Settings

1.  Navigate to **Party > Party Master Settings**.
2.  Configure the settings as described below.

---

## Party Types Configuration

Configure which party types are managed by UPH:

| Setting | Description |
|---------|-------------|
| **Party Type** | Select the party type (Customer, Supplier, Employee) |
| **Required** | Make Party Master mandatory for this party type |
| **Allowed** | Allow this party type to be linked |
| **Rule Fieldname** | Field to use for uniqueness validation |

### Example Configuration

| Party Type | Required | Allowed | Rule Fieldname |
|------------|----------|---------|----------------|
| Customer | Yes | Yes | default_currency |
| Supplier | Yes | Yes | default_currency |
| Employee | No | Yes | - |

---

## Document Types Configuration

Configure which transactional documents support Party Master:

| Setting | Description |
|---------|-------------|
| **Parent DocType** | The main document (e.g., Sales Invoice) |
| **Document Type** | The child document (e.g., Sales Invoice Item) |
| **Party Fieldname** | Field containing the party reference |
| **Party Type Fieldname** | Field containing the party type |
| **Required** | Make Party Master mandatory |

### Default Configured Documents

- Sales Invoice / Sales Invoice Item
- Purchase Invoice / Purchase Invoice Item
- Journal Entry / Journal Entry Account
- Payment Entry / Payment Entry Reference
- Sales Order / Sales Order Item
- Purchase Order / Purchase Order Item
- Delivery Note / Delivery Note Item
- Purchase Receipt / Purchase Receipt Item
- Expense Claim

---

## Party Analytic Accounting

Enable and configure party-level financial reporting:

| Setting | Description |
|---------|-------------|
| **Enable Party Analytic Accounting** | Activate the accounting dimension |
| **Dimension Name** | Display name for the dimension |
| **Mandatory** | Require dimension selection on transactions |

### Setting Up

1.  Enable "Party Analytic Accounting" in settings.
2.  Navigate to **Party > Party Analytic Accounting**.
3.  Create records for each branch/site/office.
4.  Link each analytic account to a Party Master.

---

## Data Quality Rules

Configure rules to prevent duplicate party records:

### Creating a Rule

1.  Navigate to **Party > Data Quality Rule**.
2.  Click **New**.
3.  Configure:
    - **Document Type**: Select Customer, Supplier, or Party Master
    - **Trigger**: On Save or On Submit
    - **Action**: Block or Warn
    - **Threshold Score**: Minimum similarity score (0-100)
    - **Conditions**: Define matching criteria

### Example Rule

```yaml
Rule Name: Duplicate Customer Detection
Document Type: Customer
Trigger: On Save
Action: Block
Threshold Score: 85

Conditions:
- Field: customer_name
  Check Type: Fuzzy Match
  Weight: 100
  Minimum Similarity: 80

- Field: tax_id
  Check Type: Exact Match
  Weight: 100
```

---

## General Settings

| Setting | Description |
|---------|-------------|
| **Enable Party Analytic Accounting** | Activate PAA dimension |
| **Check Party Master Duplicate Vouchers** | Prevent duplicate vouchers for same party master |
| **Auto-set Party Master** | Automatically set PM on transactional documents |

---

## Caching Configuration

UPH uses SmartCache for performance. Cache settings are automatic but can be cleared:

1.  Navigate to **Party Master Settings**.
2.  Click **Clear All Caches**.
3.  Confirm the action.

---

## Troubleshooting

### Party Master Not Showing

- Verify the party type is configured in Party Master Settings
- Check that the user has appropriate permissions
- Clear browser cache and refresh

### Duplicate Detection Not Working

- Ensure Data Quality Rules are enabled
- Check that rules have correct threshold scores
- Verify normalization settings for Arabic text

### Performance Issues

- Clear and rebuild caches
- Check database indexes on party_master field
- Review scheduled jobs for background processing
