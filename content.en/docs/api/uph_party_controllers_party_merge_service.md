---
title: "uph.party.controllers.party_merge_service"
weight: 10
---

# uph.party.controllers.party_merge_service

**Source File:** `party/controllers/party_merge_service.py`

## merge_party_masters
**Endpoint:** `uph.party.controllers.party_merge_service.merge_party_masters`

API endpoint for merging Party Masters.

Args:
    primary_party: The Party Master to keep
    secondary_party: The Party Master to merge and delete
    fields_to_keep: Optional dict of fields to copy from secondary

Returns:
    dict with success status and merge details

**Parameters:**
`primary_party`, `secondary_party`, `fields_to_keep`, `ignore_validation`

---
