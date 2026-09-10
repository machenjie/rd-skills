# Indexing Query Optimization Checklist

- Name each target query and its latency or resource budget.
- Capture predicates, joins, sorting, grouping, pagination, and expected result size.
- Estimate cardinality, selectivity, skew, and tenant distribution.
- Match proposed indexes to predicate order, sort order, and covering needs.
- Identify write amplification, storage growth, and index build risk.
- Reject indexes lacking a named query or safe plan/telemetry evidence sufficient for the bounded decision.
- Use representative execution evidence when safe and available; otherwise use the accepted estimated-plan or bounded-telemetry fallback and state unmeasured behavior.
- Define regression tests, monitoring, and rollback or disable path.
