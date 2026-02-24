---
title: "uph.party.utils"
weight: 10
---

# uph.party.utils

**Source File:** `party/utils.py`

## get_party_master_list
**Endpoint:** `uph.party.utils.get_party_master_list`

SECURE: Rewritten using pypika query builder to prevent SQL injection.
Returns list of Party Masters for link field searches.

Security fixes:
- No string formatting in SQL
- All parameters properly escaped by pypika
- Field names validated against meta

**Parameters:**
`doctype`, `txt`, `searchfield`, `start`, `page_len`, `filters`

---
