---
title: "Installation, Configuration, and Usage"
weight: 3
---

# Installation & Setup

## Prerequisites

- Frappe/ERPNext deployment with bench tooling
- Python runtime supported by your ERPNext version
- MariaDB or PostgreSQL backend

## Installation Steps

```bash
bench get-app https://github.com/Sendipad/uph
bench --site <your-site> install-app uph
bench --site <your-site> migrate
bench build --app uph
bench restart
```

## Initial Validation Checklist

- Party workspace is visible
- Party Master Settings is available
- Core reports load successfully
- Data quality dashboard returns baseline metrics

# Configuration Guide

## Core Settings

Configure **Party Master Settings** first:

- Enable target party types (Customer/Supplier/Employee)
- Define uniqueness boundaries per role and currency
- Configure duplicate handling behavior (warn/stop)
- Set linked DocTypes that should receive `party_master`

## Data Governance Setup

- Define normalization and duplicate quality rules
- Set score threshold and review policy
- Add exclusion rules for known safe duplicates

## Reporting Setup

- Enable Party Analytic Accounting if used
- Configure default account/currency behavior
- Validate consolidated reports with sample records

# Feature-by-Feature Usage

## Unified Role Linking

Use Party Master as root and link Customer/Supplier/Employee records to maintain one legal-entity profile.

## Hierarchy Management

Create parent and child Party Masters for holding-company, regional, and branch-level structures.

## Relationship Management

Capture non-tree relations (ownership, affiliate, subsidiary) via Party Relationship model.

## Data Quality Dashboard

Use the dashboard APIs/UI to:

- monitor quality metrics,
- review possible duplicates,
- execute merges,
- track dismissed candidates.

## Reporting

Use Party Master-centric reports for cross-role financial and operational visibility.

# Usage Example (Operational)

1. Create `PM-ACME` as a Party Master.
2. Link existing Customer and Supplier records for Acme.
3. Configure account mapping for USD/EUR context.
4. Post sales and purchase transactions.
5. Review consolidated statement and quality status.

