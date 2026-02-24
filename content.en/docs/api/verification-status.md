---
title: "Verification Status (Current Branch vs Legacy API Docs)"
weight: 1
---

# Verification Status

This page was added to answer the review concern about deleted docs.

## What was changed

- Legacy API documentation pages were restored.
- No legacy API page was deleted in this revision.

## Verification scope

Because this workspace snapshot does not include a local `develop` branch (or remote refs), verification was performed against the **current checked-out branch artifacts**.

## Current branch artifacts found

Available implementation files are mainly compiled Python bytecode (`.pyc`) under `uph/**/__pycache__/`.

Verified modules present in this branch snapshot include:

- `uph.__init__`
- `uph.hooks`
- `uph.install`
- `uph.party.boot`
- `uph.party.utils`
- `uph.party.controllers.field`
- `uph.party.controllers.mdm`
- `uph.party.controllers.party`
- `uph.party.controllers.queries`
- `uph.party.doctype.party_master.party_master`
- `uph.party.doctype.party_master_settings.party_master_settings`
- `uph.party.report.party_account_statement.party_account_statement`
- `uph.party.report.party_account_balances.party_account_balances`
- `uph.party.report.chronological_party_ledger.chronological_party_ledger`
- `uph.party.report.party_master_health_report.party_master_health_report`
- `uph.regional.arabic`

## Legacy API pages with uncertain module presence in this snapshot

The following legacy pages were restored, but corresponding module artifacts were not found in the current snapshot and may represent `develop`-only or older code:

- `uph_party_controllers_duplicate_scanner`
- `uph_party_controllers_party_merge_service`
- `uph_party_controllers_transaction_health`
- `uph_party_controllers_unlinked_resolver`
- `uph_party_page_data_quality_dashboard_data_quality_dashboard`
- `uph_party_page_uph_setup_wizard_uph_setup_wizard`
- `uph_party_dashboard_chart_source_party_identity_governance_party_identity_governance`
- `uph_party_doctype_party_relationship_party_relationship`

If you want exact `develop` verification, provide the `develop` branch in this workspace (or a remote URL) and this page can be upgraded to a strict line-by-line compatibility matrix.
