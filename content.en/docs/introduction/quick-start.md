---
title: "Quick Start"
weight: 3
---

# Quick Start: Your First 5 Minutes

Let's unify a Customer and Supplier into a single Party Master.

## Scenario
You do business with **"Acme Corp"**. They buy your products (Customer) and also sell you raw materials (Supplier). In standard ERPNext, these are two separate documents. In UPH, we unify them.

## Step 1: Create the Party Master

1.  Open the **Party** Workspace.
2.  Click **New Party Master** (or go to Party Master list > Add Party Master).
3.  **Name**: Enter "Acme Corp".
4.  **Type**: Select "Company" (or Individual).
5.  **Save**.

*The system generates a unique Party Master ID (e.g., `1000000001`).*

## Step 2: Link Roles

### A. Create Customer Role
1.  On the Party Master dashboard, click **Create > Customer**.
2.  The Customer form opens. Notice the **Party Master** field is auto-filled.
3.  Save the Customer.

### B. Create Supplier Role
1.  Go back to the Party Master.
2.  Click **Create > Supplier**.
3.  Save the Supplier.

## Step 3: View Unified Dashboard

Now that both roles are linked:
1.  Go to the **Party Master** for "Acme Corp".
2.  The **Dashboard** cleanly lists both the Customer and Supplier links.
3.  Click **Party Account Statement** to see a consolidated ledger of all transactions (Sales + Purchase) for this entity.

{{< hint success >}}
**Congratulations!** You have successfully unified a multi-role entity.
{{< /hint >}}
