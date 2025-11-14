---
title: "Supplier invoice you in EUR, USD and AED"
weight: 61

categories : [
    "Usage Cases",
    "Supplier","Multi-Currencies"
]
---

{{< hint danger >}} 
**Case:** 
Supplier (Alpha Export LLC) invoices you in<strong>EUR, USD</strong> and <strong> AED </strong> <br>
This guide shows how to configure a multi-currency supplier and record transactions accurately.

{{< /hint >}} 

{{% steps %}}
1. ## Enable Multi-Party Mode.
   Go to Party Master Settings → Party Type (Table)
   <strong>Supplier</strong> → <strong>Allow Multi Party</strong> = ✅, <strong>Rule Field</strong> = `default_currency` 
   
2. ## Create the Party Master and its Linked Parties( Supplier).
   Create Alpha Export LLC Party Master,as Supplier and from action menu create Link and select Currency, with a single click you can create linked supplier with all enabled currencies in your system.
   
3. ## Create Purchase Invoice.
    Choose <strong>Alpha Export LLC as Party Master</strong> → if more than one supplier linked to this Party Master then a dialog popup will show with all options as selection.
    <small> You can set this as default so next time it get fetch dynamically upon selecting the same Party Master</small>
   
4. ## 360° view of Party Account Statement.
   Full Statments or Balances in <strong>EUR</strong> & <strong>USD</strong> and any currency this supplier used to transact with you side-by-side.
{{% /steps %}}


### Result  
You can now manage and report supplier activity across all three currencies clearly and accurately. All Purchase Invoices linked to this Party Master—across all its linked currency-based Suppliers—are accessible and consolidated in one place.