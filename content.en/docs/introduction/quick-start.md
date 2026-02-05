---
title: "Quick Start"
weight: 3
---

# Quick Start: Your First 5 Minutes

Let's unify a Customer and Supplier into a single Party Master and explore key UPH features.

## Scenario
You do business with **"Acme Corp"**. They buy your products (Customer) and also sell you raw materials (Supplier). In standard ERPNext, these are two separate documents. In UPH, we unify them.

## Step 1: Create the Party Master

1.  Open the **Party** Workspace.
2.  Click **New Party Master** (or go to Party Master list > Add Party Master).
3.  **Name**: Enter "Acme Corp".
4.  **Party Type**: Select "Company" (or Individual).
5.  **Legal Entity Type**: Select "LLC" (or appropriate type).
6.  **Save**.

*The system generates a unique Party Master ID (e.g., `PM-ACME-001`).*

## Step 2: Configure Accounts

Set up multi-currency support:

1.  In the **Accounts** section, click **Add Row**.
2.  Select a **Company**.
3.  Set **Default Currency** (e.g., USD).
4.  Set the **Account** for Receivables.
5.  Add another row for EUR with different accounts if needed.

*UPH will automatically use the correct account based on transaction currency.*

## Step 3: Link Roles

### A. Create Customer Role
1.  On the Party Master dashboard, click **Create > Customer**.
2.  The Customer form opens. Notice the **Party Master** field is auto-filled.
3.  Save the Customer.

### B. Create Supplier Role
1.  Go back to the Party Master.
2.  Click **Create > Supplier**.
3.  Save the Supplier.

## Step 4: View Unified Dashboard

Now that both roles are linked:
1.  Go to the **Party Master** for "Acme Corp".
2.  The **Dashboard** cleanly lists both the Customer and Supplier links.
3.  View **Total Sales**, **Total Purchases**, and **Outstanding Balances** at a glance.
4.  Click **Party Account Statement** to see a consolidated ledger of all transactions.

## Step 5: Check Data Quality

Navigate to the Data Quality Dashboard:

1.  Go to **Party > Data Quality Dashboard**.
2.  Review the governance score and statistics.
3.  Check for potential duplicates using the similarity slider.

## Step 6: Create a Transaction

Test the unified experience:

1.  Create a **Sales Invoice** for "Acme Corp" (Customer role).
2.  Notice the **Party Master** field is automatically set.
3.  Create a **Purchase Invoice** for "Acme Corp" (Supplier role).
4.  Both transactions link to the same Party Master.

{{< hint success >}}
**Congratulations!** You have successfully:
- Created a unified Party Master
- Configured multi-currency accounts
- Linked multiple roles (Customer + Supplier)
- Verified the consolidated dashboard
- Tested transactional integration
{{< /hint >}}

---

## Next Steps

Now that you've mastered the basics, explore:

1.  **Data Quality Rules**: Configure duplicate detection rules
2.  **Party Analytic Accounting**: Set up branch/site-level reporting
3.  **Hierarchy**: Create parent-child Party Master relationships
4.  **Reports**: Explore Party Account Statement and Party Ledger reports
