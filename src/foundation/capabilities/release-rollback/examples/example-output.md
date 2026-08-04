# Example Output

```markdown
## Release Recovery Decision

Release identity:
- Source revision, application artifact, configuration, additive schema state, feature control, provider configuration, and target environment are linked.

Compatibility and order:
- Earlier and later application versions both tolerate the additive schema and disabled control state.
- Provider configuration changes after compatibility proof and before bounded exposure.

Exposure and stop:
- Initial exposure scope follows current blast-radius policy rather than a fixed percentage.
- Payment failure, missing provider callbacks, and reconciliation divergence are watched against current baselines with a named stop authority.

Recovery:
- Disable exposure and the feature control, restore prior provider configuration, then redeploy the earlier artifact if compatibility remains valid.
- Leave additive schema state in place; data migration cleanup is a later forward-recovery decision.
- Reconcile in-flight provider actions and duplicate or missing callbacks before closing recovery.

Evidence limit:
- Current staged proof covers selected compatibility and signal paths; broader provider traffic and live recovery authority remain with the operational and delivery gates.
```
