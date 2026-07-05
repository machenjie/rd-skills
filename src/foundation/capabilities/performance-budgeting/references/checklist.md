# Performance Budgeting Checklist

- Define the protected user or operational scenario.
- Choose metrics such as p95 latency, throughput, payload, bundle, CPU, memory, query count, or job duration.
- Record baseline, threshold, tolerance, data volume, and measurement environment.
- State whether budget failure blocks release or requires exception approval.
- Include budgets for frontend assets, API payloads, queries, jobs, and external calls where relevant.
- Track accepted regressions with owner, mitigation, and expiration.
- Map each changed endpoint, route, query, job, bundle, dependency, runtime growth surface, or cost driver to a budget, validator command/report, freshness, owner, rollback threshold, or residual risk.
