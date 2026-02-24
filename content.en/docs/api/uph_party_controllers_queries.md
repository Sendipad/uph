---
title: "uph.party.controllers.queries"
weight: 10
---

# uph.party.controllers.queries

**Source File:** `party/controllers/queries.py`

## party_master_link_query
**Endpoint:** `uph.party.controllers.queries.party_master_link_query`

No description provided.

**Parameters:**
`doctype`, `txt`, `searchfield`, `start`, `page_len`, `filters`, `reference_doctype`

---
## get_party_master
**Endpoint:** `uph.party.controllers.queries.get_party_master`

No description provided.

**Parameters:**
`doctype`, `txt`, `searchfield`, `start`, `page_len`, `filters`

---
## get_party_master_parties
**Endpoint:** `uph.party.controllers.queries.get_party_master_parties`

No description provided.

**Parameters:**
`party_master`, `party_type`, `cached`

---
## get_all_vouchers_documents_with_null_or_another_party_master
**Endpoint:** `uph.party.controllers.queries.get_all_vouchers_documents_with_null_or_another_party_master`

No description provided.

**Parameters:**
`doctypes`, `parties`, `party_master`

---
## get_unlinked_party
**Endpoint:** `uph.party.controllers.queries.get_unlinked_party`

No description provided.

**Parameters:**
`filters`, `limit`

---
## get_linked_parties_list
**Endpoint:** `uph.party.controllers.queries.get_linked_parties_list`

No description provided.

**Parameters:**
`party_master_filters`, `party_type`

---
## get_counts_of_unposted_or_cancelled_vouchers
**Endpoint:** `uph.party.controllers.queries.get_counts_of_unposted_or_cancelled_vouchers`

Get counts of vouchers that are not posted or are cancelled.
Returns a list of dicts with 'party_master' and other basic info.

**Parameters:**
`company`, `party_master`, `is_party_gl_effected`

---
## get_party_analytic_accounting_filtered
**Endpoint:** `uph.party.controllers.queries.get_party_analytic_accounting_filtered`

Filter 'Party Analytic Accounting' by party_master.

**Parameters:**
`doctype`, `txt`, `searchfield`, `start`, `page_len`, `filters`

---
## query_similar_name_or_number
**Endpoint:** `uph.party.controllers.queries.query_similar_name_or_number`

Check for existing Party Master with same or similar name/number.
Returns dict with exact matches found.

**Parameters:**
`party_name`, `party_number`

---
## get_party_master_dashboard_info
**Endpoint:** `uph.party.controllers.queries.get_party_master_dashboard_info`

No description provided.

**Parameters:**
`party_master_name`

---
## get_party_master_history_stats
**Endpoint:** `uph.party.controllers.queries.get_party_master_history_stats`

No description provided.

**Parameters:**
`party_master`

---
