# v3 Branch Code Review Findings

## Scope
Review target: latest v3 feature set implementing unlinked resolver + Party Issue governance workflows.

## High-risk bugs

1. **Non-scalable unlinked query path (loads full datasets then paginates in Python).**
   - `get_unlinked_parties` and `get_unlinked_transactions` call `frappe.get_all(..., limit_page_length=0)` and then sort/paginate in memory.
   - This can cause large memory spikes and slow response time in production with high-volume doctypes.

2. **Dashboard cache invalidation mismatch.**
   - `link_to_party_master` and duplicate scanner invalidate `uph:dashboard_stats`, but dashboard stats are actually read from many keys under `uph:stats:*`.
   - The wrong key invalidation causes stale cards after user actions.

3. **Duplicate scan is scheduled twice daily.**
   - Scheduler registers both `uph.tasks.run_full_duplicate_scan` and `uph.party.controllers.duplicate_scanner.enqueue_duplicate_scan` in the same `daily` event.
   - This effectively runs duplicate detection twice and may create avoidable worker pressure.

4. **Fuzzy suggestion collision bug.**
   - `get_unlinked_suggestions` stores candidates in `choice_map[norm] = p`.
   - If multiple Party Masters share the same normalized string, earlier records are overwritten and suggestions can return the wrong party.

## Anti-patterns vs v3 blueprint expectations

1. **HTTP request path still performs heavy counts/scans** instead of pre-warmed cache-only reads.
2. **Inconsistent cache-key strategy** (`uph:unlinked_count`, `uph:health_counts`, `uph:dashboard_stats`, `uph:stats:*`) increases stale-data risk.
3. **Workflow/API mismatch:** `dismiss_duplicate(reason=...)` accepts a reason but does not persist it, losing audit context.

## Enhancements

1. Shift unlinked and transaction list endpoints to SQL pagination per doctype + merged heap strategy, not full materialization.
2. Standardize cache invalidation helper (`invalidate_dashboard_stats()`) that clears all `uph:stats:*` keys touched by dashboard cards.
3. Persist issue actions (dismiss reason, merge note) in `details_json` and show these in list/detail views.
4. Add a compact "Issue lifecycle" badge + last action user/date in dashboard cards.
5. Add UX fast filters per tab (doctype, severity, owner, date range) and remembered tab state in local storage.
6. Add optimistic UI updates after dismiss/merge/link actions to reduce perceived latency.

## Suggested immediate fixes (small patch set)

- Replace `limit_page_length=0` calls in dashboard APIs with real `limit_start` / `limit_page_length` pagination.
- Remove one of the two daily duplicate scan schedules.
- Update invalidation points to clear `uph:stats:*` keys instead of `uph:dashboard_stats`.
- Store `reason` when dismissing duplicate issues.
