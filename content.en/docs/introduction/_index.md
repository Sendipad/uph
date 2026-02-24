---
title: "Introduction"
weight: 2
---

# Unified Party Hub (UPH)

UPH is a Frappe/ERPNext extension that centralizes party identity into a **Party Master** tree and links role-specific parties (Customer, Supplier, Employee, etc.) to that identity.

## Value delivered by implementation

- Shared identity with multi-role mapping (`Party Master.roles`, `Party Master.parties`).
- Auto-validation and optional auto-assignment of `party_master` on configured transactional documents.
- Query/report layer for party ledgers, balances, statements, and data health.
- Data quality controls (normalization + duplicate scanning + rule actions).
- Redis-backed caches for cross-doctype party mappings and list lookups.

## Prerequisites

- Frappe bench environment.
- ERPNext installed (declared in hooks `required_apps = ["erpnext"]`).

## Installation (bench)

```bash
bench get-app https://github.com/Sendipad/uph.git
bench --site <site-name> install-app uph
bench migrate
```

After install, UPH runs app setup hooks and injects Party Master behavior via `doc_events` handlers.
