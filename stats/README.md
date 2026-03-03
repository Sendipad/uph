# Stats Branch Artifacts

This folder is used by the clone-stats GitHub Action.

- On the `develop` branch, the workflow writes `stats/clones.json` every run.
- The root README badge reads that JSON from the `develop` branch.

If you do not see recent data, trigger the **Update Clone Stats** workflow manually and wait for cache refresh.

> Note: GitHub's traffic API often returns `403 Resource not accessible by integration` when called with the default `github.token`. Set a repository secret named `TRAFFIC_TOKEN` (classic PAT with `repo` scope) for reliable updates.
