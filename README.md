# 🚀 Unified Party Hub (UPH) for ERPNext

<div align="center">
  <a href="https://github.com/Sendipad/uph">
    <img src="https://github.com/user-attachments/assets/424defe6-b5cc-4f77-aa94-7d74c67ff7cc" alt="UPH Logo" height="100px" width="100px"/>
  </a>
  <h3>Master Data Management (MDM) for Frappe/ERPNext</h3>
  <p><b>Centralize. Unify. Govern.</b></p>

  [![Test v15](https://github.com/Sendipad/uph/actions/workflows/test_v15.yml/badge.svg)](https://github.com/Sendipad/uph/actions/workflows/test_v15.yml)
  [![Test Develop (v16)](https://github.com/Sendipad/uph/actions/workflows/test_develop.yml/badge.svg)](https://github.com/Sendipad/uph/actions/workflows/test_develop.yml)
  <br>
  <img src="https://img.shields.io/badge/Frappe%20%2F%20ERPNext-v15+-red?style=for-the-badge" alt="Supports ERPNext v15+"/>
  <img src="https://img.shields.io/badge/Version-v2.5.0-blue?style=for-the-badge" alt="Version 2.5.0"/>
  <img src="https://img.shields.io/badge/Localization-Arabic%20(100%25)-green?style=for-the-badge" alt="Arabic 100%"/>
  <br><br>

  <a href="#-the-problem">The Problem</a> •
  <a href="#-the-solution">The Solution</a> •
  <a href="#-key-features">Key Features</a> •
  <a href="#-business-impact">Impact</a> •
  <a href="#-installation">Installation</a>
</div>

---

## 🖼️ Visual Insights

<p align="center">
  <img src="screenshots/party_master_tree.png" alt="Party Master Tree Hierarchy" width="800" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
  <br>
  <i>Advanced Tree Hierarchy providing consolidated financial visibility at every node.</i>
</p>

---

## 🛑 The Problem: Fragmented Business Entities
Standard ERPNext treats **Customers**, **Suppliers**, and **Employees** as isolated data silos. For a business, this creates technical debt:
*   **Identity Fragmentation**: A single legal partner who is both a customer and a vendor ends up as two unconnected records.
*   **Opacity in Financials**: No out-of-the-box way to see the "Net Position" (AR - AP) of a complex partner.
*   **Broken Governance**: Managing head-offices with multiple branches or sub-dealers requires manual reconciliation.
*   **Multi-Currency Complexity**: Managing a single partner transacting in multiple currencies often requires creating duplicate "Parties" for each currency, leading to data mess and reporting nightmares.

---

## ✅ The Solution: Unified Party Hub (MDM)
UPH introduces a **Master Data Management (MDM)** layer to ERPNext. It decouples the **Legal Entity** (The Who) from the **Business Role** (The How).

### 🏢 One Identity, Infinite Currencies
The **Party Master** acts as the parent identity. You can link a single Party Master to multiple ERPNext roles (Customer, Supplier, etc.) across different companies and currencies.

**Hierarchical Account Resolution**: UPH intelligently resolves the correct Ledger Account during transactions by traversing the Party Master tree. This means you can have a single "Group Account" in the Party Master that dynamically selects the correct leaf account based on the transaction currency, eliminating the need for manual account selection or duplicate party records.

---

## ✨ Key Features

### 💎 Smart MDM Engine
*   **Unified Profile**: Centralized management of contact info, addresses, and custom attributes.
*   **Automatic Synchronization**: Changes in the Party Master propagate instantly to all linked entities (Customer/Supplier).
*   **Duplicate Governance**: Enforces unique business identities across the organization, preventing redundant data entry.

### 📊 Financial & Multi-Currency Intelligence
*   **Comprehensive Dashboards**: Real-time aggregation of Sales, Purchases, and Outstanding Balances with built-in data quality metrics (e.g., Missing Tax IDs).
*   **Currency Exposure Tracking**: Visualize your financial commitment across different currencies in a single donut chart.
*   **Recursive Tree Balances**: Instant calculation of total exposure for any node in the hierarchy, supporting multi-currency totals.

### ⚙️ Deep Integration
*   **Transaction Middleware**: Revolutionary hooks that automatically fetch and validate the Party Master on Sales Invoices, Payments, and Journal Entries.
*   **Automatic Enrichment**: Missing contact, address, or tax information in transactions is automatically pulled from the Golden Record in the Party Master.

---

## 🚀 Business Impact
*   **Seamless Multi-Currency**: Transact with the same partner in USD, EUR, and YER without ever changing the Party link.
*   **360° Financial View**: Net position reporting across Payables and Receivables, regardless of the role or currency.
*   **Enterprise Scaling**: Native support for complex hierarchical distribution and procurement networks with rigorous governance.
*   **Zero Core Hacks**: Implemented using standard Frappe hooks—safe for upgrades and cloud-ready.

---

## 💻 Installation

```bash
bench get-app uph https://github.com/Sendipad/uph
bench install-app uph
bench migrate
```

---

## 🎯 Target Use Cases
*   **International Trade**: Managing partners across borders with multiple currencies.
*   **Group Companies**: Managing subsidiaries and parent entities with complex ledger requirements.
*   **SME MDM**: Small businesses needing a clean, unified, and governed view of their business partners.

---

## 📜 License
Licensed under **GNU General Public License v3.0**.  
Created with ❤️ by the UPH Community.

---
<p align="center">
  <a href="https://github.com/Sendipad/uph/wiki">📚 Explore the Full Documentation</a>
</p>
