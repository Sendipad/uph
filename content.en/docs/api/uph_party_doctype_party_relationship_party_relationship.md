---
title: "uph.party.doctype.party_relationship.party_relationship"
weight: 10
---

# uph.party.doctype.party_relationship.party_relationship

**Source File:** `party/doctype/party_relationship/party_relationship.py`

## get_party_relationships
**Endpoint:** `uph.party.doctype.party_relationship.party_relationship.get_party_relationships`

Get all relationships for a party master.

Args:
    party_master: Name of the Party Master
    direction: 'outgoing' (as subject), 'incoming' (as object), or 'all'

Returns:
    List of relationship records

**Parameters:**
`party_master`, `direction`

---
## get_related_parties
**Endpoint:** `uph.party.doctype.party_relationship.party_relationship.get_related_parties`

Get all parties related to the given party master.

Args:
    party_master: Name of the Party Master
    relationship_type: Optional filter by relationship type

Returns:
    List of related party names with relationship details

**Parameters:**
`party_master`, `relationship_type`

---
