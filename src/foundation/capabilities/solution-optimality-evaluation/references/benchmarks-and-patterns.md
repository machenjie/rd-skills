# Feasibility And Option Comparison

This matrix compares candidates that have a credible path to satisfying the decision scope; it does not manufacture alternatives for a trivial local choice.

## Comparative Decision Matrix

| Decision facet | Facts that distinguish candidates | Rejection or residual signal |
| --- | --- | --- |
| Hard constraints | Correctness, compatibility, security, policy, data, deployment, and operability obligations | A required constraint is unsupported, unverified, or delegated to an unowned mitigation |
| Failure behavior | Expected, boundary, partial, duplicate, cancellation, recovery, and worst-case outcomes | The happy path is comparable while failure semantics differ or remain unknown |
| Resource and workload | Input distribution, scale, frequency, CPU, memory, I/O, contention, throughput, tail latency, queueing, and growth bounds that matter here | An estimate or benchmark uses a mismatched workload, environment, or aggregation level |
| Total-change cost | Build, migration, coexistence, validation, release, operation, incidents, exit, deletion, and affected-owner effort | Entry cost is counted while recurring, transition, or exit work is omitted |
| Reversibility and option value | Rollback unit, coexistence, information loss, switching cost, staged learning, and reopening condition | A hard-to-reverse choice carries unresolved assumptions that a staged option could test |
| Ownership and maintainability | Decision owner, changed surfaces, on-call and recovery boundary, test seams, and deletion path | The candidate shifts work or risk to an owner who has not accepted it |
| Comparative proof | Current source facts, representative measurement, dated assumptions, sensitivity, rejected-alternative reason, and proof limits | The claim depends on reputation, stale evidence, false precision, or uninspected consumers |

## Comparison Limits

- Compare dimensions that can change this decision, with rationale for excluding any plausible adjacent bottleneck, failure path, or cost surface.
- Treat formulas, complexity classes, models, profiles, and benchmarks as scoped evidence whose inputs, environment, and unproved boundaries are named.
- Reopen the decision when a named constraint, workload distribution, cost assumption, support condition, or exit path changes materially.
