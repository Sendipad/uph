---
title: "uph.party.controllers.unlinked_resolver"
weight: 10
---

# uph.party.controllers.unlinked_resolver

**Source File:** `party/controllers/unlinked_resolver.py`

## get_unlinked_parties
**Endpoint:** `uph.party.controllers.unlinked_resolver.get_unlinked_parties`

Find ERPNext role records where party_master is NULL or empty.

Returns paginated results grouped by role DocType with total count.
Uses Redis cache for the total count (5-min TTL).

**Parameters:**
`limit`, `offset`, `role_doctype`

---
## get_unlinked_transactions
**Endpoint:** `uph.party.controllers.unlinked_resolver.get_unlinked_transactions`

Find ERPNext transactions where party_master is NULL or empty.
Vouchers like Sales Invoice, Payment Entry, etc.
For child doctypes (e.g. Journal Entry Account), resolves the parent
document name so the UI links to the parent (e.g. Journal Entry).

**Parameters:**
`limit`, `offset`, `transaction_doctype`

---
## get_unlinked_suggestions
**Endpoint:** `uph.party.controllers.unlinked_resolver.get_unlinked_suggestions`

Suggest Party Masters that might match an unlinked role record.
Uses normalized name similarity.

**Parameters:**
`role_doctype`, `role_name`, `limit`

---
## link_to_party_master
**Endpoint:** `uph.party.controllers.unlinked_resolver.link_to_party_master`

Link an unlinked role record to a Party Master.
Validates the Party Master is appropriate for the role.

**Parameters:**
`role_doctype`, `role_name`, `party_master`

---
## create_party_master_from_unlinked_role
**Endpoint:** `uph.party.controllers.unlinked_resolver.create_party_master_from_unlinked_role`

Create a new Party Master from an unlinked role record.
Automatically finds a parent group and links the record.

**Parameters:**
`role_doctype`, `role_name`

---
## get_unlinked_issues
**Endpoint:** `uph.party.controllers.unlinked_resolver.get_unlinked_issues`

Fetch unlinked issues from Party Issue (governance registry).
For child doctypes, resolves the parent document name from the
child row's `parent` field so the UI can link to it correctly.

**Parameters:**
`limit`, `offset`, `party_master`

---
## resolve_unlinked_voucher
**Endpoint:** `uph.party.controllers.unlinked_resolver.resolve_unlinked_voucher`

Called from the Dashboard's Unlinked Vouchers tab.
Links the underlying role (e.g. Customer, Supplier) to a Party Master.
This naturally cascades to the historical voucher and resolves the issue.

**Parameters:**
`role_doctype`, `role_name`, `party_master`

---
