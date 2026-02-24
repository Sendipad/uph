---
title: "Installation, Setup, and Configuration"
weight: 3
---

# Installation and setup

## Prerequisites

- ERPNext/Frappe environment with Bench
- Installed dependency app: `erpnext` (required by hooks)
- Site admin access

## Install

```bash
bench get-app <uph-repository-url>
bench --site <site-name> install-app uph
bench --site <site-name> migrate
bench build --app uph
bench restart
```

## Post-install initialization

The app defines an `after_install` entrypoint and boot-time setup hooks. After install:

1. Open **Party Master Settings**.
2. Seed/validate party type table and document type mappings.
3. Create/update custom `party_master` fields on configured doctypes.
4. Confirm `party_master` appears in target forms.

# Configuration reference

## Party Master Settings

Main configuration areas inferred from the settings controller:

- **Party types rules** (`reqd`, `allowed`, `rule_fieldname`)
- **Document type mappings**
  - `document_type`
  - `parent_doctype`
  - `party_fieldname`
  - `party_type_fieldname`
  - dynamic-party-type behavior
- **Party master fields** mapping table for source/target field sync

The settings controller validates field existence and can reject non-system-manager edits for sensitive operations.

## Recommended rollout sequence

1. Configure party-type rules.
2. Configure transactional doctypes that need `party_master`.
3. Sync custom fields.
4. Backfill or relink existing records.
5. Enable/adjust data quality rules.
6. Validate with health and account reports.

# Usage examples

## Example A: Link existing parties

1. Create Party Master `PM-ACME`.
2. Add roles: Customer + Supplier.
3. Assign existing Customer/Supplier records to `PM-ACME`.
4. Save and verify linked count + report visibility.

## Example B: Auto-manage party master in transactions

1. In settings, map `Sales Invoice` and `Purchase Invoice`.
2. Ensure `party_fieldname` points to `customer`/`supplier`.
3. Save mapping and regenerate fields.
4. Create new transactions and verify `party_master` is set/validated.

## Example C: Data quality enforcement

1. Create Data Quality Rule for Customer.
2. Add conditions (Exact + Fuzzy match on name/phone/email).
3. Set action to warn or block.
4. Save a record and review duplicate alert behavior.
