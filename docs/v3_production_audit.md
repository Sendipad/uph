# v3 Branch Production Audit (Against `v3_blueprint.md`)

## 1) Executive Summary

**Health Score: 63 / 100 (Not production-ready yet for enterprise-scale rollout).**

Top risks:
1. **Security/permission gap in setup API** (`apply_setup_settings`) with no explicit Administrator/System Manager guard.
2. **Scalability bottlenecks** in duplicate detection and dashboard enrichment (N+1 lookups, full in-memory scans, repeated `db.exists` in loops).
3. **Blueprint drift**: duplicate architecture is split across `Potential Duplicate` and `Duplicate Exclusion`, while blueprint prescribes a single canonical duplicate table workflow.
4. **Concurrency risk in numbering** (`MAX + 1` allocation) can fail under parallel inserts.
5. **Heavy global hooks** (`*` validate/before_validate/on_change) remain an operational risk under high transaction throughput.

---

## 2) Blueprint Gap Analysis

| Blueprint Requirement | Current Status | Severity | Fix |
|---|---|---:|---|
| Setup wizard should enforce admin-first setup and govern all core setup options | **Partial**: `setup_finished` exists and is set, but setup API has no explicit role check and only applies subset of governance fields | High | Add explicit role permission guard in wizard methods; enforce/validate all governance fields in one atomic transaction |
| Numbering formats `####-######` / `##########` and configurable digits | **Partial**: settings include format + digits, but generator currently outputs concatenated numeric strings only | Medium | Implement formatter layer in numbering + rename/sync paths to honor selected format end-to-end |
| Parent-child prefix enforcement | **Partial/unclear**: config field exists; enforcement not clearly implemented in numbering validator path | High | Add deterministic validator using parent prefix and block rules during insert/update |
| Cross-role uniqueness with **DB-level unique index** | **Missing (DB-level)**: functional checks exist conceptually, but no explicit DB unique index for collisions across role projections | High | Add DB uniqueness strategy (composite unique on canonical link table or deterministic unique key) |
| Avoid shadow tables for duplicate status where possible | **Diverged**: both `Potential Duplicate` and `Duplicate Exclusion` are used, creating split state logic | Medium | Consolidate to single duplicate table lifecycle (`Detected/Dismissed/Merged`) with clear ownership |
| Dashboard should avoid heavy request-time aggregates; rely on cache lazy + background refresh | **Partial**: hourly refresh exists, but request path still computes totals and some endpoints do N+1 enrichments | High | Add strict cache-first API with TTL + lazy refresh fallback and remove heavy request-time counts |
| Scheduler: daily duplicate scan + hourly cache refresh | **Implemented** | Low | Keep, but align implementation with one duplicate model and robust cache invalidation |
| API layer organization (`uph.party.api.dashboard`, `uph.party.api.duplicates`) | **Missing exact structure** | Low | Optional refactor to blueprint module layout for maintainability/governance |
| `normalized_party_name` indexed | **Missing explicit index evidence** on Party Master field itself | High | Add index migration on `normalized_party_name` |
| Setup wizard language/tree template behavior | **Partial**: template selection exists; language assignment and translation inheritance behavior not fully enforced in backend | Medium | Persist language selection in setup flow and enforce/propagate localization rules |

---

## 3) Critical Bugs

1. **Permission vulnerability in setup completion path**  
   `apply_setup_settings` is whitelisted and mutates singleton governance config without explicit Administrator/System Manager role check. This is a high-risk configuration integrity issue.

2. **Race condition in party number allocation**  
   Number generation uses `SELECT MAX(...) + increment` patterns. Under concurrent inserts this can collide; unique constraint will reject one transaction, causing intermittent failures and possible user-facing retry storms.

3. **Reset path bug in party type setup helper**  
   In `setup_party_types_table(reset=True)`, code attempts `d.update(row)` where `d` is a string from `party_types` list; this will raise an exception if that code path executes.

4. **Duplicate-state fragmentation bug risk**  
   One scheduler path writes `Potential Duplicate`, another scanner/service path writes `Duplicate Exclusion` with status lifecycle. This can create inconsistent dashboard counts and review actions.

---

## 4) Anti-Patterns

1. **Global wildcard hooks on all DocTypes/events**  
   Hooking `*` on `validate`, `before_validate`, and `on_change` is expensive and operationally fragile, even with early-exit checks.

