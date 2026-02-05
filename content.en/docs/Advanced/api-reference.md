---
title: "API Reference"
weight: 4
---

# API Reference

UPH exposes several API endpoints and utility functions for integrations and customizations.

## Whitelisted Methods

### Party Management

#### `uph.party.controllers.party.get_party_details`
Overrides standard ERPNext logic to inject Party Master data (Addresses, Contacts) into transactions.

```python
# Example usage in custom script
details = frappe.call('uph.party.controllers.party.get_party_details', {
    'party': 'Customer001',
    'party_type': 'Customer',
    'company': 'My Company'
})
```

#### `uph.party.controllers.party.set_party_master`
Link selected parties to a Party Master.

```python
frappe.call('uph.party.controllers.party.set_party_master', {
    'selection': [
        {'party_type': 'Customer', 'name': 'Customer001'},
        {'party_type': 'Supplier', 'name': 'Supplier001'}
    ],
    'party_master': 'PM-001'
})
```

### Data Quality & MDM

#### `uph.party.controllers.mdm.normalize_text`
Normalize text for fuzzy matching (removes diacritics, unifies characters).

```python
from uph.party.controllers.mdm import normalize_text

normalized = normalize_text("Abdul-Rahman")
# Returns: "abdulrahman"
```

#### `uph.party.controllers.mdm.validate_document_quality`
Run configured Data Quality Rules against a document.

```python
frappe.call('uph.party.controllers.mdm.validate_document_quality', {
    'doc': doc.name,
    'doctype': 'Party Master'
})
```

### Data Quality Dashboard APIs

#### `get_potential_duplicates`
Get potential duplicate Party Masters based on similarity scoring.

```python
frappe.call('uph.party.page.data_quality_dashboard.get_potential_duplicates', {
    'limit': 50,
    'offset': 0,
    'min_score': 70.0
})
```

#### `merge_parties`
Merge secondary party into primary party.

```python
frappe.call('uph.party.page.data_quality_dashboard.merge_parties', {
    'primary_party': 'PM-001',
    'secondary_party': 'PM-002',
    'fields_to_keep': {
        'tax_id': 'PM-002',
        'mobile_no': 'PM-002'
    }
})
```

#### `dismiss_duplicate`
Dismiss a potential duplicate pair.

```python
frappe.call('uph.party.page.data_quality_dashboard.dismiss_duplicate', {
    'party_1': 'PM-001',
    'party_2': 'PM-002',
    'reason': 'Different legal entities'
})
```

#### `get_dashboard_stats`
Get summary statistics for the data quality dashboard.

```python
frappe.call('uph.party.page.data_quality_dashboard.get_dashboard_stats')
```

---

## Utility Functions

### Normalization Utilities

```python
from uph.party.controllers.normalization import NormalizationUtils

# Normalize text for fuzzy matching
normalized = NormalizationUtils.normalize("Abdul-Rahman")

# Get similarity score between two texts
score = NormalizationUtils.get_similarity_score("Acme Corp", "Acme Corporation")
# Returns: 85.0 (percentage)

# Check if two texts are similar
is_similar = NormalizationUtils.is_similar("John Doe", "Johnathan Doe", threshold=80.0)
# Returns: True

# Normalize party name specifically
normalized_name = NormalizationUtils.normalize_party_name("ABC LLC")
```

### Cache Utilities

```python
from uph.party.controllers.cache_utils import SmartCache

# Get cached value
value = SmartCache.get_cached_value('my_key', generator_function)

# Set cached value
SmartCache.set_cached_value('my_key', my_value)

# Invalidate cache
SmartCache.delete_cached_value('my_key')

# Get party master parties list
parties = SmartCache.get_party_master_parties('PM-001')
```

---

## Hook Integration

### Document Events

UPH automatically hooks into document events for:

- **validate**: Validates party master linkage on transactions
- **on_update**: Updates linked parties count
- **on_trash**: Handles party deletion

Example custom hook:

```python
# In your app's hooks.py
doc_events = {
    "Custom Party": {
        "validate": "uph.party.controllers.party.validate_party_master_on_document_types",
    }
}
```

### Overridden Methods

UPH overrides the following whitelisted methods:

| Original Method | UPH Override |
|-----------------|--------------|
| `erpnext.accounts.party.get_party_details` | `uph.party.controllers.party.get_party_details` |

---

## Query Functions

### Party Master Link Query

Optimized link query with usage-based ranking:

```python
frappe.call('uph.party.controllers.queries.party_master_link_query', {
    'txt': 'search',
    'searchfield': 'party_name',
    'start': 0,
    'page_len': 20,
    'filters': {'party_type': 'Customer'}
})
```

---

## Event Handlers

### On Party Master Change

When a party master is changed on a party record, UPH:

1. Enqueues a background job to update all related transactional documents
2. Updates the linked party count
3. Invalidates relevant caches

```python
frappe.enqueue(
    'uph.party.controllers.party.on_change_party_master_update_transactional_document_types',
    party=doc,
    old_party_master=old_pm,
    queue='long'
)
```
