---
title: "Key Features"
weight: 2
---

# Key Features

Unified Party Hub (UPH) provides a comprehensive set of features for Master Data Management in ERPNext.

## Core Features

### 🛡️ Party Identity Governance
A dedicated dashboard provides real-time insights into data quality and completeness:
- **Governance Score**: Tracks the percentage of parties with valid Tax IDs and proper linkage.
- **Linkage Stats**: Visualizes the ratio of Linked vs. Unlinked parties.
- **Duplicate Detection**: Smart algorithms check for existing parties using text normalization to prevent duplicate entry.

### 🚀 Production-Ready Onboarding
Designed for heavy production systems with thousands of records:
- **Smart Linking Dialog**: Detects unlinked ERPNext parties and offers one-click bulk association.
- **Create Party As**: A wizard to instantly provision a new Role (e.g., create a Supplier from an existing Customer), automatically inheriting address, contact, and tax data.

### 💱 Hierarchical Multi-Currency Support
UPH solves the remote multi-currency problem through intelligent GL account resolution:
- Define a **Group Account** at the Party Master level.
- The system automatically traverses the hierarchy to find the specific **Leaf Account** matching the transaction currency.
- Result: Maintain a single "Customer" record but transact in USD, EUR, and GBP with correct GL mapping.

### ⚡ High-Performance Architecture
- **SmartCache**: A robust caching layer (Redis) ensures instant retrieval of party details and configuration.
- **Batched Processing**: Dashboard statistics and validation rules use optimized SQL queries.
- **Query Builder**: Utilizes `frappe.qb` for efficient database operations.

### 📊 Party Analytic Accounting
A separate, immutable accounting dimension (`Party Analytic Accounting`) is automatically tagged on every financial transaction:
- Enables party-level financial reporting independent of the specific "Customer" or "Supplier" document.
- Generate a P&L or Balance Sheet for a specific branch or site of a customer/supplier.
- Similar to **Oracle TCA Sites**.

### 🌳 Tree-Based Hierarchy
Party Master supports tree-based hierarchy:
- Model complex organizational structures (Holding Company → Regional Office → Local Branch).
- View consolidated balances at any level of the tree.
- Hierarchical numbering system for organized growth.

## Advanced Features

### 🔗 Relationship Management
Map complex N-to-N relationships:
- Define Parent/Subsidiary structures.
- Ownership percentages and validity dates.
- Relationship Engine for advanced party connections.

### 📋 Configuration
Highly customizable through **Party Master Settings**:
- Dynamically inject `party_master` field into any DocType.
- Configure uniqueness rules per party type.
- Set validation rules and mandatory fields.

---

## Related Documentation

- [Data Quality Dashboard](data-quality-dashboard.md)
- [Configuration](configuration.md)
- [Hierarchical Numbering](hierarchical-numbering.md)
- [Relationship Management](relationship-management.md)
