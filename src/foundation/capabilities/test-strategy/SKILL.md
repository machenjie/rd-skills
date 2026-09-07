---
name: test-strategy
description: "`analysis-agent`/`task-agent`/`review-agent`: use to recommend a risk-to-test evidence portfolio and omissions; skip test implementation, fixed-command, and release-verdict work."
---

# test-strategy

## Registry Trigger

**Use when**

- choose risk based proof portfolio test levels failure mechanisms oracles omissions and admissibility evidence

**Do not use when**

- one test level and command are already fixed or the task only implements tests or decides release readiness

## Skill Role

Select the smallest proof portfolio from mechanisms, consequences, surfaces, oracles, levels, omissions, and limits; exclude exact commands, cases, validation judgments, and release verdicts.

## High-Value Rules

- Map each risk to its mechanism, consequence, surface, oracle, and cheapest exercising level.
- Define mechanism-sensitive assertions and signals without taking entrypoint, coverage, or fallback ownership from `targeted-validation-selection`.
- Route release evidence to `delivery-release-gate`.

## Anti-Patterns

- Local success substituted for evidence of the test strategy contract.

## Stop Conditions

Stop on unresolved acceptance, consequence, surface, environment/fixture, oracle, or high-risk evidence owner. Repository checks prove only inspected paths and environments.

## Output Contract

- risk based test strategy decision with failure mechanisms oracles proof levels coverage obligations omissions command-signal requirements and admissibility limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Test levels layered proof assertion challenge or omission tradeoffs remain contested | One accepted portfolio covers each material failure mechanism | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Negative paths nondeterminism flaky containment omissions and risk tracing need multi-part closure | The accepted portfolio already closes those decisions | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Admissibility depends on fresh changed-path consumer command fixture or report evidence | No strategy-confidence claim awaits proof | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
