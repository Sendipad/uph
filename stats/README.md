# Stats Branch Artifacts

This folder is used by the clone-stats GitHub Action.

- On the `stats` branch, the workflow writes `stats/clones.json` every run.
- The README badge reads that JSON from the `stats` branch.

If you do not see recent data, trigger the **Update Clone Stats** workflow manually and wait for cache refresh.

- If clone totals stay empty, add a `TRAFFIC_TOKEN` repository secret (classic PAT with `repo` scope) so the workflow can access the traffic API reliably.
- `stats/clones.json` stores `count` (total clones in last 14 days), `uniques` (unique cloners in last 14 days), and `total_count` (cumulative clones tracked over time).
- `stats/clone_history.json` stores daily clone snapshots so cumulative totals survive the 14-day API window.


Troubleshooting:
- `401 Requires authentication`: the `TRAFFIC_TOKEN` value is invalid/expired.
- `403 Resource not accessible by integration`: the token does not have enough permission for the traffic API; use a **classic PAT** with `repo` scope from an account with repository access.
