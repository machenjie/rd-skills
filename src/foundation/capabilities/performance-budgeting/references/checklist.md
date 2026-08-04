# Performance Budgeting Checklist

- Name the protected user, operational, contractual, safety, capacity, or unit-cost outcome and its decision owner.
- Record threshold authority, current baseline, changed objective, and the consequence of breach.
- Define representative request/data distribution, load shape, device/runtime/topology, dependencies, cache/startup state, and growth assumption.
- Map affected routes, endpoints, queries, jobs, payloads or bundles, dependencies, resource pools, and cost drivers to metrics and validators.
- Make before/after code, configuration, data, environment, warmup/state, and observation conditions comparable.
- Report distributions, errors, rejected/degraded work, variance, and measurement noise alongside the selected metric.
- Define capacity, saturation, queueing, retry/fan-out, recovery, and cost behavior where the changed path can amplify load.
- Select warning, blocking, abort, degradation, rollback, or follow-up from impact and evidence quality.
- Prove accepted behavior, security, durability, and required work remain intact after optimization.
- Record each exception's authority, rationale, affected outcome, mitigation, revisit/expiry trigger, residual risk, and removal evidence.
- State unmeasured users, workloads, devices, data shapes, dependencies, and production effects as residual risk.
