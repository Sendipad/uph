# Stats Branch Artifacts

This folder is used by the clone-stats GitHub Action.

- On the `stats` branch, the workflow writes `stats/clones.json` every run.
- The README badge reads that JSON from the `stats` branch.

If you do not see recent data, trigger the **Update Clone Stats** workflow manually and wait for cache refresh.
