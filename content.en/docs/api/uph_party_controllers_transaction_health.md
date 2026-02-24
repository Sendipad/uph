---
title: "uph.party.controllers.transaction_health"
weight: 10
---

# uph.party.controllers.transaction_health

**Source File:** `party/controllers/transaction_health.py`

## get_transaction_health
**Endpoint:** `uph.party.controllers.transaction_health.get_transaction_health`

Find Party Masters with open Transaction Policy issues.
Returns paginated list aggregated by (party, reference_doctype), sorted by doctype.
Severity is determined by per-doctype warn_not_submitted_document setting.

**Parameters:**
`limit`, `offset`, `party_master`, `reference_doctype`

---
## get_party_health_detail
**Endpoint:** `uph.party.controllers.transaction_health.get_party_health_detail`

Drill-down: list individual policy issues for a given Party Master.

**Parameters:**
`party_master`, `reference_doctype`

---
## resolve_health_issue
**Endpoint:** `uph.party.controllers.transaction_health.resolve_health_issue`

Resolve a specific transaction health issue (e.g. submit draft, cancel).
Action can be 'submit', 'cancel', or 'dismiss'.

**Parameters:**
`issue_name`, `action`

---
