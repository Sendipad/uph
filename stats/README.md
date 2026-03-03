# Stats Branch Artifacts

This folder is used by the clone-stats GitHub Action.

- On the `stats` branch, the workflow writes `stats/clones.json` every run.
- The README badge reads that JSON from the `stats` branch.

If you do not see recent data, trigger the **Update Clone Stats** workflow manually and wait for cache refresh.

- If clone totals stay empty, add a `TRAFFIC_TOKEN` repository secret (classic PAT with `repo` scope) so the workflow can access the traffic API reliably.
- `stats/clones.json` stores `count` (total clones in last 14 days), `uniques` (unique cloners in last 14 days), and `total_count` (cumulative clones tracked over time).
- `stats/clone_history.json` stores daily clone snapshots so cumulative totals survive the 14-day API window.
