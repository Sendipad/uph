<div align="center">
  <a href="https://github.com/Sendipad/uph/wiki">
    <img src="https://github.com/user-attachments/assets/424defe6-b5cc-4f77-aa94-7d74c67ff7cc" alt="UPH Logo By Abdo" height="80px" width="80px"/>
  </a>
  <h1>Unified Party Hub (UPH)</h1>
  <p><strong>A Foundational and Scalable Master Data Management Solution for ERPNext</strong></p>

  <!-- Badges -->
  <p>
    ![Frappe v15+](https://img.shields.io/badge/Frappe-v15+-blue)
    ![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue)
    ![GitHub issues](https://img.shields.io/github/issues/Sendipad/uph)
    ![GitHub stars](https://img.shields.io/github/stars/Sendipad/uph)
  </p>
</div>

---

## 🖼 Screenshots & Demo

<p align="center">
  <img src="screenshots/party_master_tree.png" alt="Party Master Tree" width="600"/>
</p>

<p align="center">
  <img src="screenshots/link_party_roles.gif" alt="Link Party Roles Demo" width="600"/>
</p>

---

## 🌟 Overview
UPH is a mission-critical Frappe application solving **Master Data Management (MDM) challenges** in ERPNext.  
It provides a **single source of truth** for all business entities (Customers, Suppliers, Employees, Shareholders), enabling multi-role management, consolidated reporting, and zero data duplication.  

> Built on Frappe (Python, JavaScript, Vue) for extensibility and enterprise readiness.

**Other Languages:**  
- [Arabic (العربية)](README.ar.md) 🇸🇦

---

## 💡 The Problem UPH Solves
Standard ERPNext treats Customers, Suppliers, and Employees as separate entities, which causes:
- **Data Duplication:** Entities with multiple roles require separate records.  
- **Consolidation Complexity:** No unified multi-currency reporting per entity.  
- **Lack of Hierarchy:** No native parent-subsidiary or organizational grouping.  
- **Limited Flexibility:** Extending party roles for vertical domains (Schools, Healthcare) is cumbersome.

---

## ✅ Key Features

### 1. Unified Party Master (Tree Doctype)
- **Single Unified Doctype:** Controls creation, fetching, and linking of all related entities.  
- **Zero Duplication:** Minimizes duplicate party records and transactional mistakes.  
- **Tree Hierarchy:** Multi-level structure for reporting by party type, business type, or corporate structure.  

### 2. Dynamic Role & Integration Flexibility
- **Multi-Role Party:** Assign multiple roles to a single Party Master (Customer, Supplier, Shareholder).  
- **Flexible Integration:** Works with standard and custom ERPNext party types.  
- **Easy UI/Migration:** Backend queries allow linking thousands of existing unlinked records seamlessly.  

### 3. Advanced Financial & Data Control
- **Multi-Currency Support:** Consolidated reporting and balance tracking per Party Master entity.  
- **Centralized Control:** Configure all relationships, settings, and data in one place.  
- **Extensible Foundation:** Future modules can extend capabilities, e.g., the Hub module.

---

## 🔧 Future Module: Hub (Rule System)
The **Hub module** is currently under development as a **flexible rule engine** for ERPNext.  
It provides essential automation and system services, including:

- **Deduplication:** Automatically prevent duplicate entries.  
- **Dynamic Text Generation:** Populate fields based on configurable rules.  
- **Integrity Validation:** Ensure data consistency across the system.  
- **Custom Rule Services:** Developers can easily define their own rule types for specialized workflows.  

> This module extends UPH’s capabilities, enabling advanced automation and control over party management and other business processes.

---

## 🚀 Usage

### Installation
```bash
bench get-app unified_party_hub https://github.com/Sendipad/uph
bench install-app uph
```
Next Steps

1. Navigate: Unified Party Hub → Party Master in ERPNext v15+.


2. Define your Party Master hierarchy.


3. Link existing Customers/Suppliers/Employees or create new linked doctypes from Party Master.


4. Explore reports, multi-currency tracking, and hierarchical analytics.




---

🎯 Call to Action

UPH is more than a feature—it’s a fundamental architectural improvement.

We urge the ERPNext developer team to consider integrating key UPH modules into the standard codebase. Benefits include:

Native support for multi-role entities.

Consolidated reporting with multi-currency and hierarchical tracking.

Elimination of duplicate party records, improving data integrity.

Enhanced ERPNext enterprise MDM capabilities.


We welcome feedback and collaboration to align UPH with ERPNext core standards.


---

💼 Use Cases

Group-level financial consolidation.

Hierarchical sales and procurement reporting.

Mapping business unit, employee, and shareholder relationships.

Departmental or regional party organization.



---

📜 License

Licensed under GNU General Public License v3.0.
Free to use, extend, and contribute.


---

🚀 Try it Now

UPH supports Frappe / ERPNext v15+.

<p align="center">
  <a href="https://github.com/Sendipad/uph#installation">
    <img src="https://img.shields.io/badge/Try%20It%20Now-Install-blue?style=for-the-badge&logo=github" alt="Try It Now"/>
  </a>
  &nbsp;
  <a href="https://github.com/Sendipad/uph/wiki">
    <img src="https://img.shields.io/badge/Documentation-Wiki-green?style=for-the-badge&logo=read-the-docs" alt="Documentation"/>
  </a>
</p>
```
