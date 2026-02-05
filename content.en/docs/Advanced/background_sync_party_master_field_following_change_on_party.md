---
title: "Background Sync Logic"
weight: 3
---

# Background Sync & transactional integrity 

One of the core promises of UPH is that every transactional document (Invoice, Order, Entry) is tagged with the correct `Party Master`.

## How it works

When you link a Party Master to a Customer or Supplier, the system triggers a background synchronization process to ensure data consistency.

### 1. The Trigger
The sync is triggered in two main scenarios:
- **Linking**: When a `Customer` is first linked to a `Party Master`.
- **Merging**: When two `Party Masters` are merged (via the Data Quality Dashboard).

### 2. The Background Job
To prevent timeouts on large databases, the update happens via a queued background job (`uph.party.controllers.mdm._update_party_master_references` or similar).

**Logic:**
1.  System identifies all configured Document Types (Sales Invoice, Purchase Order, etc.).
2.  It queries for documents where `party` matches the changed Customer/Supplier.
3.  It updates the `party_master` field to the new Party Master ID.
4.  Standard SQL update is used for speed, bypassing heavy framework validation for these maintenance updates.

### 3. Real-time Hook
For new documents, a `before_validate` hook automatically fetches the `party_master` from the selected Customer/Supplier, ensuring new data is always correct from the moment of creation.
