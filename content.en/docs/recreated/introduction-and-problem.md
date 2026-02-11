---
title: "Introduction and Problem Space"
weight: 1
---

# Introduction

**Unified Party Hub (UPH)** is a Frappe/ERPNext app that introduces a canonical **Party Master** record and links operational party doctypes (Customer, Supplier, Employee, etc.) into a single governed identity layer.

## What problem UPH solves

From static analysis of `hooks`, controllers, and reports, UPH targets these ERP pain points:

1. **Same legal entity spread across multiple party records**.
2. **Weak cross-role visibility** (e.g., customer + supplier under one business).
3. **No canonical hierarchy** for parent/child legal entities.
4. **Duplicate and low-quality party data** entering the system.
5. **Party-level reporting fragmentation** across role-specific doctypes.

## Core concept

UPH introduces these concepts:

- **Party Master** as the canonical legal entity node (tree/nested set).
- **Role links** from Party Master to party doctypes.
- **Rules** for allowed/required party mapping.
- **Auto-propagation** of `party_master` into configured transactional doctypes.
- **Data quality rules** with exact/fuzzy/date-window matching.

## Typical users

- ERP implementers and solution architects
- Master data governance teams
- Finance teams requiring consolidated party reporting
- Frappe developers extending party workflows

## Terminology

- **Party Master**: Canonical legal-entity record.
- **Party Type**: Target ERP doctype role (Customer/Supplier/Employee).
- **Transactional Doctype Mapping**: Config describing where `party_master` should be auto-managed.
- **Data Quality Rule**: Matching policy used to detect potential duplicate records.
