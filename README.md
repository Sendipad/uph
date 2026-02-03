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

  <a href="#problem-statement">The Problem</a> •
  <a href="#solution-overview">The Solution</a> •
  <a href="#key-features">Key Features</a> •
  <a href="#api--integrations">API</a> •
  <a href="#compatibility">Installation</a>
</div>

---

## 🖼️ Visual Insights

<p align="center">
  <img src="screenshots/party_master_tree.png" alt="Party Master Tree Hierarchy" width="800" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
  <br>
  <i>Advanced Tree Hierarchy providing consolidated financial visibility at every node.</i>
</p>

---

# Unified Party Hub (UPH)

**Unified Party Hub (UPH)** is an enterprise-grade Master Data Management (MDM) extension for ERPNext. It centralizes siloed business roles (Customers, Suppliers, Employees) into a unified, tree-based hierarchy, providing consolidated financial visibility and rigorous data governance across complex business ecosystems.

## Problem Statement

Standard ERPNext implementations often face challenges when managing complex business entities:

*   **Fragmented Identity**: A single legal entity acting as both a Customer and a Supplier exists as two disconnected documents.
*   **Multi-Currency Logic**: Transacting with the same party in multiple currencies often requires creating duplicate party records (e.g., "Customer USD", "Customer EUR") to map to specific Receivable/Payable accounts.
*   **Siloed Reporting**: Financial reports (General Ledger, Aging) are segmented by the specific Party record, making it difficult to get a 360-degree view of the legal entity's total exposure.
*   **Data Redundancy**: Address and Contact data must be duplicated across multiple party roles.

## Solution Overview

UPH introduces the **Party Master**, a central governance layer that sits above standard ERPNext Party types. By treating the "Party" as a single legal entity and "Roles" (Customer, Supplier) as attributes, UPH delivers:

*   **True Multi-Currency Support**: Transact in any currency with a single Party entity using hierarchical account mapping.
*   **Unified Analytic Accounting**: Similar to **Oracle TCA Sites**, this feature allows a single party to have multiple dimensions (sites/branches), each with its own independent financial reporting. It tags every transaction (`Party Analytic Accounting` dimension), enabling you to generate a P&L or Balance Sheet for a specific branch or site of a customer/supplier without cluttering the chart of accounts.
*   **360-Degree Visibility**: A consolidated dashboard showing total sales, purchases, and outstanding balances across the entire hierarchy.

## Core Concepts

### 1. Party Master
The **Party Master** is the single source of truth for a legal entity. It supports a tree-based structure to model complex hierarchies (e.g., Holding Company -> Regional Office -> Local Branch).

### 2. Party Roles
Existing ERPNext records (Customers, Suppliers, Employees) are linked to a Party Master as **Roles**. A single Party Master can have multiple roles (e.g., being both a Customer and a Supplier).

### 3. Party Analytic Accounting
A separate, immutable accounting dimension (`Party Analytic Accounting`) is automatically tagged on every financial transaction. This allows for party-level financial reporting independent of the specific "Customer" or "Supplier" document used in the voucher.

## Key Features

### 🛡️ Party Identity Governance
A dedicated dashboard provides real-time insights into data quality and completeness:
*   **Governance Score**: Tracks the percentage of parties with valid Tax IDs and proper linkage.
*   **Linkage Stats**: Visualizes the ratio of Linked vs. Unlinked parties.
*   **Duplicate Detection**: Smart algorithms check for existing parties using text normalization to prevent duplicate entry of names or tax IDs.

### 💱 Hierarchical Multi-Currency Support
UPH solves the remote multi-currency problem through intelligent GL account resolution:
*   Define a **Group Account** at the Party Master level.
*   The system automatically traverses the hierarchy to find the specific **Leaf Account** matching the transaction currency.
*   **Result**: Maintain a single "Customer" record but transact in USD, EUR, and GBP with correct GL mapping.

### ⚡ High-Performance Architecture
*   **SmartCache**: A robust caching layer (Redis) ensures instant retrieval of party details and configuration, even with millions of records.
*   **Batched Processing**: Dashboard statistics and validation rules use optimized SQL queries to prevent N+1 performance issues.

### 🧠 Intelligent Search & Onboarding
*   **Smart Link Fields**: Dropdowns for Party Master are usage-ranked. The parties you transact with most frequently appear at the top.
*   **Assisted Onboarding**: Bulk tools and "Create Party As" dialogs streamline the creation of new parties, automatically inheriting address and contact data from the master.

## API & Integrations

UPH exposes key methods for external integrations and data validation:

### Party Management
*   **`uph.party.controllers.party.get_party_details`**: Overrides standard ERPNext logic to inject Party Master data (Addresses, Contacts) into transactions.
*   **`uph.party.controllers.queries.party_master_link_query`**: Optimized link query with usage-based ranking for fast selection.

### Data Quality & MDM
*   **`uph.party.controllers.mdm.normalize_text(text)`**: A utility to normalize text for fuzzy matching (removes diacritics, unifies characters) - useful for custom dedup logic.
*   **`uph.party.controllers.mdm.validate_document_quality(doc)`**: Runs configured "Data Quality Rules" against a document to detect duplicates using fuzzy logic (RapidFuzz).
*   **`uph.party.controllers.party.check_duplicate_voucher_party_master`**: Validates if a voucher is being created for a Party Master that already has a similar transaction.

## Architecture

UPH is built as a non-intrusive extension to ERPNext:

*   **Hooks & Events**: Intercepts `validate`, `on_update`, and `on_trash` events to ensure data integrity without modifying core code.
*   **API Overrides**: Extends `erpnext.accounts.party.get_party_details` to inject Party Master data (Addresses, Contacts, Accounts) into transactions dynamically.
*   **Scalability**: Designed for high-volume environments, utilizing `frappe.qb` (Query Builder) for efficient database operations.

## Compatibility

*   **Framework**: Frappe Framework v15+
*   **ERP**: ERPNext v15+
*   **Database**: MariaDB / PostgreSQL

## Use Cases

1.  **Conglomerates**: Manage inter-company transactions where a subsidiary is both a vendor and a client.
2.  **Multi-National Trade**: Handle single customers paying in multiple currencies without cluttering the Customer master.
3.  **Governance Compliance**: Enforce strict Tax ID validation and prevent duplicate customer creation across different sales teams.

---
