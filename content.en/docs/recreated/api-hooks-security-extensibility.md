---
title: "APIs, Hooks, Security, Extensibility, and Limitations"
weight: 4
---

# API Reference (Source-Inferred)

The repository references the following callable paths and integration surfaces:

## Party APIs

- `uph.party.controllers.party.get_party_details`
- `uph.party.controllers.party.set_party_master`

## Data Quality APIs

- `uph.party.controllers.mdm.normalize_text`
- `uph.party.controllers.mdm.validate_document_quality`
- `uph.party.page.data_quality_dashboard.get_potential_duplicates`
- `uph.party.page.data_quality_dashboard.merge_parties`
- `uph.party.page.data_quality_dashboard.dismiss_duplicate`
- `uph.party.page.data_quality_dashboard.get_dashboard_stats`

## Query API

- `uph.party.controllers.queries.party_master_link_query`

## Background Update Entry Points

- `uph.party.controllers.party.on_change_party_master_update_transactional_document_types`
- `uph.party.controllers.mdm._update_party_master_references` (documented as representative background sync function)

# Hooks and Background Jobs

## Hook Patterns (Documented)

- `validate`
- `before_validate`
- `on_update`
- `on_trash`

## Workflow Impact

- Enforce linkage and quality controls at save-time.
- Keep existing transactional records consistent after merge/relink events.
- Offload large updates into long queue jobs.

# Permissions and Security Model (Inferred)

1. Access control is expected to remain aligned with Frappe role permissions on involved DocTypes.
2. Whitelisted APIs should be treated as privileged business endpoints and protected by standard authentication/session controls.
3. Merge actions imply audit and governance requirements; maintain role-restricted access.
4. Bulk update jobs should be considered sensitive operations and scheduled on trusted queues.

# Integration Points

- ERPNext standard party masters (Customer/Supplier/Employee)
- Transactional DocTypes with injected `party_master` link fields
- Reports and dashboard pages
- Bench deployment lifecycle (`install-app`, `migrate`, `build`)

# Extensibility and Customization

## Supported Extension Approaches

- Add custom DocTypes to Party Master field-injection configuration.
- Register custom hook handlers around party validation life cycle.
- Extend normalization strategy for locale-specific data quality logic.
- Build custom analytics from Party Master and Party Analytic Accounting linkage.

## Documentation UI Customization

This repository now includes visible top-right actions per page to send context to:

- Ask ChatGPT
- Ask Gemini
- Ask Claude

The action prompt includes page title, URL, and page text excerpt.

# Known Limitations and Assumptions

1. This repository primarily contains documentation-site source; underlying Python app modules are not present here.
2. Detailed code-level behavior beyond referenced API paths cannot be fully validated from this repository alone.
3. URL-based prompt prefill support can vary by AI provider over time.
4. Large pages are truncated before context transmission to avoid URL-size limits.

# Developer Notes

- Site is Hugo-based using the Book theme.
- Menu and docs hierarchy are configuration-driven (`config.toml`) and content-structure-driven.
- Custom layout overrides live under `layouts/` and custom styling under `assets/custom.css` / `static/custom.css`.

