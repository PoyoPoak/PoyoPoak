---
name: verify-profile
description: Use after changing scripts/, assets/, README.md or the workflow in the PoyoPoak profile repo, to confirm the dashboard still builds, renders, and keeps private data out.
---

# Verify the profile dashboard

1. **Tests:** `python3 scripts/test_stats.py` must print `ok`.
2. **Build with real data:** `GH_TOKEN=$(gh auth token) python3 scripts/stats.py`. It prints the stat totals; check they are non-zero. A `stack: site source unreadable` line means the peterluey.com parser fell back to the built-in list.
3. **Render:** screenshot `assets/dashboard.svg` with headless Chromium. Freeze the animation first by copying the file and replacing every `begin="<n>s"` with `begin="0s"`, otherwise the screenshot shows the blank boot screen. Check that no text runs past a box edge.
4. **Privacy:** `grep` the SVG for private repository names (`gh repo list PoyoPoak --visibility private --json name`). Names written by hand in `NOW` or `STATUS` (ShiftWize, CIDA) are expected; any other hit is a leak.
5. **Workflow:** after pushing, `gh workflow run stats.yml` and `gh run watch`. A missing `STATS_TOKEN` shows as a warning, not a failure.
