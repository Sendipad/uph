# 🚀 Unified Party Hub (UPH) for ERPNext

<div align="center">
  <a href="https://github.com/Sendipad/uph">
    <img src="https://github.com/user-attachments/assets/424defe6-b5cc-4f77-aa94-7d74c67ff7cc" alt="UPH Logo" height="100px" width="100px"/>
  </a>
  <h3>Master Data Management (MDM) Reimagined for Frappe/ERPNext</h3>
  <p><b>Break the Silos. Unify your Business.</b></p>

  [![Test v15](https://github.com/Sendipad/uph/actions/workflows/test_v15.yml/badge.svg)](https://github.com/Sendipad/uph/actions/workflows/test_v15.yml)
  [![Test Develop (v16)](https://github.com/Sendipad/uph/actions/workflows/test_develop.yml/badge.svg)](https://github.com/Sendipad/uph/actions/workflows/test_develop.yml)
  <br>
  <img src="https://img.shields.io/badge/Frappe%20%2F%20ERPNext-v15+-red?style=for-the-badge" alt="Supports ERPNext v15+"/>
  <img src="https://img.shields.io/badge/Version-v2.3.0-blue?style=for-the-badge" alt="Version 2.3.0"/>
  <img src="https://img.shields.io/badge/Localization-Arabic%20(100%25)-green?style=for-the-badge" alt="Arabic 100%"/>
  <br><br>

  <a href="#-the-challenge">The Challenge</a> •
  <a href="#-the-solution">The Solution</a> •
  <a href="#-key-features">Features</a> •
  <a href="#-app-structure">Structure</a> •
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
*   **Lack of Governance**: No native support for complex parent-subsidiary or head-office-branch structures.

---

## ✅ The Solution: Unified Party Hub
UPH introduces a **Master Data Management (MDM)** layer that decouples the **Legal Entity** from the **Business Role**. It acts as the "Single Source of Truth" for your entire business ecosystem.

### 🏢 One Master, Infinite Roles
Define a legal entity once in the **Party Master** and assign it multiple roles (Customer, Supplier, etc.) without duplicating data.

### 🌳 Hierarchical Governance
Organize your parties into deep tree structures. Manage global conglomerates, regional branches, or departmental groups with ease.

---

## 🏗️ App Structure & Integration

UPH is designed as a **Seamless Middleware** for ERPNext:

1.  **MDM Core**: The `Party Master` DocType serves as the central hub for all legal entities.
2.  **Linking Logic**: A robust set of controllers (`uph.party.controllers`) handles the mapping between the Hub and standard ERPNext DocTypes.
3.  **Real-time Synchronization**: Uses Frappe hooks to ensure that data modified in UPH propagates instantly to all linked roles.
4.  **Balance Aggregation Engine**: A high-performance recursive query system that calculates live balances across complex tree structures.
5.  **Validation Middleware**: Hardened validation rules that prevent transactional errors by ensuring the correct Party Master is used for linked parties.

---

## � Value to ERPNext Users
*   **360° Financial Visibility**: Instantly see the net position (Payables - Receivables) for any partner acting in multiple roles.
*   **Zero Core Modification**: Benefit from advanced MDM features without changing a single line of standard ERPNext code.
*   **Group Consolidation**: Roll up financial data from multiple sub-companies or branches into a single parent entity view.
*   **Clean Data Ecosystem**: Eliminate duplicates and inconsistent contact/address data across your business.

---

## ✨ Key Features

### 💎 Unified Master (Tree-Based)
*   **Hierarchical Numbering**: Automatic, structured ID generation based on parent nodes.
*   **Tree Balances**: Real-time financial balances aggregated across the hierarchy.
*   **Smart Discovery**: Normalization-based fuzzy matching to identify and link existing records.

### 📊 Advanced Financial Dashboards
*   **Recursive Calculation**: Group nodes automatically aggregate Sales, Purchases, and Net Payables/Receivables.
*   **Multi-Currency Engine**: Consolidated reporting across different currencies and companies.
*   **Health Audits**: Built-in reports to identify unlinked or inconsistent party data.

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

---

## 📜 License
Licensed under **GNU General Public License v3.0**.  
Free to use, extend, and contribute. Created with ❤️ by the UPH Community.

---
<p align="center">
  <a href="https://github.com/Sendipad/uph/wiki">📚 Read the Full Documentation on Wiki</a>
</p>
