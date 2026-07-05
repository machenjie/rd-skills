# Example Output

```markdown
## Release Rollback Plan

Mode selected:
- External-integration rollback with migration-sensitive release sequencing.

Source evidence:
- Current API deployment manifest, additive migration file, payment provider config change, feature flag definition, prior release runbook, and canary dashboard were inspected.

Changed surfaces:
- API code, payment provider config, additive database column, feature flag.

Release order:
- Apply additive migration.
- Deploy code with feature flag off.
- Enable provider config in staging, then production canary.
- Turn flag on for 5 percent of traffic.

Rollback triggers:
- Payment error rate above threshold for 10 minutes.
- Missing settlement webhook events.

Rollback actions:
- Disable feature flag.
- Restore previous provider config.
- Redeploy prior API only if flag disable does not recover.
- Leave additive column in place and forward-fix cleanup later.

Graph/memory/execution validation:
- Prior runbook claim that provider config is self-service is accepted because current provider admin docs and deployment checklist still show the same reversal path.
- Canary evidence proves the metric path is wired; it does not prove full-traffic provider behavior.

Changed release to validation map:
- API code -> smoke test and canary 5xx monitor.
- Provider config -> settlement webhook test and provider admin audit log.
- Additive column -> migration status query and old-code compatibility test.
- Feature flag -> safe-default test and flag propagation check.
```
