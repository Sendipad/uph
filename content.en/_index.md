---
title: "Unified Party Hub"
layout: landing
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

```bash
bench get-app https://github.com/Sendipad/uph.git
bench --site &lt;site-name&gt; install-app uph
bench migrate
```

    <p>Then configure Party Master Settings for party types and document mappings.</p>
  </section>

  <section>
    <h2>Documentation</h2>
    <p>Explore <a href="{{< relref \"/docs/_index.md\" >}}">full documentation</a> and <a href="{{< relref \"/docs/api/_index.md\" >}}">API reference</a>.</p>
  </section>
</div>
