Selected stage: code-review.
Selected professional skill: data-middleware-change-builder.
Selected capabilities: sql-professional-usage.

Hidden risks: SQL dynamic query without parameterization; unsafe interpolation allows injection; tenant predicate missing from query test.

Inspected boundaries: request query input, sort allowlist, tenant predicate, parameter binding, SQL plan, index support, and integration test against the real engine.

Evidence required: parameterized query evidence; query plan and index evidence; tenant predicate integration test.

Output obligations covered: SQL parameterization evidence; validation evidence for query and tenant safety; what evidence proves and does not prove; residual data security risk owner.

Validation command: `python3 -m pytest tests/integration/test_account_search_sql.py` (not run in fixture; expected outcome is parameterization, allowlist, tenant isolation, and query plan evidence).
What evidence proves: the inspected SQL path does not interpolate request input and preserves tenant boundaries for covered cases.
What evidence does not prove: production cardinality, lock contention, all tenants, or all future sort fields.

Residual risk: production query skew needs plan sampling; owner: security-privacy-gate.
Next gate: security-privacy-gate before merge.
