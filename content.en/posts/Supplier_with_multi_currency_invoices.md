---
draft: false
title: "Supplier invoice you with EUR, USD and AED"
weight: 61
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
    parent: Posts # Corrected: Use standard key-value structure for nested menu items.
    # Optionally add a weight here if you need to control the order within the Showcases group
---

{{< hint warning >}} 
<strong> Case:</strong> Supplier (Alpha Export LLC) invoices you in<strong>EUR</strong> and <strong>USD</strong>.
{{< /hint >}} 

{{% steps %}}
1. ## Enable Multi-Party Mode.
   Go to Party Master Settings → Party Type (Table)
   <strong>Supplier</strong> → <strong>Allow Multi Party</strong> = ✅, <strong>Rule Field</strong> = `default_currency` 
   
2. ## Create the Party Master and its Linked Parties( Supplier).
   Create Alpha Export LLC Party Master,as Supplier and from action menu create Link and select Currency, with a single click you can create linked supplier with all enabled currency in your system.
   
3. ## Create Purchase Invoice.
    Choose <strong>Alpha Export LLC as Party Master</strong> → if more than one supplier linked to this Party Master then a dialog popup will show with all options as selection.
   
4. ## 360 view of Party Account Statement.
   Balances in <strong>EUR</strong> & <strong>USD</strong> and any currency this supplier used to transact with you side-by-side.
{{% /steps %}}
