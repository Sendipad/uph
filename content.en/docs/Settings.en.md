---
title: "Party Master Settings"
weight: 4
---
{{< hint info >}}
<strong> Upon installing the app </strong> Most of settings will be avaliable dynamically , Just you must learn more in order to make every thing work smoothly. 
{{< /hint >}}
Party Master Settings → table Party Types \
All party Type from ERPNext Party Type will be set in here.
| Column                | Meaning                                                                                                                                      |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **Mandatory**         | Party Master becomes **required** when saving a Customer/Supplier/…                                                                          |
| **Allow Multi Party** | More than one Customer (or Supplier) can point to the **same Party Master** – differentiated by the **Rule Field** (e.g. `default_currency`) |



8.2 Transaction doctypes
Party Master Settings → table Document Types
Add any custom doctype that has a Link or Dynamic Link to a party
System will auto-insert party_master field and keep it in sync
Child tables supported – set Parent Doctype (e.g. “Journal Entry Account” parent = “Journal Entry”)
