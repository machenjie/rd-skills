# Example Output

Change: Exclude archived projects from active search.

Source of truth: Project table status field.

Derived store: Search index receives `is_archived` flag.

Consistency: Search can lag for 30 seconds; UI must tolerate stale results.

Failure mode: Index update retry may replay; operation must be idempotent.

Verification: Query plan check, search reconciliation job metric, regression test.
