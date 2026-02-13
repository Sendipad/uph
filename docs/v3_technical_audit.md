# UPH v3 Branch Technical Audit

## 1) Executive Summary

The v3 branch introduces substantial functionality (duplicate scanning, merge orchestration, smart caching, and dashboard APIs), but it currently carries **several high-risk production issues**:

- **Transaction safety and concurrency hazards** in merge/update workflows (`frappe.db.commit()` inside service/controller methods and request-cycle writes).  
- **Permission exposure** in multiple whitelisted APIs that return potentially sensitive cross-doctype data without explicit read checks.  
- **Upgrade fragility** from runtime monkey-patching ERPNext internals and MariaDB-specific patch SQL.  
- **Performance regressions at scale** due to N+1 patterns and “load-all then paginate” behavior in dashboard/data-quality endpoints.

Overall posture: **functional but risky for high-volume or multi-tenant ERPNext deployments** without targeted refactoring.

---

## 2) Critical Risks (High / Medium / Low)

### High

1. **Manual transaction commits inside domain logic can break request/worker atomicity.**  
   - `on_change_party_master_update_transactional_document_types()` calls `frappe.db.commit()` directly.  
   - `PartyMergeService.merge()` also performs an explicit `frappe.db.commit()`.  
   - These patterns can partially persist side effects before outer workflows finish and make rollback behavior harder to reason about.  
   - Files/functions: `uph/party/controllers/party.py::on_change_party_master_update_transactional_document_types`, `uph/party/controllers/party_merge_service.py::PartyMergeService.merge`.

2. **Permission bypass surface on whitelisted endpoints (data disclosure risk).**  
   - `get_party_master_details_with_parties`, `get_transaction_health`, `get_party_health_detail`, and `get_potential_duplicates` expose large record sets / metadata but do not consistently enforce per-doctype permission gates in-function.  
   - Some functions check existence only, not read authorization of underlying docs.  
   - Files/functions: `uph/party/controllers/party.py::get_party_master_details_with_parties`, `uph/party/controllers/transaction_health.py::{get_transaction_health,get_party_health_detail}`, `uph/party/page/data_quality_dashboard/data_quality_dashboard.py::get_potential_duplicates`.

3. **Core monkey-patching in request path (upgrade breakage + concurrency side effects).**  
   - `get_party_details()` temporarily replaces `erpnext.accounts.party.get_default_contact` at runtime.  
   - This is brittle across ERPNext upgrades and unsafe under concurrent execution models.  
   - File/function: `uph/party/controllers/party.py::get_party_details`.

4. **Broken hook asset references (runtime client errors).**  
   - `hooks.py` references `public/js/erpnext/sales_invoice.js` and `public/js/erpnext/payment_entry.js`, but these files are absent in repo.  
   - File/functionality: `uph/hooks.py::doctype_js` with missing files under `uph/public/js/erpnext/`.

### Medium

1. **Race conditions in “single default party per PM” logic.**  
   - `set_party_as_default_for_party_master()` reads existing defaults then updates/saves multiple docs without locking/unique enforcement, so concurrent requests can leave multiple defaults set.  
   - File/function: `uph/party/controllers/party.py::set_party_as_default_for_party_master`.

2. **Cache consistency risk after write-heavy flows.**  
   - Cache invalidation is uneven (`SmartCache` updated/invalidation in some paths, skipped in others), especially around merge/relink and bulk updates.  
   - File/functions: `uph/party/controllers/cache_utils.py`, `uph/party/controllers/party_merge_service.py`, `uph/party/controllers/queries.py`.

3. **DB portability risk in patching (MariaDB-only metadata SQL).**  
   - `add_indexes.py` introspects `information_schema.statistics` and uses `DATABASE()`, which is not PostgreSQL-compatible.  
   - File/function: `uph/patches/add_indexes.py::execute`.

### Low

1. **Over-broad wildcard hooks add steady request overhead.**  
   - `doc_events['*']` runs smart wrappers on `before_validate`, `validate`, and `on_change` for all doctypes, relying on early-exit for containment.  
   - File: `uph/hooks.py::doc_events`.

2. **Fat controller complexity and mixed responsibilities.**  
   - `party.py` and `party_master.py` combine validation, data enrichment, async orchestration, cache updates, and utility behavior, reducing maintainability/test isolation.  
   - Files: `uph/party/controllers/party.py`, `uph/party/doctype/party_master/party_master.py`.

---

## 3) Frappe Anti-Patterns Found

1. **Monkey-patching core ERPNext methods**  
   - `erp_party.get_default_contact` reassigned inside `get_party_details()`.  

