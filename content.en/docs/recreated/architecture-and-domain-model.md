---
title: "Architecture and Domain Model"
weight: 2
---

# Architecture Overview

UPH is represented as a non-intrusive extension model around ERPNext party entities.

## High-Level Layers

1. **Domain Layer**
   - Party Master (canonical identity)
   - Party role links (Customer/Supplier/Employee)
   - Relationship model (N:N and hierarchy)

2. **Configuration Layer**
   - Party Master Settings (single DocType pattern)
   - Per-party-type uniqueness and behavior controls
   - Dynamic field mapping/injection controls

3. **Validation + Governance Layer**
   - Duplicate detection and normalization
   - Quality scoring and dashboard APIs
   - Merge/dismiss workflows

4. **Accounting/Reporting Layer**
   - Party Analytic Accounting for segmented reporting
   - Currency/account-aware mappings
   - Consolidated statements and health metrics

5. **Performance Layer**
   - Smart cache utility pattern
   - Query optimization and batched updates
   - Background queue updates for bulk consistency tasks

## Domain Model (Inferred from Source)

### Primary Entities

- **Party Master**
  - Root identity for legal entities
  - Supports parent-child hierarchy
  - Holds governance and role linkage metadata

- **Party Master Parties**
  - Child/junction model connecting Party Master to role records
  - Dynamic link pattern for party type + party record

- **Party Master Settings**
  - Single settings document controlling runtime behavior
  - Contains party-type rules, DocType settings, and field mapping controls

- **Party Analytic Accounting**
  - Additional accounting dimension model
  - Supports effective dates and allow/restrict style controls

- **Party Relationship**
  - N-to-N relationship mapping for ownership/corporate links

### Secondary/Operational Entities

- Duplicate tracking and exclusion model
- Dashboard aggregation models/views
- Quality rule models for validation thresholds and matching rules

## Business Workflows

### 1) Canonical Party Onboarding

1. Create Party Master.
2. Attach one or more operational roles.
3. Apply uniqueness and data quality checks.
4. Start using role records in transactions while preserving canonical linkage.

### 2) Multi-Currency Operations

1. Configure account/currency mappings in Party Master context.
2. Use the same legal entity across role transactions.
3. Resolve appropriate account path by transaction context.

### 3) Duplicate Management

1. Run duplicate detection via dashboard API.
2. Review scored candidates.
3. Merge duplicates or dismiss false positives.
4. Trigger reference update process to preserve transactional integrity.

### 4) Background Reference Synchronization

1. Party linkage changes trigger update workflow.
2. Background job updates configured transactional DocTypes.
3. New documents continue to be auto-tagged by hooks.

