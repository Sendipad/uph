---
title: "Installation"
weight: 2
---

# Installation Guide

UPH is a standard Frappe application designed to run alongside ERPNext.

## Prerequisites
- **Frappe Framework**: v15 or v16
- **ERPNext**: v15 or v16
- **Python**: 3.8+
- **Database**: MariaDB or PostgreSQL

## Setup

### 1. Get the App
Download the application from GitHub to your bench:
```bash
bench get-app https://github.com/Sendipad/uph
```

### 2. Install on Site
Install the app on your specific site (replace `site_name` with your actual site URL):
```bash
bench --site [site_name] install-app uph
```

### 3. Migrate and Build
Ensure all database schemas and assets are compiled:
```bash
bench --site [site_name] migrate
bench build --app uph
```

### 4. Restart the Server
Restart your bench to apply all changes:
```bash
bench restart
```

---

## What Happens During Install?

The installation script performs the following actions:

### 1. Schema Extensions
- Adds `party_master` link fields to all major transaction DocTypes (Sales Invoice, Purchase Invoice, Journal Entry, Payment Entry, etc.)
- Adds fields to `Customer`, `Supplier`, and `Employee` forms
- Creates `Party Master` DocType with tree hierarchy support

### 2. Configuration Setup
- Creates **Party Master Settings** document with default configuration
- Sets up default document type mappings
- Configures caching system

### 3. Workspace Creation
- Creates the "Party" workspace in the Desk
- Adds dashboard charts and number cards
- Configures default reports

### 4. Localization
- Installs Arabic language translations (100% coverage)
- Sets up regional handling for Arabic text normalization

---

## Post-Installation Steps

### 1. Configure Party Master Settings
Navigate to **Party > Party Master Settings** and configure:
- Enable/disable party types (Customer, Supplier, Employee)
- Set uniqueness rules per party type
- Configure data quality rules
- Enable/disable Party Analytic Accounting

### 2. Set Up Data Quality Rules
Create data quality rules to prevent duplicates:
- Navigate to **Party > Data Quality Rule**
- Define rules for each party type
- Set threshold scores for fuzzy matching

### 3. Verify Installation
1. Check that the "Party" workspace appears in the Desk
2. Create a test Party Master
3. Link a Customer and Supplier to it
4. Verify the Data Quality Dashboard is accessible

---

## Upgrade from Previous Versions

To upgrade UPH to the latest version:

```bash
bench get-app https://github.com/Sendipad/uph --branch main
bench --site [site_name] migrate
bench build --app uph
bench restart
```

{{< hint warning >}}
**Important**: Always backup your database before performing upgrades.
{{< /hint >}}

---

## Compatibility

| Component | Version |
|-----------|---------|
| Frappe Framework | v15+ |
| ERPNext | v15+ |
| Python | 3.8+ |
| Database | MariaDB / PostgreSQL |
