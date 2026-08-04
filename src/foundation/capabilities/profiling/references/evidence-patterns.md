# Profiling Evidence Patterns

Load this reference when closing hypothesis, representative-comparison, bottleneck, re-profile, resource/cost-transfer, overhead, correctness, or sensitive-artifact claims. Keep it as an evidence map, not a profiler catalog.

| Claim | Minimum fresh evidence | Proof limit |
| --- | --- | --- |
| Hypothesis is testable | User/operational symptom, suspected resource or wait, competing cause, falsifying signal | A plausible hypothesis is not a confirmed bottleneck |
| Workload is representative | Request/data distribution, load shape, runtime/topology, dependencies, cache/startup state, configuration | Unobserved production shapes remain residual risk |
| Bottleneck is measured | Profile/trace/plan/snapshot/cost artifact, dominant contribution, owned source or configuration path | Secondary bottlenecks and other workloads remain unknown |
| Before/after is comparable | Matched source/config/data/workload/environment/settings, baseline, candidate, variance or noise account | Production contention and rare events are not inferred |
| Re-profile closes the change | Final measurement, changed dominant contribution, moved constraint, error/rejection result | Future growth and different workload mixes remain unknown |
| Resource or cost transfer is bounded | Affected memory/I/O/queue/egress/provider/unit-cost metrics and degraded outcomes | Unmeasured external or shared costs remain residual risk |
| Overhead is bounded | Instrumentation method/settings, observed overhead, load/duration boundary, blast radius, stop and cleanup result | Heisenberg effects outside the sampled conditions remain possible |
| Correctness is preserved | Output/state/error/required-work comparison, security/durability checks, rollback or containment | Profiling alone does not prove full compatibility or release safety |
| Artifact lifecycle is owned | Captured fields, minimization/redaction, permission, path or ephemeral boundary, retention/deletion/cleanup owner | Future captures and downstream copies are not covered |

Treat old incidents, dashboards, profiles, traces, plans, billing exports, prior claims, and generated reports as selectors until current source, workload, settings, final measurement, and owner evidence match. Mark evidence stale after changes to hot paths, data shape, dependencies, cache, concurrency, retries, runtime, instrumentation, pricing, or build artifacts.

For production capture or state-changing capacity/restart actions, require owner authority, blast-radius and stop limits, redaction, rollback or containment, and cleanup. Block closure when comparison is not representative, overhead is unknown, the bottleneck is not measured and re-profiled, correctness regresses, or artifact lifecycle is unowned.
