---
title: "Reports"
weight: 6
---

# Reports Reference

UPH provides comprehensive reporting capabilities for financial and operational insights.

---

## Party Master Ledger

**Report:** `Party Master Ledger`

Consolidated ledger view across all linked parties for a single Party Master.

### Features

- Filter by Party Master, party type, company, and date range
- View all transactions under a single Party Master
- Consolidated totals across linked parties
- Debit/Credit summaries per transaction type

### Filters

| Filter | Type | Description |
|--------|------|-------------|
| Party Master | Link | Primary party master to report on |
| From Date | Date | Start date for transactions |
| To Date | Date | End date for transactions |
| Company | Link | Filter by company |
| Party Type | Select | Customer, Supplier, or all |
| Group By | Select | Group results by |

### Use Cases

1. **Consolidated View**: See all transactions for a parent company across all subsidiaries
2. **Multi-Role Analysis**: Analyze both customer and supplier transactions for the same entity
3. **Currency Aggregation**: View transactions across all currencies under one Party Master

---

## Party Account Balances

**Report:** `Party Account Balances`

Account balance reporting per party with detailed breakdowns.

### Features

- Receivable/Payable balances by party
- Currency-wise breakdown of balances
- Aging analysis (0-30, 30-60, 60-90, 90+ days)
- Company-wise segregation

### Filters

| Filter | Type | Description |
|--------|------|-------------|
| Company | Link | Filter by company |
| Party Type | Select | Customer or Supplier |
| Party Master | Link | Filter by Party Master |
| Ageing Based On | Select | Posting date or due date |
| Report Date | Date | Date for aging calculation |

### Output Columns

- Party Name
- Party Type
- Currency
- Total Receivable/Payable
- Ageing Buckets (0-30, 30-60, 60-90, 90+)
- Average Days Overdue

---

## Party Accounting Ledger

**Report:** `Party Accounting Ledger`

Detailed accounting transactions with Party Master and accounting dimension filters.

### Features

- Filter by Party Master and accounting dimension
- Voucher-wise transaction details
- Debit/Credit summaries
- Running balance per transaction

### Filters

| Filter | Type | Description |
|--------|------|-------------|
| Party Master | Link | Primary party master |
| From Date | Date | Start date |
| To Date | Date | End date |
| Company | Link | Company filter |
| Party Type | Select | Party type filter |
| PAA | Link | Party Analytic Accounting filter |

### Output Columns

- Posting Date
- Voucher Type
- Voucher Number
- Party Master
- Against Party
- Debit
- Credit
- Balance

---

## Party Ledger

**Report:** `Party Ledger`

Standard party ledger enhanced with Party Master integration.

### Features

- Enhanced with Party Master link
- Extended filtering options
- Detailed transaction view
- Balance tracking

### Filters

| Filter | Type | Description |
|--------|------|-------------|
| Party | Dynamic Link | Party to report on |
| From Date | Date | Start date |
| To Date | Date | End date |
| Company | Link | Company filter |
| Party Master | Link | Filter by Party Master |

---

## Chronological Party Ledger

**Report:** `Chronological Party Ledger`

Time-based party transaction history for audit and analysis.

### Features

- Chronological transaction listing
- Date-wise summaries
- Transaction type filtering
- Period-based aggregation

### Filters

| Filter | Type | Description |
|--------|------|-------------|
| Party Master | Link | Party master to analyze |
| From Date | Date | Start date |
| To Date | Date | End date |
| Transaction Type | Select | Filter by transaction type |
| Company | Link | Company filter |

---

## Party Account Statement

**Report:** `Party Account Statement`

Customer/statement-style reporting for balance confirmation and statement generation.

### Features

- Statement format output
- Balance confirmation ready
- Transaction details with running balance
- Printable format

### Filters

| Filter | Type | Description |
|--------|------|-------------|
| Party | Dynamic Link | Party for statement |
| Party Type | Select | Party type |
| From Date | Date | Statement start date |
| To Date | Date | Statement end date |
| Company | Link | Company filter |

### Output Format

```
Party Account Statement
Period: 2024-01-01 to 2024-12-31

Date        | Voucher        | Debit    | Credit   | Balance
------------|----------------|----------|----------|----------
2024-01-15  | SI-2024-001    | 10,000   |          | 10,000 CR
2024-02-20  | PV-2024-001    |          | 5,000    | 5,000 CR
```

---

## Party Master Health Report

**Report:** `Party Master Health Report`

Data quality and governance reporting for compliance and quality assurance.

### Features

- Linkage status analysis
- Missing tax ID tracking
- Unlinked parties identification
- Data completeness metrics
- Governance score calculation

### Health Metrics

| Metric | Description | Health Indicator |
|--------|-------------|------------------|
| Linked Parties | Count of parties with Party Master link | Higher is better |
| Missing Tax IDs | Parties without Tax ID | Lower is better |
| Unlinked Parties | Parties not connected to Party Master | Lower is better |
| Governance Score | Composite quality score (0-100) | Higher is better |

### Filters

| Filter | Type | Description |
|--------|------|-------------|
| Company | Link | Filter by company |
| Party Type | Select | Filter by type |
| Link Status | Select | Linked or unlinked |

---

## Dashboard Charts

UPH includes several dashboard charts for real-time monitoring:

### Party Stats

- Total Party Masters
- Linked Customers
- Linked Suppliers
- Unlinked Parties

### Party Status Distribution

- Active parties
- Inactive parties
- Frozen parties
- Disabled parties

### Top Debtors/Creditors

- Top 10 customers by outstanding
- Top 10 suppliers by outstanding
- Trend analysis

### Currency Exposure

- Exposure by currency
- Concentration risk
- Multi-currency distribution

### Legal Entity Distribution

- Distribution by legal entity type
- Industry segmentation
- Territory breakdown

---

## Export Options

All reports support:

- **PDF Export**: Generate printable documents
- **Excel Export**: Spreadsheet format for analysis
- **Print**: Direct printing capability
- **Email**: Send reports via email

---

## Related Documentation

- [Core DocTypes](./core-doctypes.md)
- [Data Quality Dashboard](./data-quality-dashboard.md)
- [Configuration](./configuration.md)

{{< ai-assistant >}}
