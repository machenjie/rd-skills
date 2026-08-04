# Performance Budgeting Evidence Patterns

Load this reference when closing threshold-authority, representative-workload, changed-surface, measurement-integrity, correctness, exception-removal, or final-edit freshness claims. Keep it as an evidence map, not a benchmark catalog.

| Claim | Minimum fresh evidence | Proof limit |
| --- | --- | --- |
| Threshold is authorized | Protected outcome, contract/objective/baseline/resource or cost source, consequence, owner approval | Future demand and policy changes remain unknown |
| Workload is representative | Request/data distribution, load shape, device/runtime/topology, dependency and cache/startup state, growth assumption | Unobserved production shapes remain residual risk |
| Changed surface is covered | Changed path-to-metric-to-validator map, owner and release action | Uninspected sibling paths and consumers are not covered |
| Measurement is comparable | Matched code/config/data/environment/state/window, instrumentation, repeated result or variance/noise account | Production contention and rare events are not inferred |
| Capacity or recovery is bounded | Saturation/queue/pool behavior, accepted/rejected/degraded work, downstream limit, recovery or drain result | A different spike or outage shape may behave differently |
| Unit cost is traceable | Owned cost unit, billing dimensions, retries/cache/egress/storage effects, scenario growth, approval boundary | Invoice accuracy and shared-cost allocation outside the inspected billing boundary are not proven |
| Correctness is preserved | Output/state/error comparison, required work accounting, security/durability checks, rollback or degradation result | Performance evidence alone does not prove full functional compatibility |
| Exception is removable | Authority, impact, rationale, mitigation, revisit/expiry trigger, residual risk, removal validator | Owner execution and future removal are not guaranteed |

Treat prior dashboards, traces, billing exports, load results, benchmark notes, task claims, and generated reports as selectors.
Accept them only when current source, configuration, telemetry, validator output, and owner evidence match the final edit.
Mark evidence stale after code, dependency, data-shape, workload, runtime-limit, retry, fan-out, cache, or instrumentation changes.
Also mark it stale after price-driver or generated-artifact changes.

For shared or production actions, record authority, blast-radius and stop limits, redaction, and cleanup or rollback.
Actions include load, queries, billing exports, capacity controls, feature flags, and release gates.
Record generated-artifact ownership when such an action produces one.
State unmeasured users, workloads, devices, data shapes, dependencies, and production effects as residual risk.
