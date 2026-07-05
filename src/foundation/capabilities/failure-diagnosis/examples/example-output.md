# Example Output

```markdown
## Failure Diagnosis Report

Symptom:
- Checkout requests intermittently returned 500 after release 2026.05.16.

Trigger:
- New provider timeout setting increased retry overlap during peak traffic.

Evidence:
- Error logs show duplicate payment finalization attempts.
- Metrics show spike in retry concurrency after config deploy.
- Reproduction succeeds with two delayed provider callbacks.

Root cause:
- Payment finalization was not idempotent for duplicate callback delivery.

Contributing factors:
- Integration test covered single callback only.
- Alert fired on 500 rate but not duplicate finalization attempts.

Fix:
- Add idempotency guard around finalization.

Regression prevention:
- Integration test for duplicate delayed callbacks.
- Metric and alert for duplicate finalization suppression.
```
