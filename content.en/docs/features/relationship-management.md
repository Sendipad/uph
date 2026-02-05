---
title: "Relationship Management"
weight: 1
---

# Relationship Management

The **Relationship Management** module allows you to map complex, real-world connections between parties beyond simple Customer/Supplier roles. You can define hierarchies, ownership structures, and business associations directly within your Party Master.

## Key Features
- **N-to-N Relationships**: Connect any party to any other party multiple times.
- **Custom Relationship Types**: Define your own semantics (e.g., "Subsidiary", "Director", "Distributor").
- **Hierarchical Logic**: Flag relationships as hierarchical to build ownership trees.
- **Temporal Validity**: Track relationship history with *Start Date* and *End Date*.

---

## 1. Configuring Relationship Types

Before linking parties, define the types of relationships relevant to your business.

1.  Navigate to **Party > Party Relationship Type**.
2.  Click **New Party Relationship Type**.
3.  **Name**: Enter a descriptive name (e.g., `Parent Company`).
4.  **Reverse Relationship**: Link the inverse type (e.g., `Subsidiary`).
    - *Tip: If you create "Parent Company", ensure "Subsidiary" exists or create it afterwards.*
5.  **Is Hierarchical**: Check this if the relationship implies control or ownership structure.

{{< hint info >}}
**Example Pair:**
- Type A: **Employer** (Reverse: Employee)
- Type B: **Employee** (Reverse: Employer)
{{< /hint >}}

---

## 2. Creating Relationships

You can link parties directly from the Party Master dashboard or the Relationship list.

1.  Open a **Party Master** record.
2.  Go to the **Connections** tab (or check the *Relationships* shortcut on the dashboard).
3.  Click **+** to add a new relationship.
4.  **Relationship Type**: Select the type (e.g., `Subsidiary`).
5.  **Object Party**: Select the related party.
6.  **Details**:
    - **Ownership %**: If applicable, enter the percentage share.
    - **Dates**: Set valid from/to dates.
7.  **Save**.

{{< hint warning >}}
**Self-Reference Check**: You cannot link a party to itself. The system will prevent this validation error.
{{< /hint >}}

---

## 3. Visualizing Hierarchy

Use the **Party Master Tree** view to see hierarchical relationships (where `Is Hierarchical` is checked).
1.  Go to **Party > Party Master Tree**.
2.  Expand the nodes to see the parent-child structure governed by your relationship definitions.
