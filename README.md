# 🚀 Unified Party Hub (UPH) for ERPNext

<div align="center">
  <a href="https://github.com/Sendipad/uph">
    <img src="https://github.com/user-attachments/assets/424defe6-b5cc-4f77-aa94-7d74c67ff7cc" alt="UPH Logo" height="100px" width="100px"/>
  </a>
  <h3>Master Data Management (MDM) Reimagined for Frappe/ERPNext</h3>
  <p><b>Break the Silos. Unify your Business.</b></p>

  <img src="https://img.shields.io/badge/Frappe%20%2F%20ERPNext-v15+-red?style=for-the-badge" alt="Supports ERPNext v15+"/>
  <img src="https://img.shields.io/badge/Version-v2.3.0-blue?style=for-the-badge" alt="Version 2.3.0"/>
  <img src="https://img.shields.io/badge/Localization-Arabic%20(100%25)-green?style=for-the-badge" alt="Arabic 100%"/>
  <br><br>

  <a href="#-the-challenge">The Challenge</a> •
  <a href="#-the-solution">The Solution</a> •
  <a href="#-key-features">Features</a> •
  <a href="#-whats-new-in-v230">What's New</a> •
  <a href="#-installation">Installation</a>
</div>

---

## 🖼️ Visual Insights

<p align="center">
  <img src="screenshots/party_master_tree.png" alt="Party Master Tree Hierarchy" width="800" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
  <br>
  <i>Advanced Tree Hierarchy providing real-time financial visibility at every level.</i>
</p>

---

## 🛑 The Challenge: Siloed Master Data
In standard ERPNext, **Customers**, **Suppliers**, and **Employees** are isolated entities. This architectural silo leads to:
*   **Data Fragmentation**: One physical entity (a partner who is both customer and supplier) results in multiple unlinked records.
*   **Reporting Nightmares**: Difficult to get a 360-degree financial view of a person or company.
*   **Duplicate Data**: Inconsistent addresses, contacts, and tax IDs across different roles.
*   **Lack of Governance**: No native support for complex parent-subsidiary or head-office-branch (TCA Site) structures.

---

## ✅ The Solution: Unified Party Hub
UPH introduces a **Master Data Management (MDM)** layer that decouples the **Legal Entity** from the **Business Role**. It acts as the "Single Source of Truth" for your entire business ecosystem.

### 🏢 One Master, Infinite Roles
Define a legal entity once in the **Party Master** and assign it multiple roles (Customer, Supplier, Shareholder, etc.) without duplicating data.

### 🌳 Hierarchical Governance
Organize your parties into deep tree structures. Manage global conglomerates, regional branches, or departmental groups with ease.

---

## ✨ Key Features

### 💎 Unified Master (Tree-Based)
*   **Hierarchical Numbering**: Automatic, structured ID generation based on parent nodes.
*   **Tree Balances**: Real-time financial balances aggregated across the hierarchy.
*   **Smart Discovery**: Normalization-based fuzzy matching to identify and link existing records.

### 📊 Advanced Financial Dashboards
*   **Recursive Calculation**: Group nodes automatically aggregate Sales, Purchases, and Net Payables/Receivables from all children.
*   **Multi-Currency Engine**: Consolidated reporting across different currencies and companies.
*   **Health Audits**: Built-in reports to identify unlinked or inconsistent party data.

### 🛠️ Integration Layer
*   **Dynamic Mapping**: UPH injects itself into standard ERPNext transactions with zero core code modification.
*   **Auto-Sync**: Changes to the Hub automatically synchronize with linked Customer/Supplier records.
*   **Transactional Integrity**: Hard validation prevents role/dimension mismatches in Sales and Purchase cycles.

### 🇸🇦 Full Arabic Localization
Native, 100% complete translation for Arabic, including RTL-optimized UI and localized error handling.

---

## 🚀 What's New in v2.3.0
*   **Hierarchical KPIs**: Major upgrade to the Dashboard allowing Group nodes to show aggregated financial performance.
*   **Enhanced Workspace**: Modernized Desk UI with Number Cards for real-time monitoring of Linked vs. Unlinked parties.
*   **Performance Overhaul**: Refactored caching and query logic for sub-second balance calculations on large datasets.
*   **Restored MDM Rules**: Re-implemented and hardened the Duplicate Detection and Field Mapping engines.

---

## 💻 Installation

```bash
bench get-app uph https://github.com/Sendipad/uph
bench install-app uph
bench migrate
```

---

## 🎯 Target Use Cases
*   **Enterprise MDM**: Centralizing data across multiple business units.
*   **B2B2C Management**: Managing partners who act as both vendors and distributors.
*   **Financial Consolidation**: Getting accurate exposure reports for group companies.
*   **Segmented Reporting**: Using Analytical Accounting (PAA) to track branch-level performance without record bloating.

---

## 📜 License
Licensed under **GNU General Public License v3.0**.  
Free to use, extend, and contribute. Created with ❤️ by the UPH Community.

---
<p align="center">
  <a href="https://github.com/Sendipad/uph/wiki">📚 Read the Full Documentation on Wiki</a>
</p>
