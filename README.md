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
  <img src="https://img.shields.io/badge/Version-v2.4.0-blue?style=for-the-badge" alt="Version 2.4.0"/>
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
*   **Duplicate Overhead**: Managing the same address, contact, and tax info across multiple roles.

---

## ✅ The Solution: Unified Party Hub (MDM)
UPH introduces a **Master Data Management (MDM)** layer to ERPNext. It decouples the **Legal Entity** (The Who) from the **Business Role** (The How).

### 🏢 One Identity, Multiple Roles
The **Party Master** acts as the parent identity. You link a single Party Master to multiple ERPNext roles (Customer, Supplier, etc.), ensuring data consistency and cross-role visibility.

### 🌳 Hierarchical Governance
Organize your business ecosystem into a deep tree structure. Whether it's a conglomerate with 50 subsidiaries or a retailer with 500 branches, UPH provides a native tree-based management system.

---

## ✨ Key Features

### 💎 Smart MDM Engine
*   **Unified Profile**: Centralized management of contact info, addresses, and custom attributes.
*   **Automatic Synchronization**: Changes in the Party Master propagate instantly to all linked entities (Customer/Supplier).
*   **Fuzzy Search & Linking**: Intelligent discovery logic to identify and link existing ERPNext records to new Master entities.

### 📊 Financial Intelligence
*   **Consolidated Dashboards**: Real-time aggregation of Sales, Purchases, and Outstanding Balances across all linked roles.
*   **Recursive Tree Balances**: Instant calculation of total exposure for any node in the hierarchy.
*   **Multi-Currency Native**: Handles complex cross-currency transactions within a single partner view.

### ⚙️ Deep Integration
*   **Transaction Middleware**: Revolutionary hooks that automatically fetch and validate the Party Master on Sales Invoices, Payments, and Journal Entries.
*   **Customizable Mapping**: A flexible settings engine allows you to define exactly which fields sync between the Hub and standard DocTypes.

---

## 🚀 Business Impact
*   **360° Financial View**: Net position reporting across Payables and Receivables.
*   **Clean Data Ecosystem**: Zero duplicates; 100% data integrity.
*   **Enterprise Scaling**: Native support for complex hierarchical distribution and procurement networks.
*   **Zero Core Hacks**: Implemented using standard Frappe hooks—safe for upgrades.

---

## 💻 Installation

```bash
bench get-app uph https://github.com/Sendipad/uph
bench install-app uph
bench migrate
```

---

## 🎯 Target Use Cases
*   **Group Companies**: Managing subsidiaries and parent entities.
*   **B2B2C Networks**: Manufacturers managing distributors and retailers.
*   **SME MDM**: Small businesses needing a clean, unified view of their business partners.

---

## 📜 License
Licensed under **GNU General Public License v3.0**.  
Created with ❤️ by the UPH Community.

---
<p align="center">
  <a href="https://github.com/Sendipad/uph/wiki">📚 Explore the Full Documentation</a>
</p>
