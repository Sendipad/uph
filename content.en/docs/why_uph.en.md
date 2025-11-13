---
title: "Why we Built UPH"
weight: 2
---


Unified Party Hub (UPH)
One master record to rule Customers, Suppliers, Employees and every other party with all its variant like currencies,subsidary..etc.
* What is UPH?
UPH is a single source of truth for every legal / commercial entity that ever transacts with your company.
Instead of maintaining a separate master for Customer, Supplier, Employee, etc., you create one Party Master and link it to as many roles (Customer, Supplier, Employee, Shareholder …) as you need.
* Why did we build it?
  
| Pain in vanilla ERPNext                                                             | How UPH fixes it                                                          |
| ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| One real-world company = 3 masters: Customer “ABC”-Currency USD, Customer “ABC”-Currency SAR,Customer “ABC”-Currency EUR | One Party Master “ABC Corp.” linked to Customers,with all its currencies |
| One real-world company = 3 masters: Customer “ABC”, Supplier “ABC”, Employee “John” | One Party Master “ABC Corp.” linked to Customer, Supplier, Employee roles |
| Changing address / tax-id must be done in N places                                  | Edit once in Party Master – changes cascade automatically                 |
| No tree view for parties                                                            | Native Nested-Set (lft/rgt) tree – groups, divisions, subsidiaries        |
| No easy way to see “all balances for one real party”                                | Every GL entry is tagged with Party Master – one click statement          |
| Duplicated custom fields on every party doctype                                     | Centralised field set, synced down to role doctypes                       |
