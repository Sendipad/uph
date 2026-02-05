---
title: "Introduction"
weight: 1
---

# Unified Party Hub (UPH)

**One Legal Entity – One Master Record.**

ERPNext historically separates Customers, Suppliers, Employees, and Shareholders into distinct silos. This leads to duplicate data handling, fragmented financial reporting, and complex reconciliation. 

**Unified Party Hub resolves this by introducing the `Party Master`**, a single source of truth for every legal entity you interact with.

## Core Philosophy

1.  **Identity First, Role Second**: A person is created once as a `Party Master`. They can then be linked to a Customer role, a Supplier role, or both.
2.  **Unified Ledger**: View financial standing across all roles. If a Supplier is also a Customer, net off their balances instantly.
3.  **Clean Data**: Strict validation and duplicate detection prevent database pollution.

## Architecture

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
{{< /mermaid >}}
