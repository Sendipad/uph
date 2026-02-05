---
title: "Introduction"
weight: 1
---

# Unified Party Hub (UPH)

**Enterprise-Grade Master Data Management (MDM) for ERPNext**

Unified Party Hub (UPH) is a comprehensive Master Data Management (MDM) extension for ERPNext that centralizes siloed business roles (Customers, Suppliers, Employees) into a unified, tree-based hierarchy. It provides consolidated financial visibility and rigorous data governance across complex business ecosystems.

## The Problem

Standard ERPNext implementations often face challenges when managing complex business entities:

*   **Fragmented Identity**: A single legal entity acting as both a Customer and a Supplier exists as two disconnected documents.
*   **Multi-Currency Logic**: Transacting with the same party in multiple currencies often requires creating duplicate party records (e.g., "Customer USD", "Customer EUR") to map to specific Receivable/Payable accounts.
*   **Siloed Reporting**: Financial reports (General Ledger, Aging) are segmented by the specific Party record, making it difficult to get a 360-degree view of the legal entity's total exposure.
*   **Data Redundancy**: Address and Contact data must be duplicated across multiple party roles.

## The Solution

UPH introduces the **Party Master**, a central governance layer that sits above standard ERPNext Party types. By treating the "Party" as a single legal entity and "Roles" (Customer, Supplier) as attributes, UPH delivers:

*   **True Multi-Currency Support**: Transact in any currency with a single Party entity using hierarchical account mapping.
*   **Unified Analytic Accounting**: Similar to **Oracle TCA Sites**, this feature allows a single party to have multiple dimensions (sites/branches), each with its own independent financial reporting. It tags every transaction with `Party Analytic Accounting`, enabling you to generate a P&L or Balance Sheet for a specific branch or site without cluttering the chart of accounts.
*   **360-Degree Visibility**: A consolidated dashboard showing total sales, purchases, and outstanding balances across the entire hierarchy.

## Core Concepts

### 1. Party Master
The **Party Master** is the single source of truth for a legal entity. It supports a tree-based structure to model complex hierarchies (e.g., Holding Company -> Regional Office -> Local Branch). It maintains the "Single Version of Truth" for shared data like Address, Contacts, and Legal Identity.

### 2. Linking & Roles
UPH does not replace ERPNext Party documents; it connects them.
*   **Link Injection**: UPH dynamically injects a `party_master` field into standard DocTypes (Customer, Supplier, Employee) via **Party Master Settings**.
*   **Uniqueness Rules**: Settings can enforce strict rules, such as allowing multiple "Customer" records for one Party Master only if they have different **Currencies**.
*   **Role Management**: A Party Master declares its roles (e.g., Primary Role: Customer, Secondary Role: Supplier). The system then facilitates creating or linking the corresponding ERPNext records.

### 3. Party Analytic Accounting
A separate, immutable accounting dimension (`Party Analytic Accounting`) is automatically tagged on every financial transaction. This allows for party-level financial reporting independent of the specific "Customer" or "Supplier" document used in the voucher.

## Architecture

UPH is built as a non-intrusive extension to ERPNext:

{{< mermaid >}}
graph TD
    PM[Party Master] -->|Link| C[Customer]
    PM -->|Link| S[Supplier]
    PM -->|Link| E[Employee]
    
    PM -->|Parent| PM_Group[Party Group]
    
    subgraph "Financials"
    C -.->|GL Entry| GL[General Ledger]
    S -.->|GL Entry| GL
    GL -->|Consolidated| PM_Report[Party Account Statement]
    end
    
    subgraph "Data Quality"
    DQ[Data Quality Dashboard] -->|Detects| Duplicates[Potential Duplicates]
    DQ -->|Merges| Merge[Merge Parties]
    DQ -->|Dismisses| Exclude[Duplicate Exclusion]
    end
    
    subgraph "Performance"
    Cache[SmartCache] -->|Redis| Fast[Millisecond Retrieval]
    Cache -->|Local| Request[Request Scope]
    end
{{< /mermaid >}}

### Key Architectural Features:
- **Hooks & Events**: Intercepts `validate`, `on_update`, and `on_trash` events to ensure data integrity without modifying core code.
- **Dynamically Injected Fields**: Uses `Party Master Settings` to inject Link fields into target DocTypes without permanent schema modifications.
- **Scalability**: Designed for high-volume environments, utilizing `frappe.qb` (Query Builder) for efficient database operations.
- **Caching System**: SmartCache combines local (request scope) and Redis (shared scope) caching for performance.
