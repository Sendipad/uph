---
title: "Hierarchical Numbering"
weight: 3
---

# Hierarchical Numbering

UPH employs a logic-driven numbering system that reflects the structure of your Party Master tree. This ensures that party numbers are predictable, sortable, and indicative of their position in the hierarchy.

## Numbering Logic

The numbering follows a strict parent-child incremental pattern:

### 1. Root Nodes (+1000)
Top-level groups (Roots) are incremented by 1000.
- **Root 1**: `1000`
- **Root 2**: `2000`
- **Root 3**: `3000`

### 2. Sub-Groups (+100)
Direct children of a group (that are themselves groups) increment by 100 from their parent's base.
- Parent `1000` -> Child Group 1: `1100`
- Parent `1000` -> Child Group 2: `1200`
- Parent `2000` -> Child Group 1: `2100`

### 3. Leaf Nodes (Sequential Suffix)
Operational parties (Leaves) are assigned a 6-digit suffix appended to their parent's base.
- Parent Group `1100` ->
    - Leaf 1: `1100000001`
    - Leaf 2: `1100000002`

---

## Configuration

This logic is enforced by the **Party Master** controller. To customize the sequence or prefix:

1.  Navigate to **Party > Party Master Settings**.
2.  Enable/Disable **"Mandatory Logic"** (if exposed in settings).
3.  *Note: In v2.6.0, this logic is hardcoded for consistency across the application.*

{{< hint info >}}
**Legacy Data**: If you import legacy data, you can preserve old codes by setting them manually during import. The system calculates the next number based on the highest existing number in the relevant branch.
{{< /hint >}}
