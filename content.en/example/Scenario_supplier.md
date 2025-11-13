---
title: "Supplier invoice you with EUR, USD and AED"
weight: 3
---

{{< hint info >}} 
Your supplier **Alpha Export LLC** invoices you in **EUR** and **USD**.
{{< /hint >}} 

{{< steps >}}
1. ## Party Master Settings → Party Type (Table)
**Supplier** → **Allow Multi Party** = ✅, **Rule Field** = `default_currency` 
2. ## Go to Party Master, Alpha Export LLC
Create Party default is supplier → **currency** = **EUR** → **Save**
Again Create Party again → **currency** = **USD** → **Save**
3. ## Go to Purchase Invoice 
→ Choose **Alpha Export USD** → **currency** = **USD** → **Submit**
4. ## Party Account Statement 
Balances in **EUR** & **USD** side-by-side
{{< /steps >}}
