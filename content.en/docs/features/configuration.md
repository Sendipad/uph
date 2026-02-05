---
title: "Configuration"
weight: 10
---

# Party Master Settings

To access global settings, navigate to **Party > Party Master Settings**.

## 1. Party Types & Logic

Here you configure how UPH interacts with standard ERPNext party types (Customer, Supplier, Employee, etc.).

| Setting | Description |
| :--- | :--- |
| **Mandatory** | If checked, users **must** link a Party Master when creating a new Customer/Supplier. |
| **Allow Multi Party** | Enables linking multiple Customers to a *single* Party Master. |
| **Rule Field** | Used when "Allow Multi Party" is on. Defines the distinguishing field (e.g., `default_currency`). <br> *Example*: One Party Master can have a USD Customer record and a EUR Customer record. |

## 2. Transaction Document Types

UPH automatically injects the `party_master` field into transactional documents to ensure all financial data is tracked.

- **System managed**: Standard DocTypes (Sales Invoice, Purchase Invoice, etc.) are pre-configured.
- **Custom DocTypes**: You can add your own custom DocTypes here. The system will auto-insert the link field and keep it in sync.

{{< hint info >}}
**Child Tables**: UPH also supports tracking at the item/account line level. Set the "Parent Doctype" for the child table configuration (e.g., for `Journal Entry Account`, set parent to `Journal Entry`).
{{< /hint >}}
