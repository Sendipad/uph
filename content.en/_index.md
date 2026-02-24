---
title: "Unified Party Hub"
---

<div class="uph-landing">
  <section class="uph-hero">
    <h1>Unified Party Hub (UPH)</h1>
    <p>
      A Frappe/ERPNext extension for centralized Party Master identity, role-aware party mapping,
      advanced reporting, and data quality governance.
    </p>

    <p class="uph-badges">
      <a href="https://github.com/Sendipad/uph/actions/workflows/preview.yml?query=branch%3Adevelop">
        <img alt="Docs Preview (develop)" src="https://github.com/Sendipad/uph/actions/workflows/preview.yml/badge.svg?branch=develop" />
      </a>
      <a href="https://github.com/Sendipad/uph/actions/workflows/deploy.yml?query=branch%3Adevelop">
        <img alt="Deploy (develop)" src="https://github.com/Sendipad/uph/actions/workflows/deploy.yml/badge.svg?branch=develop" />
      </a>
      <a href="https://github.com/Sendipad/uph/commits/develop/">
        <img alt="Develop branch" src="https://img.shields.io/badge/branch-develop-2563eb" />
      </a>
      <a href="https://github.com/Sendipad/uph/blob/main/LICENSE">
        <img alt="License" src="https://img.shields.io/badge/license-MIT-22c55e" />
      </a>
    </p>

    <p>
      <a class="uph-cta" href="{{< relref \"/docs/introduction/_index.md\" >}}">Get Started</a>
      <a class="uph-cta secondary" href="{{< relref \"/docs/api/_index.md\" >}}">API Reference</a>
    </p>
  </section>

  <section>
    <h2>Core Features</h2>
    <div class="uph-cards">
      <article class="uph-card">
        <h3>Party Master Tree</h3>
        <p>Hierarchical identity model with parent/child traversal, role modeling, and numbered structure.</p>
      </article>
      <article class="uph-card">
        <h3>Transactional Validation</h3>
        <p>Global doc-event checks with auto-assignment support for <code>party_master</code> across configured doctypes.</p>
      </article>
      <article class="uph-card">
        <h3>Data Quality Rules</h3>
        <p>Normalization and duplicate detection with configurable actions for improved master data quality.</p>
      </article>
      <article class="uph-card">
        <h3>Reporting Suite</h3>
        <p>Account statement, balances, chronological ledger, and health reports for Party Master operations.</p>
      </article>
    </div>
  </section>
# Unified Party Hub (UPH) {anchor=false}
A Frappe/ERPNext extension for **centralized Party Master identity**, role-aware party mapping, and operational data quality controls.

{{< badge style="success" title="Status" value="Implementation-backed docs" >}}
[{{< badge style="info" title="Version" value="1.0" >}}](https://github.com/Sendipad/uph/releases)
[{{< badge style="default" title="License" value="MIT" >}}](https://github.com/Sendipad/uph/blob/main/LICENSE)

{{< button href="/docs/" >}}Read Technical Docs{{< /button >}}

  <section>
    <h2>Architecture & Modules</h2>
    <ul>
      <li><code>uph/hooks</code> for app integration, assets, doc events, boot and install hooks.</li>
      <li><code>uph/party/controllers</code> for validation, mapping, query APIs, and MDM behavior.</li>
      <li><code>uph/party/doctype</code> for Party Master + settings and related DocTypes.</li>
      <li><code>uph/party/report</code> for script reports and financial/health analytics.</li>
    </ul>
  </section>

  <section>
    <h2>Installation & Setup</h2>

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

See [API Reference]({{< relref "/docs/api/_index.md" >}}) for whitelisted/search/report function entry points extracted from current implementation.

---

### Footer

Version: `1.0` · License: [MIT](https://github.com/Sendipad/uph/blob/main/LICENSE) · Repository: [github.com/Sendipad/uph](https://github.com/Sendipad/uph)
