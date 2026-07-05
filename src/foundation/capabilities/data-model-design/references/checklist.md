# Data Model Design Checklist

- Identify source-of-truth owner and domain responsibility.
- Define entities, documents, relationships, and cardinality.
- Capture invariants, uniqueness, constraints, and invalid states.
- Define lifecycle states, retention, archival, and deletion behavior.
- Map read and write query patterns, volumes, and latency needs.
- Define access control and tenant or owner scope.
- Identify indexes, denormalization, and rebuild needs.
- Assess migration, backfill, rollback, and data loss risk.
- Keep internal persistence separate from API and DTO contracts.
