# Example Output

```markdown
## Release Rollback Plan

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
```
