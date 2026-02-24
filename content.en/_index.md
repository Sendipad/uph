---
title: "Unified Party Hub"
layout: landing
---

<div class="book-hero">

# Unified Party Hub (UPH) {anchor=false}
A Frappe/ERPNext extension for **centralized Party Master identity**, role-aware party mapping, and operational data quality controls.

{{< badge style="success" title="Status" value="Implementation-backed docs" >}}
[{{< badge style="info" title="Version" value="1.0" >}}](https://github.com/Sendipad/uph/releases)
[{{< badge style="default" title="License" value="MIT" >}}](https://github.com/Sendipad/uph/blob/main/LICENSE)

{{< button href="/en/docs/" >}}Read Technical Docs{{< /button >}}

</div>

---

## Core Features

{{% columns %}}
- {{< card >}}
  ### Party Master Tree
  Hierarchical `Party Master` identity model with numbering, parent/child traversal, and role tables.
  {{< /card >}}

- {{< card >}}
  ### Transactional Validation
  Global hook-driven validation and optional auto-set of `party_master` across configured doctypes.
  {{< /card >}}

- {{< card >}}
  ### Reporting Layer
  Party account statement, balances, chronological ledger, and health reporting modules.
  {{< /card >}}
{{% /columns %}}

## Architecture Summary

- Hook layer (`uph/hooks`) integrates assets, boot session extension, install hook, and doc events.
- Controller layer enforces mapping rules and synchronization across transactional data.
- Query/report layer uses Frappe query builder utilities and cached mapping dictionaries.
- Data quality layer normalizes text and flags probable duplicates using configurable rules.

## Module Breakdown

- `uph/__init__`: cache key map + helper methods.
- `uph/party/boot`: boot payload augmentation.
- `uph/party/controllers/*`: queries, mapping validation, MDM checks.
- `uph/party/doctype/*`: Party Master + settings + rule doctypes.
- `uph/party/report/*`: financial/health script reports.

## Installation & Setup

```bash
bench get-app https://github.com/Sendipad/uph.git
bench --site <site-name> install-app uph
bench migrate
```

Then configure **Party Master Settings** to map target doctypes and party types.

## API Reference

See [API Reference](/en/docs/api/) for whitelisted/search/report function entry points extracted from current implementation.

---

### Footer

Version: `1.0` · License: [MIT](https://github.com/Sendipad/uph/blob/main/LICENSE) · Repository: [github.com/Sendipad/uph](https://github.com/Sendipad/uph)
