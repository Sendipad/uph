---
title: "Installation"
weight: 3
---

Installation:
```
bench get-app https://github.com/Sendipad/uph
bench --site erp.your.com install-app uph
```
The app will:
1. Create Party Master DocType (tree)
2. Add party_master Link field on every transactional doctype (SI, PI, SO, PO, DN, PR, PE, JE, Expense Claim)
3. Add party_master + is_default_for_party_master on Customer, Supplier, Employee, Shareholder
4. Create Party Master Settings (single) where you can toggle mandatory / multi-party rules
