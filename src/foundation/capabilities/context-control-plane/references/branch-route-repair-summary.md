# Branch Route Repair Summary

Use this summary after branch switch, rebase, merge, route repair, or fixture regeneration changes the assumptions behind a route.

## Required Fields

- schema version and deterministic summary id
- trigger: repeated same-path retry, repair-after-review, route repair,
  branch switch, or compaction recovery
- abandoned or repaired route context
- current or replacement route context
- changed files and generated artifacts
- selected skills, capabilities, gates, and references before and after repair
- forbidden retries and reusable findings
- stale assumptions removed
- validators rerun, skipped, failed, or still required
- affected fixtures or benchmark records
- residual risk and next owner

The summary should be enough for review to see why the route changed without copying full diffs, logs, or repository graphs.
