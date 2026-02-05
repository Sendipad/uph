---
title: "Unified Party Hub"
layout: landing
---

<!-- Hero Section -->
<div class="book-hero" style="text-align:center; padding: 4rem 0; background: linear-gradient(to bottom right, #f8f9fa, #e9ecef);">
  <h1 style="font-size: 3rem; margin-bottom: 1rem; color: #2c3e50;">Master Data Management for ERPNext</h1>
  <p style="font-size: 1.25rem; color: #6c757d; max-width: 800px; margin: 0 auto 2rem;">
    Centralize, Unify, and Govern your party data with Unified Party Hub (UPH) - an enterprise-grade Master Data Management (MDM) extension for ERPNext.
  </p>
  
  <div style="margin: 2rem 0;">
    <a href="./docs/introduction/" class="book-btn" style="padding: 1rem 2rem; font-size: 1.1rem;">Get Started</a>
    <a href="https://github.com/Sendipad/uph" class="book-btn outline" style="padding: 1rem 2rem; font-size: 1.1rem; margin-left: 1rem;">⭐ Star on GitHub</a>
  </div>

  <div class="badges" style="margin-top: 1rem;">
    <a href="https://github.com/Sendipad/uph/releases">{{< badge style="info" title="Stable Version" value="v2.4.0" >}}</a>
    <a href="https://github.com/Sendipad/uph/blob/main/license.txt">{{< badge style="default" title="License" value="GPL-3.0" >}}</a>
    <a href="https://github.com/Sendipad/uph/actions/workflows/test_v15.yml">{{< badge style="success" title="ERPNext v15+" value="Supported" >}}</a>
    <a href="https://github.com/Sendipad/uph/actions/workflows/test_develop.yml">{{< badge style="warning" title="Develop (v16)" value="Testing" >}}</a>
    <a href="https://github.com/Sendipad/uph">{{< badge style="secondary" title="Localization" value="Arabic 100%" >}}</a>
  </div>
</div>

<!-- Features Architecture -->
<div style="max-width: 1200px; margin: 4rem auto; padding: 0 1rem;">
  <h2 style="text-align: center; margin-bottom: 3rem;">Key Features</h2>

  {{% columns %}}
  
  {{< card header="🛡️ Party Identity Governance" >}}
  **Data Quality Dashboard**
  Real-time insights into data quality and completeness with governance score tracking, linkage stats, and duplicate detection using fuzzy matching.
  {{< /card >}}

  {{< card header="🚀 Production-Ready Onboarding" >}}
  **Smart Linking & Wizard**
  Smart linking dialog for bulk-associating unlinked ERPNext parties and a wizard to instantly provision new roles from existing Party Masters, inheriting address, contact, and tax data.
  {{< /card >}}

  {{< card header="💱 Hierarchical Multi-Currency Support" >}}
  **Intelligent GL Account Resolution**
  Define group accounts at Party Master level with automatic hierarchy traversal to find specific leaf accounts matching transaction currency.
  {{< /card >}}

  {{% /columns %}}

  <div style="margin-top: 2rem;"></div>

  {{% columns %}}

  {{< card header="⚡ High-Performance Architecture" >}}
  **SmartCache System**
  Robust caching layer (Redis) ensures instant retrieval of party details and configuration, even with millions of records.
  {{< /card >}}

  {{< card header="📊 Party Analytic Accounting" >}}
  **Oracle TCA-like Sites**
  Separate accounting dimension for party-level financial reporting, enabling P&L or Balance Sheet for specific branches/sites without cluttering the chart of accounts.
  {{< /card >}}

  {{< card header="🌳 Tree-Based Hierarchy" >}}
  **Organizational Structure**
  Party Master supports tree-based hierarchy to model complex organizational structures (Holding Company -> Regional Office -> Local Branch) with consolidated financial visibility.
  {{< /card >}}

  {{% /columns %}}
</div>

<!-- Problem Solution Section -->
<div style="max-width: 1200px; margin: 4rem auto; padding: 0 1rem; background-color: #f8f9fa; border-radius: 8px; padding: 3rem;">
  <h2 style="text-align: center; margin-bottom: 2rem;">The Problem with Standard ERPNext</h2>
  
  {{% columns %}}
  
  {{< card header="Fragmented Identity" >}}
  A single legal entity acting as both Customer and Supplier exists as two disconnected documents.
  {{< /card >}}

  {{< card header="Multi-Currency Complexity" >}}
  Transacting in multiple currencies often requires duplicate party records (e.g., "Customer USD", "Customer EUR").
  {{< /card >}}

  {{< card header="Siloed Reporting" >}}
  Financial reports are segmented by specific Party records, making it difficult to get a 360-degree view.
  {{< /card >}}

  {{% /columns %}}

  <div style="text-align: center; margin-top: 3rem;">
    <h3>UPH Solves These Problems</h3>
    <p style="font-size: 1.1rem; color: #6c757d; max-width: 800px; margin: 1rem auto;">
      By treating the "Party" as a single legal entity and "Roles" (Customer, Supplier) as attributes, UPH delivers true multi-currency support, unified analytic accounting, and 360-degree visibility.
    </p>
  </div>
</div>

<!-- Social Proof / CTA -->
<div style="text-align:center; margin: 4rem 0; padding: 3rem; background-color: #f8f9fa; border-radius: 8px;">
  <h3>Ready to upgrade your ERPNext experience?</h3>
  <div style="margin-top:2rem;">
    <iframe src="https://ghbtns.com/github-btn.html?user=Sendipad&repo=uph&type=star&count=true&size=large" frameborder="0" scrolling="0" width="170" height="30" title="GitHub"></iframe>
  </div>
</div>
