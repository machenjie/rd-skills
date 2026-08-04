---
name: profiling
description: "`task-agent`/`review-agent`: use when CPU, memory, I/O, database, network, rendering, or cost needs measured bottleneck evidence; skip without a profiling need."
---

# profiling

## Registry Trigger

**Use when**

- profile CPU memory IO database network rendering cloud cost unit economics and bottlenecks

**Do not use when**

- no task-local profiling decision is required

## Skill Role

Define the symptom, hypothesis, profiler selection, representative comparison, measured bottleneck, re-profile, resource transfer, overhead, and artifact lifecycle. Exclude performance budgets and implementation.

## High-Value Rules

- **Select evidence from the symptom and falsifiable hypothesis.** The measurement distinguishes compute, wait, allocation or retention, I/O, query, network, rendering, or unit-cost causes; familiarity alone is insufficient evidence.
- **Use a representative, comparable workload.** Match the request/data distribution, load shape, runtime/topology, dependency and cache/startup state, and relevant configuration before comparing baseline and candidate.
- **Optimize only a measured bottleneck.** Tie the dominant cost or wait to an owned source/configuration path, change the responsible constraint, and re-profile under matched conditions; report when the dominant constraint moves.
- **Account for resource and cost transfer.** A local latency/CPU gain can shift memory, I/O, queueing, egress, provider usage, rejected work, or unit cost elsewhere. Measure the affected system boundary and degraded outcomes.
- **Bound profiling overhead.** Record sampling/instrumentation effect, load and duration boundary, blast radius, stop condition, and cleanup; profiling that perturbs the system can invalidate its own evidence.
- **Preserve behavior, security, and durability.** Compare outputs, errors, state, required work, and protection boundaries alongside performance; a faster path that drops or changes required behavior is a defect.
- **Own sensitive artifact lifecycle.** Classify captured fields, minimize and redact collection, control access and storage, set retention/deletion or ephemeral cleanup, and prevent accidental persistence of traces, snapshots, queries, identifiers, or billing data.

## Anti-Patterns

- Select a familiar profiler or optimization before the symptom and hypothesis identify what evidence could falsify the suspected cause.
- Compare unmatched workloads or environments, report one improved metric without re-profiling, or ignore a new dominant bottleneck and shifted resource or cost.
- Capture sensitive or high-overhead production artifacts without authority, blast-radius and stop limits, redaction, accountable storage, and deletion or cleanup.

## Stop Conditions

Escalate unrepresentative comparison, unknown overhead, unauthorized or unstoppable production capture, unresolved artifact sensitivity/lifecycle, non-dominant bottlenecks, weakened protections, or changes to public contracts, schemas, external boundaries, capacity controls, or restart policy.

## Output Contract

- profiling evidence with symptom and hypothesis, representative comparable workload, measured bottleneck and re-profile, resource/cost transfer, overhead boundary, correctness guard, and owned sensitive-artifact lifecycle

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Competing profiler signal workload or bottleneck patterns remain viable | One authorized representative method directly tests the hypothesis and root rules resolve the decision | task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Several comparison overhead transfer correctness or artifact-lifecycle decisions must close together | One bounded measurement has comparable evidence an owner a stop path and no unresolved artifact lifecycle | task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Hypothesis representative comparison bottleneck re-profile transfer overhead correctness or sensitive-artifact freshness claims need proof | Representative matched final measurements correctness checks and owned artifact cleanup close the claims | task-agent, review-agent | evidence-record, proof-limit, residual-risk |
