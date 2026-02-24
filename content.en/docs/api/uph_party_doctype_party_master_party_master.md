---
title: "uph.party.doctype.party_master.party_master"
weight: 10
---

# uph.party.doctype.party_master.party_master

**Source File:** `party/doctype/party_master/party_master.py`

## get_party_master_balances
**Endpoint:** `uph.party.doctype.party_master.party_master.get_party_master_balances`

No description provided.

**Parameters:**
`company`, `name`

---
## get_next_party_master_number
**Endpoint:** `uph.party.doctype.party_master.party_master.get_next_party_master_number`

Hierarchical numbering with proper padding and sibling checks.

**Parameters:**
`parent`, `is_group`

---
## get_totals_number_unlinked_parties
**Endpoint:** `uph.party.doctype.party_master.party_master.get_totals_number_unlinked_parties`

No description provided.

**Parameters:**
`filters`

---
## check_similar_party_name
**Endpoint:** `uph.party.doctype.party_master.party_master.check_similar_party_name`

No description provided.

**Parameters:**
`party_name`, `doctype`, `start`, `page_len`

---
## create_party_master
**Endpoint:** `uph.party.doctype.party_master.party_master.create_party_master`

Create new Party Master with validation

**Parameters:**
`doc`

---
## get_linked_parties_with_analytic_list
**Endpoint:** `uph.party.doctype.party_master.party_master.get_linked_parties_with_analytic_list`

No description provided.

**Parameters:**
`party_master`, `party`, `party_type`, `doctype`, `party_field`

---
## assign_party_master_for_selection
**Endpoint:** `uph.party.doctype.party_master.party_master.assign_party_master_for_selection`

No description provided.

**Parameters:**
`old_party_master`, `new_party_master`, `selections`

---
## get_children
**Endpoint:** `uph.party.doctype.party_master.party_master.get_children`

Get child nodes with support for focused leaf view

**Parameters:**
`doctype`, `parent`, `company`, `name`, `is_root`

---
## get_parents
**Endpoint:** `uph.party.doctype.party_master.party_master.get_parents`

Get parent chain for a party master.

**Parameters:**
`doctype`, `name`

---
## get_party_master_details_with_parties
**Endpoint:** `uph.party.doctype.party_master.party_master.get_party_master_details_with_parties`

Get party master details with all linked parties.

**Parameters:**
`party_master_name`

---
## get_parties
**Endpoint:** `uph.party.doctype.party_master.party_master.get_parties`

No description provided.

**Parameters:**
`party_master`, `fromdb`, `party_type`

---
## get_unset_parties_list
**Endpoint:** `uph.party.doctype.party_master.party_master.get_unset_parties_list`

No description provided.

**Parameters:**
`doctype`, `txt`, `searchfield`, `start`, `page_len`, `filters`, `as_dict`

---
## create_party_from_party_master
**Endpoint:** `uph.party.doctype.party_master.party_master.create_party_from_party_master`

No description provided.

**Parameters:**
`source_name`, `target_doctype`, `rule_field_value`, `group`, `save`

---
## map_party_to_target
**Endpoint:** `uph.party.doctype.party_master.party_master.map_party_to_target`

No description provided.

**Parameters:**
`source_name`, `target_doctype`, `rule_field_value`, `save`

---
## update_linked_parties_details
**Endpoint:** `uph.party.doctype.party_master.party_master.update_linked_parties_details`

Update details of all linked parties.

**Parameters:**
`self`

---
## set_party_master
**Endpoint:** `uph.party.doctype.party_master.party_master.set_party_master`

Link selected parties to this Party Master.
Requires write permission on Party Master.

**Parameters:**
`self`, `selection`

---
## fetch_parties_list
**Endpoint:** `uph.party.doctype.party_master.party_master.fetch_parties_list`

Fetch similar parties for linking.
Returns list of parties based on filters.

**Parameters:**
`self`, `filters`

---
## assign_new_party_master_for_parties
**Endpoint:** `uph.party.doctype.party_master.party_master.assign_new_party_master_for_parties`

Assign new Party Master to selected parties.
Requires write permission on current Party Master.

**Parameters:**
`self`, `selections`

---
## set_secondary_party_roles
**Endpoint:** `uph.party.doctype.party_master.party_master.set_secondary_party_roles`

Add secondary role to this Party Master.

**Parameters:**
`self`, `role`

---
