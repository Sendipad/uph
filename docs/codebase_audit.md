# UPH Codebase Audit (Frappe/ERPNext)

## Why keep `create_custom_indices()`?

`CREATE INDEX` is not optional for this app’s runtime behavior on medium/large ledgers. UPH frequently syncs / scans voucher tables by `party_*`, `party_master`, and status fields. Without composite indexes, those operations degrade into full-table scans and can cause lock contention during reconcile/sync jobs.

So the function should **not** be removed, but it should be controlled:

- keep it idempotent,
- run it with existence checks,
- execute it in migration/patch flows (not every install bootstrap path).

This aligns with Frappe conventions where schema-shaping work belongs to migrate/patch lifecycle.

## High-impact issues fixed

1. **Wrong party fields in index bootstrap**
   - `Sales Invoice` must use `customer`.
   - `Purchase Invoice` must use `supplier`.

2. **Incomplete column existence checks in index bootstrap**
   - Validation now checks all configured index columns.

3. **Index DDL column quoting**
   - Column names are now quoted for safer generated SQL.

4. **Settings validation robustness**
   - `document_type` is now validated before `frappe.get_meta()` use.

4. **Root bootstrap assumed a single root, but setup templates can be multi-root.**
   - `create_party_master_tree()` logged errors when multiple roots exist.
   - Setup Wizard templates (e.g. `simple`) intentionally create multiple top-level groups.
   - **Fix implemented:** treat multi-root as valid and only create fallback root when no root exists.

## Install-time functions review (Production suitability)

### Keep in production install/migrate

- `ensure_essential_erpnext_fixtures()`
  - Required baseline Party Types for app flows.
- `setup_initial_document_types()` / `setup_party_types_table()`
  - Core UPH configuration bootstrap.
- `create_party_master_tree()`
  - Ensures a root exists on fresh installs without enforcing single-root topology.
- `create_party_analytic_accounting_dimension()`
  - Required when analytic accounting feature is used.
- `create_custom_indices()`
  - Keep, and execute through `on_migrate`/patch flow rather than generic install bootstrap.

### Better as test/dev-only seed behavior

- `create_gender_fixtures()`
  - Not a UPH-specific production requirement.
  - Better constrained to test/developer environments.

## Anti-pattern refactor status

### Refactored in this pass

1. **Controller-level commits** (`frappe.db.commit()` in deep business logic).
   - Removed commits from party sync / merge controller paths so transaction boundaries are owned by Frappe request/job lifecycle.
2. **Patch scripts relying on `print()` instead of structured logging.**
   - Replaced `print()` calls with `frappe.logger("uph.patches")` info/warning logs while preserving `frappe.log_error` on failures.

### Remaining candidate

1. **Manual SQL string assembly in report/query paths where Query Builder can replace it.**
