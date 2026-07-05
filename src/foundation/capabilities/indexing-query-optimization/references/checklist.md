# Indexing Query Optimization Checklist

- Name each target query and its latency or resource budget.
- Capture predicates, joins, sorting, grouping, pagination, and expected result size.
- Estimate cardinality, selectivity, skew, and tenant distribution.
- Match proposed indexes to predicate order, sort order, and covering needs.
- Identify write amplification, storage growth, and index build risk.
- Reject indexes that lack a named query or useful plan.
- Verify with execution plan, representative data, and slow query telemetry.
- Define regression tests, monitoring, and rollback or disable path.
