# Example Output

```markdown
## Profiling Report

Symptom: Export job p95 duration increased from 40 seconds to 140 seconds.

Baseline:
- 20,000-row tenant export in staging.
- CPU profile shows 62 percent time in row serialization.
- Heap profile shows allocation spike in per-row formatter creation.

Fix direction:
- Reuse formatter per export and stream rows in batches.

Verification:
- Re-run same tenant fixture.
- Target p95 under 55 seconds with unchanged output checksum.
```
