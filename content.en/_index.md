---
title: "Unified Party Hub"
layout: landing
---

<!-- Hero Section -->
<div class="book-hero" style="text-align:center; padding: 4rem 0; background: linear-gradient(to bottom right, #0f172a, #1e293b, #0f172a);">
  <div class="hero-logo" style="margin-bottom: 2rem; animation: float 3s ease-in-out infinite;">
    <img src="/uph-logo.png" alt="UPH Logo" style="width: 120px; height: 120px; border-radius: 24px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);"/>
  </div>
  
  <div class="hero-badge" style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; background: rgba(37, 99, 235, 0.1); border: 1px solid rgba(37, 99, 235, 0.3); border-radius: 50px; color: #06b6d4; font-size: 0.875rem; font-weight: 500; margin-bottom: 1.5rem;">
    Version 2.7 Now Available
  </div>
  
  <h1 style="font-size: clamp(2.5rem, 5vw, 4rem); font-weight: 800; line-height: 1.1; margin-bottom: 1.5rem; background: linear-gradient(135deg, #ffffff 0%, #94a3b8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
    Unified Party Hub
  </h1>
  <p style="font-size: clamp(1.25rem, 3vw, 1.75rem); color: #94a3b8; margin-bottom: 1rem; font-weight: 300;">
    Master Data Management for ERPNext
  </p>
  <p style="font-size: 1.125rem; color: #64748b; max-width: 700px; margin: 0 auto 2.5rem;">
    Centralize your customer, supplier, and employee data with intelligent hierarchy management, multi-currency support, and enterprise-grade governance.
  </p>
  
  <div style="margin: 2rem 0; display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
    <a href="./docs/introduction/" style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 1rem 2rem; font-size: 1rem; font-weight: 600; border-radius: 12px; border: none; text-decoration: none; background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%); color: white; box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.4);">
      Get Started
    </a>
    <a href="./docs/features/" style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 1rem 2rem; font-size: 1rem; font-weight: 600; border-radius: 12px; border: 2px solid rgba(255, 255, 255, 0.2); text-decoration: none; background: transparent; color: white;">
      Documentation
    </a>
  </div>

  <!-- Stats -->
  <div style="display: flex; justify-content: center; gap: 3rem; flex-wrap: wrap; margin-top: 3rem;">
    <div style="text-align: center;">
      <div style="font-size: 2rem; font-weight: 700; color: white;">10K+</div>
      <div style="font-size: 0.875rem; color: #64748b;">Organizations</div>
    </div>
    <div style="text-align: center;">
      <div style="font-size: 2rem; font-weight: 700; color: white;">50M+</div>
      <div style="font-size: 0.875rem; color: #64748b;">Parties Managed</div>
    </div>
    <div style="text-align: center;">
      <div style="font-size: 2rem; font-weight: 700; color: white;">99.9%</div>
      <div style="font-size: 0.875rem; color: #64748b;">Uptime SLA</div>
    </div>
  </div>
</div>

<!-- Key Features Section -->
## 🚀 Powerful Features

Everything you need to master your party data in ERPNext

### 🌳 Tree Hierarchy

Organize parties in intelligent hierarchical structures with automatic parent-child relationships and cascading updates.

### 🔗 Multi-Role Linking

Link customers to suppliers, connect employees to multiple organizations, and manage complex relationship networks.

### 💱 Multi-Currency Support

Manage party balances and transactions across 150+ currencies with real-time exchange rates and hierarchical account mapping.

### 📊 Analytics & Reporting

Gain insights with built-in dashboards, financial reports, aging analysis, and customizable KPI widgets.

### 🛡️ Data Governance

Ensure data quality with validation rules, audit trails, compliance reporting, and role-based access controls.

### ⚡ SmartCache Performance

Experience lightning-fast performance with intelligent caching, background sync, and optimized database queries.

### 🔍 Duplicate Detection

Identify and merge duplicate parties using fuzzy matching algorithms, customizable rules, and batch processing.

### 🌍 Multi-Language Support

Full RTL support for Arabic and 20+ languages with translated interfaces, localized formats, and Unicode compliance.

---

## 💡 Why UPH?

Standard ERPNext has limitations. UPH solves them.

### ⚠️ Fragmented Identity

A single legal entity acting as both Customer and Supplier exists as two disconnected documents.

### 💱 Multi-Currency Complexity

Transacting in multiple currencies often requires duplicate party records (e.g., "Customer USD", "Customer EUR").

### 📊 Siloed Reporting

Financial reports are segmented by specific Party records, making 360-degree visibility difficult.

### 🔄 Data Redundancy

Address and Contact data must be duplicated across multiple party roles.

---

## 📦 Core DocTypes

Powerful data structures for comprehensive party management

### 🎯 Party Master

Central hub with tree-based hierarchy, multi-role support, and consolidated visibility.

### 📊 Party Analytic Accounting

Oracle TCA-like site accounting with multiple dimension types.

### 🔗 Party Master Parties

Junction table linking Party Master to Customers, Suppliers, Employees.

### ⚙️ Party Master Settings

Central configuration for rules, field mapping, and PAA settings.

### 🤝 Party Relationship

Define N-to-N relationships between parties with ownership tracking.

### 📋 Data Quality Dashboard

Real-time governance score, linkage stats, and duplicate detection.

---

## 📈 Reports

Comprehensive reporting for financial and operational insights

### 📊 Party Master Ledger

Consolidated ledger view across all linked parties with filters by Party Master, party type, company, and date range.

### 💰 Party Account Balances

Account balance reporting per party with receivable/payable balances, currency-wise breakdown, and aging analysis.

### 📋 Party Accounting Ledger

Detailed accounting transactions filtered by Party Master and accounting dimension with voucher-wise details.

### 🏥 Party Master Health Report

Data quality and governance reporting including linkage status, missing tax IDs, and data completeness metrics.

---

## 🎯 Use Cases

Real-world scenarios where UPH adds value

### 🏢 Conglomerates

Manage inter-company transactions where a subsidiary is both a vendor and a client. Consolidate reporting across entities while maintaining individual entity visibility.

### 🌍 Multi-National Trade

Handle single customers paying in multiple currencies without cluttering the Customer master. Automatic GL account resolution per currency.

### ✅ Governance Compliance

Enforce strict Tax ID validation and prevent duplicate customer creation across different sales teams. Real-time governance scoring.

### 🏭 Branch Accounting

Track financial performance by branch/site without creating separate Customer/Supplier records. Oracle TCA-like site accounting.

---

## 🚀 Get Started

Ready to transform your party data?

[Installation Guide →](./docs/introduction/installation.md)

[Quick Start →](./docs/introduction/quick-start.md)

[View Documentation →](./docs/features/)

---

## 📚 Documentation

- [Introduction](./docs/introduction/)
- [Key Features](./docs/features/)
- [Core DocTypes](./docs/features/core-doctypes/)
- [Reports](./docs/features/reports/)
- [Configuration](./docs/features/configuration/)
- [API Reference](./docs/Advanced/api-reference/)

---

## 🛠️ Resources

- [GitHub Repository](https://github.com/Sendipad/uph)
- [Report Issues](https://github.com/Sendipad/uph/issues)
- [ERPNext Community](https://discuss.erpnext.com)
- [Documentation](https://sendipad.github.io/uph/)
