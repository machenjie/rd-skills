---
name: scientific-computing-extension
description: "For analysis/task/review agents: use for scientific model, solver, convergence, or reproducibility decisions; skip ordinary numeric formatting and CRUD."
---

# scientific-computing-extension

## Role

Apply model-validity and solver-evidence constraints while reusing established numerical error and representation methods.

## When To Use

- A scientific model, solver choice, convergence rule, or stochastic experiment determines accepted results.
- Units, physical assumptions, conserved quantities, or reproducibility affect a scientific conclusion.

## Do Not Use

- The task only formats numbers or performs ordinary CRUD without scientific inference.
- A numerical calculation has no model or solver-validity decision.

## Required Inputs

- Model assumptions, units, shape, boundary/initial conditions, solver applicability, and failure contract.
- Error budget, trusted reference or invariants, data/parameter provenance, random design, and environment.

## Professional Decision Rules

- Validate the modeled question and assumptions before evaluating solver output.
- Match solver preconditions to stiffness, constraints, smoothness, scale, and domain as applicable.
- Separate numerical error from model mismatch and measurement uncertainty.
- Treat convergence and termination reason as part of the result contract.
- Compare against analytical limits, reference solutions, conservation laws, or justified refinements.
- Record stochastic uncertainty using the actual sampling and dependence structure.
- Preserve data, parameter, code, dependency, and execution context needed to reproduce the claim.

## High-Value Gotchas

- A numerically stable solution can solve the wrong equations or use incompatible units.
- Normal process exit and a finite array do not prove convergence or scientific validity.

## Execution Checklist

1. Bind the scientific question to assumptions, units, and solver conditions.
2. Exercise invalid inputs, nonconvergence, and reference or conservation checks.
3. Report numerical accuracy, model validity, and stochastic uncertainty separately.

## Stop / Escalation Conditions

- Stop acceptance when the governing model, units, solver applicability, or failure meaning is unresolved.
- Escalate contradictions between converged output, physical constraints, and trusted reference evidence.

## Output Contract

- Return model/solver rationale, convergence and invariant evidence, reproducibility scope, uncertainty, and remaining validity limits.

## Targeted References

- No task-local Reference is indexed for this Skill.
