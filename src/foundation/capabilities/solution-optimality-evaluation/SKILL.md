---
name: solution-optimality-evaluation
description: "`analysis-agent`/`task-agent`/`review-agent`: use when feasible solutions differ in hard constraints, total-change cost, or reversibility; skip when no material option remains."
---

# solution-optimality-evaluation

## Registry Trigger

**Use when**

- Feasible options differ in hard constraints, resource behavior, total-change cost, ownership, or reversibility.
- Claims of simpler, faster, cheaper, safer, or more future-proof require comparison with the strongest feasible alternative.

**Do not use when**

- Code or structure existence is unresolved; use `minimal-correct-implementation`.
- Architecture-wide placement is unresolved; use `architecture-tradeoff-analysis`.
- Algorithm or data-structure selection is unresolved; use `algorithm-data-structure-selection`.
- Language or runtime selection is unresolved; use `language-runtime-selection`.
- The language and runtime are fixed while runtime behavior is open; use `language-performance-safety`.
- Package or dependency choice is unresolved; use `package-dependency-management`.
- The open decision is a technology-stack commitment involving a framework, platform, datastore, infrastructure component, or managed service; use `technology-stack-selection`.
- A measured bottleneck is unresolved; use `profiling`.

## Skill Role

Choose feasible solutions by hard constraints, total-change cost, reversibility, option value, and evidence limits, using accepted specialist conclusions as fixed inputs.

## High-Value Rules

- Define the problem, acceptance, hard constraints, non-goals, and decision owner without preferring a mechanism.
- Reject candidates with unproved correctness, compatibility, security, policy, or operability constraints; weighted scores cannot override hard-constraint gaps.
- Compare the selected option with the strongest feasible simpler or established alternative and any candidate capable of changing the decision.
- Compare total-change cost across implementation, coexistence, testing, release, operation, incidents, exit, deletion, and opportunity cost.
- Evaluate reversibility through rollback, migration, coexistence, information loss, and staged learning's option value under uncertain or costly exit.
- Compare combined solutions using accepted specialist conclusions as fixed facts and constraints, exposing evidence limits without reopening specialist selection.
- Record plausible omissions from discriminating resource and maintenance comparisons as decision limits.
- Require performance claims to identify workload, expected and worst cases, budget, environment, and measurement limits.

## Anti-Patterns

- Deferred cost or optimization has no owner, reopening condition, rollback clue, or residual-risk statement.

## Stop Conditions

- Route architecture-wide tradeoffs to `architecture-tradeoff-analysis`, existence to `minimal-correct-implementation`, and placement to `implementation-structure-design`.
- Route algorithm or data-structure selection to `algorithm-data-structure-selection`.
- Route language or runtime selection to `language-runtime-selection`, and fixed-runtime behavior to `language-performance-safety`.
- Route package or dependency choice to `package-dependency-management`.
- Route technology-stack commitments involving a framework, platform, datastore, infrastructure component, or managed service to `technology-stack-selection`.
- Route budgets to `performance-budgeting`, disputed bottlenecks to `profiling`, and executable proof to `quality-test-gate`.

## Output Contract

- solution decision with hard-constraint screen, selected option, strongest rejected alternatives, total-change cost, reversibility and option value, comparative proof and limits, reopening condition, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Feasible solution candidates differ in hard constraints total-change cost reversibility resource behavior or evidence limits | One solution is fixed by current constraints and no material alternative can change the decision | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
