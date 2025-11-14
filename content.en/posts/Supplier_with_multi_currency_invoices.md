---
title: "Supplier invoice you with EUR, USD and AED"
weight: 3
tags : [
    "usage",
    "case",
    "example",
    "howto",
]
date : "2025-04-02"
categories : [
    "Usage Cases",
    "examples",
]
menu : 
  main: 
   parent: Showcases
---

{{< hint info >}} 
Your supplier <strong>Alpha Export LLC</strong> invoices you in <strong>EUR</strong> and <strong>USD</strong>.
{{< /hint >}} 

{{% steps %}}
1. ## Party Master Settings → Party Type (Table)
   <strong>Supplier</strong> → <strong>Allow Multi Party</strong> = ✅, <strong>Rule Field</strong> = `default_currency` 
   
2. ## Go to Party Master, Alpha Export LLC
   Create Party default is supplier → <strong>currency</strong> = <strong>EUR</strong> → <strong>Save</strong>.
   Again Create Party again → <strong>currency</strong> = <strong>USD</strong> → <strong>Save</strong>.
   
3. ## Go to Purchase Invoice
   → Choose <strong>Alpha Export USD</strong> → <strong>currency</strong> = <strong>USD</strong> → <strong>Submit</strong>.
   
4. ## Party Account Statement
   Balances in <strong>EUR</strong> & <strong>USD</strong> side-by-side.
{{% /steps %}}
