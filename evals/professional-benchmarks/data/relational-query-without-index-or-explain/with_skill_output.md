Selected stage: implementation-planning.
Selected professional skill: data-middleware-change-builder.
Selected capabilities: relational-database, indexing-query-optimization.

Hidden risks: relational query without index or explain; missing index or query plan evidence on large table; production cardinality not represented by dev data.

Inspected boundaries: `invoice_events` table owner, tenant filter, status filter, created_at sort, existing indexes, proposed composite index, write path cost, and production-like cardinality source.

Evidence required: query shape and expected cardinality; index strategy and EXPLAIN/ANALYZE evidence; residual production cardinality risk.

Output obligations covered: query and index evidence; validation evidence for query plan; what evidence proves and does not prove; residual data risk owner.

Validation command: `EXPLAIN (ANALYZE, BUFFERS) SELECT ... FROM invoice_events ...` (not run in fixture; expected outcome is indexed plan evidence against representative data).
What evidence proves: the inspected query has a justified plan for the declared predicates and sort.
What evidence does not prove: production lock timing, replica lag, long-tail tenant skew, or all reporting consumers.

Residual risk: production tenant skew needs sampled plan review; owner: data-middleware-change-builder.
Next gate: reliability-observability-gate if query latency budget is production-critical.
