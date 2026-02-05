---
title: "Installation"
weight: 2
---

# Installation Guide

UPH is a standard Frappe application designed to run alongside ERPNext.

## Prerequisites
- **Frappe Framework**: v15 or v16
- **ERPNext**: Installed and active on the site

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

---

## What Happens During Install?
The installation script performs the following actions:
1.  **Schema Extensions**: Adds `party_master` link fields to all major transaction DocTypes (Sales Invoice, Purchase Order, etc.).
2.  **Party Customization**: Adds fields to `Customer`, `Supplier`, and `Employee` forms.
3.  **Workspace**: Creates the "Party" workspace in the Desk.
