---
name: reliability-observability-gate
description: "Use `analysis-agent` to analyze recovery, SLO, capacity, degradation, and observability; `task-agent` to change resilience or telemetry; and `review-agent` to assess evidence. Skip self-review and no-runtime-impact work."
---

# reliability-observability-gate

## Role

- **Analysis mode (`analysis-agent`):** Select a failure model, owned objective, and recovery evidence.
- **Task mode (`task-agent`):** Apply accepted resilience or observability controls.
- **Review mode (`review-agent`):** Judge current control and recovery evidence.

## When To Use

- reliability or recovery risk; observability contract change

## Do Not Use

- no runtime behavior impact
- self review request
- unit test or local performance change with no runtime objective
- logging field-only change with no reliability decision
- release ordering only
- data correctness only

## Required Inputs

- acceptance; failure behavior
- **Analysis mode (`analysis-agent`):** affected runtime path, objective, telemetry, and recovery evidence.
- **Task mode (`task-agent`):** accepted control decision with failure, capacity, and recovery checks.
- **Review mode (`review-agent`):** changed runtime path with recovery and telemetry evidence.

## Professional Decision Rules

- Bind each objective to consequence, indicator, owner, and action.
- Match each resilience control to reachable failure and recovery behavior.
- Select only telemetry that proves an owned decision.

## High-Value Gotchas

- Retries can amplify overload after the original failure.
- A signal without an owned action is not operational proof.
- A backup artifact does not prove usable recovery.

## Execution Checklist

1. Trace the failure mode through consequence, dependency pressure, telemetry, and recovery ownership.
2. Select only the named objective, resilience, observability, capacity, or recovery References required by current risk.
3. Verify failure, degraded behavior, signal action, recovery, freshness, and proof limits.
4. **Analysis mode:** Return the selected objective and recovery decisions from current evidence.
5. **Task mode:** Apply accepted controls at the affected runtime boundary.
6. **Review mode:** Judge control, telemetry, recovery, and freshness evidence.
7. Stop when required reliability closure evidence is incomplete.

## Stop / Escalation Conditions

- Stop when required reliability closure evidence is incomplete.

## Output Contract

- failure model; resilience changes; reliability verdict.
- **Analysis mode (`analysis-agent`):** failure model; objective and recovery decisions; telemetry gaps; current evidence and freshness; proof limits; residual risk.
- **Task mode (`task-agent`):** resilience changes; rollout-watch signals; current post-edit evidence and freshness; proof limits; residual risk.
- **Review mode (`review-agent`):** reliability verdict; failure findings; current reviewed evidence and freshness; proof limits; unproven recovery behavior; residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | A bounded L2 mode needs compact checks for the triggered objective, telemetry, alert, dashboard, recovery, or runbook risk | The root contract is enough or mode-specific closure and targeted proof are required | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Closure depends on command/report artifacts, exit code, dashboard/alert proof, incident evidence, freshness, or proof limits | No reliability claim depends on runtime evidence or the body evidence contract is sufficient | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
| [index](references/index.md) | index | competing reliability observability gate references require dependency, conflict, or output-fragment selection | the reliability observability gate root or a task-named reference already resolves selection | analysis-agent, task-agent, review-agent | reference-selection |
| [reliability output and gates](references/reliability-output-and-gates.md) | targeted | L3-L5 work needs mode-specific closure and targeted gates for a selected objective, alert, resilience, telemetry, capacity/cost, recovery, or incident risk | A compact L1/L2 result is sufficient and no selected risk needs the extended proof contract | analysis-agent, task-agent, review-agent | gate-decision, residual-risk |
| [solution optimality](references/solution-optimality.md) | targeted | An owned reliability objective, alert strategy, capacity bound, telemetry design, or failure-control choice has a material alternative | No owned objective or operational decision is affected, or current platform policy and evidence already determine the bounded control | analysis-agent, task-agent, review-agent | failure-decision, residual-risk |
