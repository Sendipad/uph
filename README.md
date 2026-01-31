# Unified Party Hub (UPH)

<div align="center">
  <a href="https://github.com/Sendipad/uph/wiki">
    <img src="https://github.com/user-attachments/assets/424defe6-b5cc-4f77-aa94-7d74c67ff7cc" alt="UPH Logo" height="80px" width="80px"/>
  </a>
  <p>A Foundational and Scalable Master Data Management Solution for ERPNext</p>

  <!-- Version/Compatibility Badge -->
  <img src="https://img.shields.io/badge/Frappe%20%2F%20ERPNext-v15+-red" alt="Supports ERPNext v15+"/>
  <img src="https://img.shields.io/badge/Version-v2.3.0-blue" alt="Version 2.3.0"/>
  <br>

  <!-- Action Badges -->
  <a href="https://github.com/Sendipad/uph#installation">
    <img src="https://img.shields.io/badge/Try%20It%20Now-Install-blue?style=for-the-badge&logo=github" alt="Try It Now"/>
  </a>
  &nbsp;
  <a href="https://github.com/Sendipad/uph/wiki">
    <img src="https://img.shields.io/badge/Documentation-Wiki-green?style=for-the-badge&logo=read-the-docs" alt="Documentation"/>
  </a>
</div>

---

## 🖼 Screenshots & Demo

<p align="center">
  <img src="screenshots/party_master_tree.png" alt="Party Master Tree Hierarchy" width="600"/>
</p>

---

## 🌟 Overview
UPH is a mission-critical Frappe application solving **Master Data Management (MDM) challenges** in ERPNext.  
It provides a **single source of truth** for all business entities (Customers, Suppliers, Employees, Shareholders), enabling multi-role management, consolidated reporting, and zero data duplication.

Built for **enterprise readiness** with support for complex organizational structures and multi-currency environments.

**Other Languages:**  
- [Arabic (العربية)](README.ar.md) 🇸🇦 (Full localization support)

---

## 🚀 What's New in v2.3.0
- **Hierarchical Financial Dashboard**: Automatic aggregation of Sales, Net Balances, and Unpaid Invoices for Group nodes in the Party Master tree.
- **Enhanced Party Workspace**: New real-time metrics (Number Cards) and quick-access shortcuts for critical reports.
- **Full Arabic Localization**: 100% translation coverage for a seamless Arabic user experience.
- **Performance Optimized**: Major architectural refactoring for faster balance calculations and tree rendering.

---

## ✅ Key Features

### 1. Unified Party Master (Tree Doctype)
- **Single Unified Doctype:** Controls creation, fetching, and linking of all related entities.  
- **Zero Duplication:** Intelligent de-duplication and mapping of party records.  
- **Tree Hierarchy:** Multi-level organizational grouping for accurate hierarchical reporting.

### 2. Dynamic Role & Integration Flexibility
- **Multi-Role Party:** Enable multiple roles (Customer, Supplier, etc.) for a single physical entity.
- **Flexible Integration:** Seamlessly works with standard ERPNext party types and custom doctypes.

### 3. Advanced Financial & Data Control
- **Consolidated Dashboard**: Real-time financial indicators aggregated across the hierarchy.
- **Multi-Currency Support**: Unified balance tracking across different currencies and companies.

---

## 🔧 Future Vision: Hub Module (Rule Engine)
The **Hub module** is a flexible rule engine providing:
- **Deduplication Enforcement**  
- **Integrity Validation**  
- **Dynamic Data Population**  
- **Custom Rule Services** for developers to create specialized business logic.

---

## 🚀 Usage

### Installation
```bash
bench get-app uph https://github.com/Sendipad/uph
bench install-app uph
```

### Quick Start
1. Navigate to **Unified Party Hub** → **Party Master**.
2. Define your organizational hierarchy (Group and Leaf nodes).
3. Link existing Customers/Suppliers or create new ones directly from the Party Master.
4. Monitor consolidated health and financial status via the **Party Workspace**.

---

## 📜 License
Licensed under GNU General Public License v3.0.
Free to use, extend, and contribute.
