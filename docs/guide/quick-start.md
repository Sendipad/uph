# Quick Start

Unified Party Hub helps you avoid duplicate customer/supplier/employee records by introducing a single Party Master.

## Prerequisites

- Frappe Framework v15+
- ERPNext v15+
- Python 3.8+

## Install

```bash
bench get-app https://github.com/Sendipad/uph
bench --site [site_name] install-app uph
bench --site [site_name] migrate
bench build --app uph
bench restart
```

## Configure

1. Open **Party > Party Master Settings**.
2. Enable relevant party types.
3. Set your uniqueness and data quality rules.
