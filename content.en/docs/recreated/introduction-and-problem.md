---
title: "Introduction and Problem Statement"
weight: 1
---

# Introduction

Unified Party Hub (UPH) is positioned as a master data management layer for ERPNext/Frappe deployments where one legal entity can appear in multiple operational roles (Customer, Supplier, Employee).

## What Problem UPH Solves

From repository source analysis, UPH addresses these operational gaps:

1. **Fragmented identity records** for the same legal entity across Customer/Supplier/Employee masters.
2. **Multi-currency duplication pressure**, where teams create multiple party records to map different account/currency needs.
3. **Weak relationship visibility** between parent companies, branches, and role variants.
4. **Data quality drift** due to duplicate entries and inconsistent naming.
5. **Reporting silos**, where financial views are split by party document type instead of legal entity.

## Core Concept

UPH introduces a unifying canonical record called **Party Master** and links role-specific ERPNext records into that canonical layer.

- Party Master becomes the legal-entity anchor.
- Role records remain usable (Customer/Supplier/Employee), but are normalized and linked.
- Reporting and accounting contexts can be consolidated at Party Master level.

## Intended Users

- Master data governance teams
- ERP administrators and implementation consultants
- Finance teams requiring party-level consolidated visibility
- Developers integrating party identity across custom DocTypes

## Documentation Scope

This recreated documentation is derived from:

- Hugo documentation source and page taxonomy
- Exposed API method paths listed in the repository
- Theme/layout and custom UI logic
- Feature declarations present in content and configuration files

