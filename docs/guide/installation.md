# Installation

## Standard installation flow

```bash
bench get-app https://github.com/Sendipad/uph
bench --site [site_name] install-app uph
bench --site [site_name] migrate
bench build --app uph
bench restart
```

## Post-install checklist

- Verify Party workspace exists.
- Create one Party Master test record.
- Link it with Customer/Supplier.
- Confirm dashboards and reports open.

!!! warning
    Always back up the database before upgrades.
