---
title: "Data Quality Dashboard"
weight: 2
---

# Data Quality Dashboard

The **Data Quality Dashboard** is your control center for maintaining a clean and accurate Party database. It automatically detects potential duplicates across your Party Masters using intelligent similarity scoring and normalization techniques.

## Key Capabilities
- **Automated Detection**: Scans party names using advanced text normalization and fuzzy matching.
- **Smart Scoring**: Assigns a similarity score (0-100%) using RapidFuzz algorithm.
- **Merge Action**: Consolidate duplicate records into a single master with one click.
- **Exclusion List**: Permanently ignore false positives with dismissal reasons.
- **Dashboard Statistics**: Provides summary metrics including total parties, groups, exclusions, and potential duplicates.

---

## 1. Using the Dashboard

1.  Navigate to **Party > Data Quality Dashboard**.
2.  **Filter**: Adjust the "Minimum Similarity Score" slider to filter results (Default: 70%).
3.  **Review Pairs**: The dashboard lists potential duplicate pairs with similarity scores.

### Understanding the Score
- **>90%**: Highly likely to be a duplicate (e.g., "Acme Corp" vs "Acme Corp.").
- **70-90%**: Likely duplicate, check details (e.g., "John Doe" vs "Johnathan Doe").
- **<70%**: Possible false positive.

---

## 2. Text Normalization

The dashboard uses **advanced text normalization** to improve duplicate detection accuracy:

### Arabic Character Normalization
- Converts different Arabic letter forms to standard forms (e.g., أ, إ, آ → ا)
- Handles Persian character variations (e.g., ك → ک, ي → ی)
- Removes diacritics (harakat, tanwin)
- Normalizes numerals (Indian → Arabic digits)

### Latin Character Normalization
- Removes accents and diacritics (e.g., é → e, ñ → n)
- Handles common prefixes/suffixes (e.g., LLC, Inc, Corp)
- Normalizes whitespace and case

---

## 3. Resolving Duplicates

For each identified pair, you have two primary actions:

### A. Merge
If the records represent the same entity:
1.  Click **Merge**.
2.  Confirm the action and select fields to keep from each record.
3.  **Result**: The *secondary* party is merged into the *primary* party. All linked documents (Invoices, Orders) are reassigned to the primary party, and the secondary party is deleted. A duplicate exclusion entry is automatically created.

### B. Dismiss (Ignore)
If the records are distinct entities (e.g., "Apple Inc." vs "Apple Store"):
1.  Click **Dismiss**.
2.  (Optional) Provide a reason.
3.  **Result**: The pair is added to the **Duplicate Exclusion** list and will not reappear in the dashboard.

{{< hint tip >}}
**Undo Dismissal**: You can view and restore dismissed pairs by navigating to the **Duplicate Exclusion** DocType list.
{{< /hint >}}

---

## 4. Dashboard Statistics

The dashboard provides real-time statistics:
- **Total Parties**: Number of active Party Masters (non-group)
- **Total Groups**: Number of Party Master groups
- **Total Exclusions**: Number of dismissed duplicate pairs
- **Incomplete Parties**: Number of parties without party numbers
- **Potential Duplicates**: Number of potential duplicate pairs (based on current filters)

---

## 5. Performance Optimization

- Uses sampling approach for duplicate detection to ensure fast performance
- Results are paginated to handle large datasets efficiently
- Normalization and similarity scoring are optimized for Arabic text

---

## 6. Technical Implementation

The Data Quality Dashboard is implemented using:
- **Backend**: Python with RapidFuzz library for fuzzy matching
- **Frontend**: Frappe Framework with Vue.js
- **Normalization**: Custom implementation handling Arabic, Persian, and Latin characters
- **Storage**: Duplicate exclusion records stored in `Duplicate Exclusion` DocType
