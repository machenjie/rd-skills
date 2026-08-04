# Example Output

```markdown
## Recovery Decision

Failure scenario: operator deletion corrupts document metadata while object versions and encryption-key history remain available.

Recoverable state:
- Authoritative metadata and object versions.
- Encryption-key mapping and compatible application/schema release.
- Search projection rebuilt from restored authoritative state.

Objectives:
- Tolerated loss and outage come from the affected-tenant consequence and current dependency/volume estimate.
- The latest database-only exercise is insufficient for the combined object, key, and projection path.

Restore order:
- Fence document writes and select a consistent capture point.
- Restore key lineage, metadata, and object versions; start compatible code; rebuild search; reconcile counts and sampled document reads.

Evidence:
- Current artifact identity, key policy, schema lineage, and restore target are recorded.
- A scoped exercise proves metadata restore and key-backed document reads in the selected environment.

Residual boundary:
- Cross-region throughput, hidden export copies, and full incident-time coordination remain unproved and have named owners.
```
