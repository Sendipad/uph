---
title: "Data Quality Dashboard"
weight: 2
---

# Data Quality Dashboard

The **Data Quality Dashboard** is your control center for maintaining a clean and accurate Party database. It automatically detects potential duplicates across your Customers, Suppliers, and Party Masters using intelligent similarity scoring.

## Key Capabilities
- **Automated Detection**: Scans names, emails, and phone numbers for similarities.
- **Smart Scoring**: Assigns a similarity score (0-100%) to help you prioritize.
- **Merge Action**: Consolidate duplicate records into a single master with one click.
- **Exclusion List**: Permanently ignore false positives.

---

## 1. Using the Dashboard

1.  Navigate to **Party > Data Quality Dashboard**.
2.  **Filter**: Adjust the "Minimum Similarity Score" slider to filter results (Default: 85%).
3.  **Review Pairs**: The dashboard lists potential duplicate pairs, showing the "Subject Party" (Existing) and "Object Party" (Potential Duplicate).

### Understanding the Score
- **>95%**: Highly likely to be a duplicate (e.g., "Acme Corp" vs "Acme Corp.").
- **80-95%**: Likely duplicate, check details (e.g., "John Doe" vs "Johnathan Doe").
- **<80%**: Possible false positive.

---

## 2. Resolving Duplicates

For each identified pair, you have two primary actions:

### A. Merge
If the records represent the same entity:
1.  Click **Merge**.
2.  Confirm the action.
3.  **Result**: The *secondary* party is merged into the *primary* party. All linked documents (Invoices, Orders) are reassigned to the primary party, and the secondary party is deleted.

### B. Dismiss (Ignore)
If the records are distinct entities (e.g., "Apple Inc." vs "Apple Store"):
1.  Click **Dismiss**.
2.  (Optional) Provide a reason.
3.  **Result**: The pair is added to the **Duplicate Exclusion** list and will not reappear in the dashboard.

{{< hint tip >}}
**Undo Dismissal**: You can view and restore dismissed pairs by navigating to the **Duplicate Exclusion** DocType list.
{{< /hint >}}
