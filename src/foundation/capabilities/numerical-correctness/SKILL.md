---
name: numerical-correctness
description: "For analysis/task/review agents: use for numerical stability, error budgets, or floating-point proof; skip ordinary CRUD and decimal-only money rules."
---

# numerical-correctness

## Registry Trigger

**Use when**

- Numerical precision, conditioning, mixed precision, reductions, or stochastic variation can change an accepted result.
- Scientific, ML, graphics, or numerical-library behavior needs a trustworthy error oracle.

**Do not use when**

- The task changes ordinary CRUD, labels, or decimal money representation without a numerical algorithm.
- Shape and value representation are incidental, with no numerical correctness decision.

## Skill Role

Protect numerical meaning across input domains, algorithms, representations, and independent verification.

## High-Value Rules

- Bind inputs to units, dimensions, shape, valid ranges, and finite-value policy.
- Define error-budget allocation across input uncertainty, approximation, rounding, and accumulation.
- Distinguish ill-conditioned problems from unstable algorithms before selecting a repair.
- Choose absolute and relative tolerances from scale and the reference value, including behavior near zero.
- Inspect overflow, underflow, cancellation, and precision conversions through intermediate values.
- Preserve required invariants across reduction order, parallel execution, and mixed precision.
- Compare against an independent reference, analytic solution, or justified metamorphic relation.
- Bound reproducibility claims by seeds, algorithms, devices, versions, and nondeterministic execution.

## Anti-Patterns

- One global epsilon hides unit differences, near-zero errors, or large-scale drift.
- A stable result solves the wrong model or accepts invalid shape and non-finite inputs.
- Matching the implementation against itself substitutes correlation for an independent oracle.
- A seed or one backend result is presented as portable bitwise reproducibility.

## Stop Conditions

- Stop numerical acceptance when units, input domain, error budget, or an independent oracle remains unresolved.

## Output Contract

- Return input-domain decisions, allocated error, oracle comparison, reproducibility limits, and unverified numerical cases.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [error budget and oracles](references/error-budget-and-oracles.md) | targeted | tolerance, conditioning, reduction, mixed-precision, or numerical-oracle decisions | ordinary decimal accounting and changes without numerical computation | analysis-agent, task-agent, review-agent | decision-record, validation-plan, proof-limit |
