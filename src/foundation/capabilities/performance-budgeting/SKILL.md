---
name: performance-budgeting
description: "`analysis-agent`/`task-agent`/`review-agent`: use when latency, throughput, bundle, memory, CPU, query, rendering, or resource cost needs a budget; skip without performance risk."
---

# performance-budgeting

## Registry Trigger

**Use when**

- set latency throughput memory cloud cost query scan per feature cost and rendering performance budgets

**Do not use when**

- no task-local performance budgeting decision is required

## Skill Role

Define threshold authority, representative workload, changed-surface coverage, measurement integrity, risk-based enforcement, correctness guards, and exception removal. Exclude broader reliability and implementation decisions.

## High-Value Rules

- **Give each selected threshold an authority.** Derive it from the protected outcome, current contract or objective, measured baseline, resource limit, or approved cost boundary. An external benchmark alone does not set product policy.
- **Measure a representative workload.** Name request/data distribution, concurrency and arrival shape, device/runtime/topology, dependency behavior, cache or startup state, and expected growth that materially affect the decision.
- **Map changed surfaces to budgets.** Connect affected routes, endpoints, queries, jobs, payloads, dependencies, resource pools, and unit-cost drivers to explicit metrics, validators, owners, and release actions; exclude uninspected siblings from coverage.
- **Protect measurement integrity.** Report matched conditions, distributions, errors, rejections, variance, and noise rather than one convenient sample.
- **Choose enforcement from consequence and evidence quality.** Warning, blocking, abort, degradation, rollback, or follow-up are risk decisions; do not impose one gate mechanism across unrelated budgets.
- **Preserve correctness, security, and durability.** A faster or cheaper path fails when it changes accepted semantics, drops required work, weakens isolation, or hides errors; measure rejected and degraded outcomes with success.
- **Make exceptions explicit and removable.** Record authority, affected outcome, rationale, mitigation, revisit or expiry trigger, residual risk, and the evidence that removes the exception.

## Anti-Patterns

- Copy an external threshold, one convenient sample, or an average into policy without current authority, distribution, consequence, and owner evidence.
- Measure an easy synthetic path while omitting the changed surface, representative workload, saturation behavior, or incomparable before/after conditions.
- Pass a speed or cost gate by dropping work, hiding errors or rejections, weakening safety, or granting an exception without a removal contract.

## Stop Conditions

Escalate when a threshold lacks authority, the workload is unrepresentative, before and after evidence is incomparable, or the changed surface lacks a validator or release action. Also escalate when optimization weakens correctness or safety, capacity or cost risk can escape the measured boundary, or an exception lacks an owner and removal conditions.

## Output Contract

- authorized performance and unit-cost budget with representative workload, changed-surface metrics, measurement-integrity evidence, risk-based enforcement, correctness guard, and explicit removable exception path

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Competing threshold workload capacity or enforcement patterns remain viable | Current authority and representative measurements determine one budget | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Several changed surfaces scale drivers validators or exception decisions must close together | One measured surface has an authorized threshold validator and owner | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Threshold authority workload representativeness changed-surface coverage measurement integrity correctness exception removal or final-edit freshness claims need proof | Fresh evidence proves authority workload coverage measurement integrity correctness and exception removal for the changed surface | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
