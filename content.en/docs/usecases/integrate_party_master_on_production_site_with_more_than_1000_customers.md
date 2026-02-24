---
title: "Migrate 1,000+ Customers to Party Master (with Multi-Currency Support)"
weight: 62

categories: [
    "Usage Cases",
    "Customer",
    "Migration",
    "Multi-Currencies"
]
---

> [!NOTE]
> **Case:** You operate a production site with **1,000+ Customers**.  
> Many of them belong to the same commercial entity but use different **default currencies**.  
> You want to migrate all customers into the new **Party Master** structure quickly, accurately, and without data loss.

## Goal
Enable a smooth migration where:
- Multiple customer records belonging to the same entity become a single **Party Master**  
- Currency-specific customer entries become **Linked Parties**  
- All invoices, GL Entries, and balances remain intact  
- The system becomes cleaner, consistent, and easier to maintain at scale

### 1. Enable Multi-Party Mode
   Go to **Party Master Settings → Party Type (Table)**  
   - Select **Customer**  
   - Set **Allow Multi Party = ✅**  
   - Set **Rule Field = `default_currency`**

### 2. Export and Identify Customers Belonging to the Same Entity
   Export the current Customer list with:  
   - Customer Name  
   - Default Currency  
   - Customer Group  
   - Parent Commercial Group (if available)

   Sort/group customers by their commercial entity (e.g., “Alpha Group” with USD/EUR/AED).

### 3. Prepare a Cleaned Party Master Import File
   From the exported list:  
   - Remove duplicate entries belonging to the same entity  
   - Add a **Parent Party Master Name** for each group according to your classification tree  
   - Set **Party Type = Customer**  
   - Import the file using **Party Master Import**

### 4. Fetch Existing Customers for Each Party Master (UI-assisted linking)
   Go to **Party Master Tree View**:  
   - For each leaf node that has unlinked parties, a **primary “Fetch Existing Party”** button appears  
   - A dialog will list the most similar/related Customers at the top  
     (Using name similarity, currency, and grouping logic)  
   - Select the correct Customer(s) to link them to the Party Master and save

### 5. Existing Transactional Documents Automatically Sync
   After linking a Customer to a Party Master:  
   - All existing transactions (Invoices, Deliveries ...) automatically get their **Party Master** field filled.
     [See Configuration]({{< relref "../features/configuration.md" >}})
   - No impact on accounting data like GL Entries, invoice status, or amounts.  

   👉 See:  
   **[How existing documents sync Party Master automatically]({{< relref "../Advanced/background_sync_party_master_field_following_change_on_party.md" >}})**

### Result  
Your 1,000+ customers are now fully migrated into the Party Master structure.  
Customers belonging to the same commercial entity (even with different currencies) are unified under one Party Master, while currency-specific Customers remain as Linked Parties.  
The system becomes cleaner, more accurate, and significantly easier to scale and maintain.
