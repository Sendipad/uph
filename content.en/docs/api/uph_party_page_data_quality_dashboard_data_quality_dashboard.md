---
title: "uph.party.page.data_quality_dashboard.data_quality_dashboard"
weight: 10
---

# uph.party.page.data_quality_dashboard.data_quality_dashboard

**Source File:** `party/page/data_quality_dashboard/data_quality_dashboard.py`

## get_duplicate_issues
**Endpoint:** `uph.party.page.data_quality_dashboard.data_quality_dashboard.get_duplicate_issues`

Get duplicate Party Issues from the governance registry.

**Parameters:**
`limit`, `offset`, `min_score`, `party_master`

---
## get_dashboard_stats
**Endpoint:** `uph.party.page.data_quality_dashboard.data_quality_dashboard.get_dashboard_stats`

Get summary statistics sourced entirely from the Party Issue doctype.
Uses a single aggregation query for all issue counts.
Optionally filters by party_master.

**Parameters:**
`party_master`

---
## get_unlinked_voucher_issues
**Endpoint:** `uph.party.page.data_quality_dashboard.data_quality_dashboard.get_unlinked_voucher_issues`

Get unlinked vouchers by querying transaction tables directly.
Finds vouchers where party_master is NULL or empty.
Optionally filters by a specific party_master (for linked party checks).
Optionally filters by specific reference_doctype.

**Parameters:**
`limit`, `offset`, `party_master`, `reference_doctype`

---
## trigger_refresh
**Endpoint:** `uph.party.page.data_quality_dashboard.data_quality_dashboard.trigger_refresh`

Manually trigger background refresh of stats.

**Parameters:**
None

---
## dismiss_duplicate
**Endpoint:** `uph.party.page.data_quality_dashboard.data_quality_dashboard.dismiss_duplicate`

Dismiss a duplicate issue by setting status to Ignored.

**Parameters:**
`party_1`, `party_2`, `reason`

---
## merge_parties
**Endpoint:** `uph.party.page.data_quality_dashboard.data_quality_dashboard.merge_parties`

Merge secondary Party Master into primary Party Master.
Delegates to PartyMergeService.

**Parameters:**
`primary_party`, `secondary_party`, `fields_to_keep`, `ignore_validation`

---