2. **Business logic in hooks/controller lifecycle methods**  
   - Large validation and side-effect logic in `validate_party_master_on_document_types`, `validate_party_master_on_target_party_type`, `PartyMaster.before_save/on_update`.

3. **Heavy DB writes in request cycle**  
   - `set_party_as_default_for_party_master` writes multiple docs synchronously.  
   - `PartyMaster.on_update` may create Contact/Address on regular saves.

4. **Explicit commits in service/controller logic**  
   - `frappe.db.commit()` used in `party.py` and merge service; should rely on framework transaction boundaries or after-commit jobs.

5. **Tight coupling across modules**  
   - Controllers import each other bidirectionally (`party.py`, `queries.py`, `cache_utils.py`, merge service), making behavior difficult to test/migrate independently.

---

## 4) Performance Issues

1. **N+1 load in dashboard aggregation**  
   - `get_party_master_dashboard_info()` loops parties and calls ERPNext `get_dashboard_info()` per party. On large PM trees this can become expensive quickly.

2. **Load-all-then-paginate anti-pattern**  
   - `get_unlinked_parties()` pulls all unlinked records (`limit_page_length=0`) across doctypes, then sorts/paginates in Python.

3. **Duplicate detection memory/CPU pressure for >100k records**  
   - Duplicate endpoints scan all leaf Party Masters and do in-memory block processing; blocking helps, but hot prefixes remain O(k²).

4. **History stats endpoint executes repeated per-party aggregations**  
   - `get_party_master_history_stats()` issues several aggregate queries per linked party plus raw SQL for journal entries.

5. **Potential missing composite indexes on voucher filters**  
   - Repeated filters by `(party_master, docstatus, posting_date/company)` appear across duplicate checks and health queries.

---

## 5) Refactor Recommendations

1. **Introduce application service boundaries**  
   - Extract transaction-safe services: `PartyLinkService`, `DuplicateService`, `DashboardReadService`, `MergeService` (already present, but still too DB/transaction-heavy).

2. **Remove monkey patching and use deterministic enrichment pipeline**  
   - Wrap ERPNext `get_party_details` output post-call without mutating module-level functions.

3. **Replace in-request heavy writes with background jobs + `enqueue_after_commit=True`**  
   - Especially for bulk transactional updates after party_master changes and expensive recalculations.

4. **Centralize authorization guards for whitelisted read APIs**  
   - Add explicit `frappe.has_permission` checks for all touched doctypes + party master before returning data.

5. **Eliminate explicit `frappe.db.commit()` from controllers/services**  
   - Use savepoints where needed, but let framework own commit/rollback lifecycle.

6. **Split fat controllers**  
   - Move pure query logic to repository modules, side effects to services, hooks to thin delegates.

---

## 6) Index & Optimization Suggestions

1. **Add/validate composite indexes on high-frequency transactional filters**  
   - Candidate patterns:
   - `(party_master, docstatus, posting_date)` for Sales/Purchase invoices used in duplicate and health checks.
   - `(party_master, docstatus, company)` for dashboard/health scans.
   - `(party_type, party, docstatus)` on `Journal Entry Account` / `Payment Entry` lookup-heavy endpoints.

2. **Index duplicate-exclusion pair keys**  
   - Composite index on `Duplicate Exclusion (party_1, party_2, status)` to speed excluded-set reads/upserts.

3. **Prefix/search support for normalized names**  
   - Ensure index coverage for `Party Master.normalized_party_name` (especially prefix scans).

4. **Avoid MariaDB-specific index patch logic**  
   - Use Frappe DB abstraction or DB-specific branch logic for PostgreSQL compatibility.

---

## 7) Prioritized Action Plan

### Phase 0 (Immediate)
1. Remove explicit `frappe.db.commit()` calls from controller/service paths and move long operations to queued jobs.  
2. Add strict permission checks to all whitelisted dashboard/data endpoints.  
3. Fix `hooks.py` references to missing JS files.

### Phase 1 (Stabilization)
4. Replace monkey-patched `get_default_contact` logic with non-invasive enrichment.  
5. Add concurrency-safe default-party enforcement (DB constraint or transactional lock strategy).  
6. Add regression tests for merge/relink rollback and permission matrix.

### Phase 2 (Scale)
7. Rework unlinked/health/history endpoints to DB-level pagination and batch aggregates.  
8. Add recommended composite indexes and validate with EXPLAIN plans in production-like datasets (100k+ parties).  
9. Break `party.py` / `party_master.py` into smaller services for maintainability and upgrade safety.

---

## Notes on Audit Scope

This audit is based on static review of v3 branch source files and focused on transactional integrity, security posture, anti-patterns, and scalability characteristics in Frappe/ERPNext runtime behavior.
