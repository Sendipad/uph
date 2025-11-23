---
title: "Data Quality Rules"
weight: 1
bookFlatSection: false
bookToc: true
bookCollapseSection: false
---

# Data Quality Rules

## Overview

The **Data Quality Rule** system is a flexible, configurable deduplication engine that prevents duplicate records in your Frappe/ERPNext application. It uses a weighted scoring system to identify potential duplicates based on multiple criteria.

---

## Core Concepts

### Rule Structure

- **Document Type**: Which DocType to monitor (e.g., Party Master, Customer, Supplier)
- **Trigger**: When to check (On Save, On Submit)
- **Action**: What to do when duplicates are found (Warn, Block)
- **Threshold Score**: Minimum score to trigger the action
- **Conditions**: List of field comparisons with weights

### Condition Types

| Type | Behavior | Score Calculation |
|------|----------|-------------------|
| **Exact Match** | Values must be identical | Full weight if match |
| **Date Range** | Dates within X days | Full weight if within window |
| **Fuzzy Match** | Similar text (normalized) | Weight × Similarity % |

### Scoring Formula

```text
Total Score = Σ (Score from each condition)

If Total Score ≥ Threshold → Trigger Action
Scenario Examples
Scenario 1: Basic Party Name Deduplication
Goal: Warn users when creating parties with similar names

yaml
Rule Name: Party Name Similarity Check
Document Type: Party Master
Trigger: On Save
Action: Warn
Threshold Score: 80

Conditions:
  - Field: normalized_party_name
    Check Type: Fuzzy Match
    Weight: 100
    Minimum Similarity: 85%
How it works:

User creates "Acme Corporation"
System finds existing "Acme Corp"
Similarity: 90%
Score: 100 × 0.90 = 90 ≥ 80 ✅
Result: Warning shown
Scenario 2: Strict Tax ID Validation
Goal: Block creation of parties with duplicate Tax IDs

yaml
Rule Name: Tax ID Duplicate Block
Document Type: Party Master
Trigger: On Save
Action: Block
Threshold Score: 100

Conditions:
  - Field: tax_id
    Check Type: Exact Match
    Weight: 100
How it works:

User creates party with Tax ID "123-456-789"
System finds exact match
Score: 100 ≥ 100 ✅
Result: Save blocked with error
Scenario 3: Multi-Field Composite Check
Goal: Detect duplicates using name + mobile combination

yaml
Rule Name: Name & Mobile Duplicate Check
Document Type: Party Master
Trigger: On Save
Action: Warn
Threshold Score: 150

Conditions:
  - normalized_party_name (Fuzzy, weight=100, min_sim=80%)
  - mobile_no (Exact, weight=100)
Examples:

Scenario	Name Match	Mobile Match	Total Score	Result
Same name, same mobile	95 (fuzzy)	100 (exact)	195	⚠️ Warn
Similar name, different mobile	90 (fuzzy)	0	90	✅ Pass
Different name, same mobile	0	100 (exact)	100	✅ Pass
Similar name, same mobile	85 (fuzzy)	100 (exact)	185	⚠️ Warn
Scenario 4: Tiered Validation (Warn → Block)
Goal: Warn at low confidence, block at high confidence

yaml
Rule 1: Possible Duplicate Warning
  Threshold: 120
  Action: Warn
  Conditions: name(100) + mobile(50) + email(50)

Rule 2: Definite Duplicate Block
  Threshold: 180
  Action: Block
  Conditions: name(100) + mobile(50) + email(50)
{{< hint info >}} Performance Optimization
Both rules check same fields → Candidates fetched once (cached!)
System evaluates both scores, Block takes priority over Warn {{< /hint >}}

Scenario 5: Date Range for Event Deduplication
Goal: Prevent booking same venue on overlapping dates

yaml
Rule Name: Event Date Overlap Check
Document Type: Event Booking
Trigger: On Save
Action: Block
Threshold Score: 150

Conditions:
  - venue_name (Exact, weight=100)
  - event_date (Date Range, window_days=3, weight=100)
How it works:

User books "Grand Hall" for 2024-12-25
System finds existing booking for 2024-12-24
Date diff: 1 day ≤ 3 days window
Score: 100 (venue) + 100 (date) = 200 ≥ 150 ✅
Result: Booking blocked
Scenario 6: Conditional Rules (filter_condition)
Goal: Apply stricter rules to companies, lenient for individuals

yaml
Rule 1: Individual Party Check
  Filter: doc.type == "Individual"
  Threshold: 120
  Action: Warn
  Conditions: name(100) + mobile(50)

Rule 2: Company Party Check
  Filter: doc.type == "Company"
  Threshold: 180
  Action: Block
  Conditions: name(100) + tax_id(100) + business_reg(100)
How it works:

Individual creation → Rule 1 applies, lenient warning
Company creation → Rule 2 applies, strict blocking
Scenario 7: High-Value Transaction Monitoring
Goal: Only check duplicates for large invoices

yaml
Rule Name: High-Value Invoice Duplicate Check
Document Type: Sales Invoice
Trigger: On Submit
Action: Block
Threshold Score: 150
Filter Condition: doc.grand_total > 10000

Conditions:
  - customer (Exact, weight=100)
  - posting_date (Date Range, window=7, weight=50)
  - grand_total (Exact, weight=100)
How it works:

Invoice for $5,000 → Rule skipped (filter_condition False)
Invoice for $15,000 → Rule applies
Best Practices
1. Start with Warnings
{{< hint warning >}} Always use Action: Warn initially to gather data, then switch to Block after tuning. {{< /hint >}}

2. Use normalized_party_name
For Party Master, always use normalized_party_name instead of party_name for better fuzzy matching.

3. Set Realistic Thresholds
Strict: 80-90% of total weight
Balanced: 60-75% of total weight
Lenient: 40-60% of total weight
4. Layer Your Rules
Use multiple rules with different thresholds:

Low threshold → Warn
High threshold → Block
5. Use Bypass Roles
Add bypass roles for administrators or data migration users.

Performance Optimization
{{< hint info >}} Automatic Optimization
The system automatically optimizes when multiple rules check the same fields:

Before: 5 rules × 1 query each = 5 database queries
After:  5 rules, same fields = 1 cached query
Result: Up to 80% reduction in database load! 🚀 {{< /hint >}}

Field Reference
Data Quality Rule (Parent)
Field	Type	Description
rule_name	Data	Unique name for the rule
document_type	Link	Target DocType to monitor
trigger	Select	When to check (On Save/On Submit)
action	Select	What to do (Warn/Block)
threshold_score	Float	Minimum score to trigger action
enabled	Check	Enable/disable this rule
filter_condition	Code	Optional Python expression to filter documents
bypass_roles	Table	Roles that can bypass this rule
conditions	Table	List of field comparison conditions
Data Quality Rule Condition (Child)
Field	Type	Depends On	Description
field	Autocomplete	-	Field to check for duplicates
check_type	Select	-	Exact Match / Fuzzy Match / Date Range
weight	Float	-	Importance/contribution of this condition
minimum_similarity	Percent	Fuzzy Match	Minimum similarity % (default: 80%)
window_days	Int	Date Range	Allowed difference in days
API Reference
Backend Functions
python
# Normalize text for fuzzy matching
from uph.party.controllers.mdm import normalize_text

normalized = normalize_text("Café Société")
# Returns: "cafe societe"
python
# Manual validation
from uph.party.controllers.mdm import validate_document_quality

doc = frappe.get_doc("Party Master", "PM-0001")
validate_document_quality(doc, "validate")
Bulk Update Script
Update existing records with normalized names:

python
from uph.party.controllers.mdm import normalize_text

parties = frappe.get_all("Party Master", fields=["name", "party_name"])
for p in parties:
    if p.party_name:
        norm = normalize_text(p.party_name)
        frappe.db.set_value(
            "Party Master", 
            p.name, 
            "normalized_party_name", 
            norm, 
            update_modified=False
        )
        
frappe.db.commit()
print(f"Updated {len(parties)} records.")
Troubleshooting
Rules Not Triggering
{{< details title="Check these items" open=false >}}

Rule enabled: Ensure enabled = 1
Correct trigger: Match trigger (On Save/On Submit) with your action
Filter condition: Check if filter_condition is excluding your document
Bypass roles: Verify your user doesn't have a bypass role
Threshold too high: Lower the threshold temporarily for testing {{< /details >}}
Performance Issues
{{< details title="Optimization tips" open=false >}}

Add filter conditions: Skip unnecessary checks
Use exact match first: Put exact match conditions before fuzzy
Limit fuzzy fields: Only use fuzzy match on critical fields
Reduce candidate pool: Use exact/date range to narrow candidates
Check database indexes: Ensure indexed fields are used in conditions {{< /details >}}
False Positives
{{< details title="Tuning recommendations" open=false >}}

Increase threshold: Require higher confidence
Increase minimum_similarity: For fuzzy matches, raise from 80% to 85-90%
Add more conditions: Combine multiple fields for better accuracy
Use filter conditions: Apply rules selectively
Adjust weights: Increase weight of critical fields {{< /details >}}
Migration Guide
From Legacy System
If migrating from a custom deduplication system:

Identify existing rules: Document current logic
Create corresponding Data Quality Rules: Map to new structure
Test with Action: Warn: Gather data before blocking
Tune thresholds: Based on real-world matches
Switch to Block: Once confident in accuracy
Remove old code: Clean up legacy validation
Adding New DocTypes
To enable for a new DocType:

Add normalized_* fields (if using fuzzy match)
Create Data Quality Rules via UI
Test thoroughly with sample data
Monitor for false positives/negatives
Adjust weights and thresholds as needed
License
Copyright (c) 2024, Abdo Ruzaqi and contributors