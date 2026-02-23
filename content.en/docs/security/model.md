---
title: "Security Model"
weight: 10
---

# Security & Compliance

## Permission Model
UPH leverages Frappe's robust Role-Based Access Control (RBAC). Core roles include:
- **System Manager**: Full access to settings and MDM configuration.
- **Party Manager**: Management of Party Master records and daily operations.
- **Accounts Manager**: Financial visibility and analytic accounting configuration.

## Risk Assessment
The following security considerations were identified during the architectural audit:
- **API Security**: Whitelisted methods are being systematically audited to ensure `frappe.has_permission` checks are consistently applied.
- **Data Governance**: The `Setup Finished` flag locks core governance settings post-initialization to prevent unauthorized changes in production environments.

## Data Protection
All party interactions are logged and audited via the `Party Issue` system, providing a clear trail of data quality adjustments and links.
