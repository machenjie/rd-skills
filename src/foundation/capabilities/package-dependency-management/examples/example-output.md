# Example Output

```markdown
## Dependency Decision

Change: Upgrade database driver from 3.8 to 3.9.
Justification: Fixes connection leak under cancellation.
Transitive Impact: Two patch-level changes, no new packages.
Security: No critical or high vulnerabilities; license remains MIT.
Lockfile: Updated by frozen install workflow.
Decision: Accept after integration test and rollback note.
```