2. **Service-layer over-abstraction vs blueprint guidance**  
   `party_merge_service.py` and duplicate pathways introduce layered orchestration not aligned with “controller-centric, Frappe-native minimal” guidance.

3. **N+1 query patterns in dashboard duplicate listing**  
   Duplicate list retrieval does per-row Party Master name fetches.

4. **Mixed data ownership for duplicates**  
   Maintaining both `Potential Duplicate` and `Duplicate Exclusion` for similar lifecycle semantics increases complexity and defect surface.

5. **Raw SQL overuse with dynamic table interpolation**  
   Several paths rely on raw SQL where query builder + constrained metadata would be safer and more portable.

---

## 5) Scalability Risks (100k+ records)

1. **Duplicate scan memory and query pressure**
   - Full non-group Party Master load in memory.
   - Nested comparisons per block.
   - `db.exists` checks in inner loops (scheduler path).

2. **Dashboard and health APIs are not fully cache-first**
   - Request-time totals still computed in some endpoints.
   - Health computations aggregate Python-side collections before pagination.

3. **Broad hook footprint under transaction-heavy workloads**
   - Wildcard hooks execute for every DocType mutation lifecycle event.

4. **Index strategy incomplete for intended query patterns**
   - Missing/unclear index on `normalized_party_name`.
   - No explicit composite uniqueness for duplicate pair (`party_1`, `party_2`).

5. **Cache invalidation inconsistency**
   - Different modules use different cache keys; some invalidations may miss active keys, causing stale dashboard data.

---

## 6) Refactoring Recommendations (File-Level)

### High priority
- **`uph/party/page/setup_wizard/setup_wizard.py`**
  - Add explicit `System Manager`/`Administrator` authorization checks on all mutating endpoints.
  - Validate input schema and enforce complete governance settings atomically.

- **`uph/party/doctype/party_master/party_master.py`**
  - Replace `MAX + 1` numbering with transactional sequence/locking strategy.
  - Fully implement formatting layer for dash/concatenated modes.
  - Add strict parent-prefix enforcement validator tied to settings.

- **`uph/tasks.py` + `uph/party/controllers/duplicate_scanner.py` + `uph/party/doctype/duplicate_exclusion/*`**
  - Choose one canonical duplicate lifecycle table.
  - Remove duplicate write paths and unify scheduler job to one implementation.
  - Add composite unique index (`party_1`, `party_2`) and indexed status/score fields.

- **`uph/party/page/data_quality_dashboard/data_quality_dashboard.py`**
  - Replace per-record lookup with batched join/get_all IN query.
  - Enforce cache-first stats response with lazy warm fallback.

### Medium priority
- **`uph/hooks.py`**
  - Reduce wildcard hooks; register targeted DocType hooks only.

- **`uph/patches/add_indexes.py` and migration strategy**
  - Add explicit index for `Party Master.normalized_party_name`.
  - Add duplicate-pair and status indexes for detection tables.

- **`uph/party/doctype/party_master_settings/party_master_settings.py`**
  - Fix `setup_party_types_table(reset=True)` bug (`d.update(row)` on string).
  - Strengthen immutable governance contract after setup completion.

---

## 7) Production-Ready Roadmap

### Immediate (0–2 weeks)
1. Patch setup API permissions and input validation.
2. Fix numbering race condition (transaction-safe allocator).
3. Consolidate duplicate data model to one table and one scanner path.
4. Eliminate dashboard N+1 duplicate enrichment.
5. Add missing critical indexes (`normalized_party_name`, duplicate pair composite).

### Stabilization (2–6 weeks)
1. Replace wildcard hooks with targeted hooks and benchmark transaction latency.
2. Make dashboard strictly cache-first with explicit TTL/lazy refresh contract.
3. Add concurrency tests (parallel create/rename/merge), large-data scan tests, and cache consistency tests.
4. Align module boundaries to blueprint API layout for long-term maintainability.

### Optimization (6+ weeks)
1. Introduce chunked/background duplicate scan with persisted checkpoints.
2. Add observability: job duration, cache hit ratio, hook latency, duplicate scan throughput.
3. Query-plan validation for 100k+/1M records with index tuning and composite key refinement.
4. Formalize data-governance migration playbooks (versioned settings, controlled rollout toggles).

---

## Final Readiness Verdict

**Not yet production-ready for enterprise-scale deployment.**

The branch has a strong foundation and many implemented components, but current gaps in security hardening, duplicate-model consistency, concurrency safety, and scalability must be addressed before go-live.
