---
title: "Key Features"
weight: 2
---

# Key Features

Unified Party Hub (UPH) provides a comprehensive set of features for Master Data Management in ERPNext.

---

## Core Features

### 🛡️ Party Identity Governance

A dedicated dashboard provides real-time insights into data quality and completeness:

- **Governance Score**: Tracks the percentage of parties with valid Tax IDs and proper linkage
- **Linkage Stats**: Visualizes the ratio of Linked vs. Unlinked parties
- **Duplicate Detection**: Smart algorithms check for existing parties using text normalization to prevent duplicate entry

[Learn more about Data Quality Dashboard →](./data-quality-dashboard.md)

### 🚀 Production-Ready Onboarding

Designed for heavy production systems with thousands of records:

- **Smart Linking Dialog**: Detects unlinked ERPNext parties and offers one-click bulk association
- **Create Party As**: A wizard to instantly provision a new Role (e.g., create a Supplier from an existing Customer), automatically inheriting address, contact, and tax data

### 💱 Hierarchical Multi-Currency Support

UPH solves the multi-currency problem through intelligent GL account resolution:

- Define a **Group Account** at the Party Master level
- The system automatically traverses the hierarchy to find the specific **Leaf Account** matching the transaction currency
- Result: Maintain a single "Customer" record but transact in USD, EUR, and GBP with correct GL mapping

### ⚡ High-Performance Architecture

- **SmartCache**: A robust caching layer (Redis) ensures instant retrieval of party details and configuration
- **Batched Processing**: Dashboard statistics and validation rules use optimized SQL queries
- **Query Builder**: Utilizes `frappe.qb` for efficient database operations

### 📊 Party Analytic Accounting

A separate, immutable accounting dimension (`Party Analytic Accounting`) is automatically tagged on every financial transaction:

- Enables party-level financial reporting independent of the specific "Customer" or "Supplier" document
- Generate a P&L or Balance Sheet for a specific branch or site of a customer/supplier
- Similar to **Oracle TCA Sites**

### 🌳 Tree-Based Hierarchy

Party Master supports tree-based hierarchy:

- Model complex organizational structures (Holding Company → Regional Office → Local Branch)
- View consolidated balances at any level of the tree
- Hierarchical numbering system for organized growth

---

## Advanced Features

### 🔗 Relationship Management

Map complex N-to-N relationships:

- Define Parent/Subsidiary structures
- Ownership percentages and validity dates
- Relationship Engine for advanced party connections

[Learn more about Relationship Management →](./relationship-management.md)

### 📋 Configuration

Highly customizable through **Party Master Settings**:

- Dynamically inject `party_master` field into any DocType
- Configure uniqueness rules per party type
- Set validation rules and mandatory fields
- Field synchronization between Party Master and linked parties

[Learn more about Configuration →](./configuration.md)

---

## Documentation Reference

### Core DocTypes

Comprehensive reference for all DocTypes introduced by UPH:

- **Party Master**: Central hub with tree-based hierarchy
- **Party Analytic Accounting**: Oracle TCA-like site accounting
- **Party Master Parties**: Junction table linking to ERPNext parties
- **Party Master Settings**: Central configuration
- **Party Relationship**: N-to-N relationship definitions
- **Duplicate Exclusion**: Rules for excluding duplicates

[Explore Core DocTypes →](./core-doctypes.md)

### Reports

Detailed documentation for all UPH reports:

- **Party Master Ledger**: Consolidated ledger view
- **Party Account Balances**: Balance reporting with aging
- **Party Accounting Ledger**: Detailed transactions
- **Party Master Health Report**: Data quality metrics
- **Chronological Party Ledger**: Time-based history

[Explore Reports →](./reports.md)

---

## Feature Overview

### Quick Feature Comparison

| Feature | Description | Benefit |
|---------|-------------|---------|
| Tree Hierarchy | Parent-child party relationships | Organizational structure modeling |
| Multi-Role Linking | Link Customer + Supplier + Employee | Single source of truth |
| Multi-Currency | 150+ currency support | No duplicate party records |
| PAA | Party Analytic Accounting | Branch-level reporting |
| Duplicate Detection | Fuzzy matching algorithms | Data quality assurance |
| SmartCache | Redis + request caching | High performance |
| Relationship Engine | N-to-N relationships | Complex corporate structures |
| Governance Dashboard | Real-time scoring | Compliance monitoring |

---

## Related Documentation

- [Data Quality Dashboard](data-quality-dashboard.md)
- [Configuration](configuration.md)
- [Hierarchical Numbering](hierarchical-numbering.md)
- [Relationship Management](relationship-management.md)
- [Core DocTypes](core-doctypes.md)
- [Reports](reports.md)
