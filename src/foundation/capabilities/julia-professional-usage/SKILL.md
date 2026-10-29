---
name: julia-professional-usage
description: "For analysis/task/review agents: use for Julia dispatch, arrays, broadcasting, missing values, or reproducibility; skip generic and non-Julia work."
---

# julia-professional-usage

## Registry Trigger

**Use when**

- Julia dispatch, element types, array axes, broadcasting, views, or missing values affect behavior.
- Random execution or package environments determine a numerical result's reproducibility.

**Do not use when**

- Julia is only an unchanged dependency or file suffix.
- Generic data delivery or build configuration changes without Julia semantics.

## Skill Role

Protect Julia dispatch, array meaning, aliasing, missing-value handling, and reproducibility.

## High-Value Rules

- Bind dispatch and conversion to actual argument types, including abstract or mixed element types.
- Distinguish matrix operations from broadcasted element operations.
- Validate axes and singleton expansion against the intended physical or statistical shape.
- Trace views and aliases before in-place mutation.
- Define how `missing`, NaN, and invalid values affect predicates, reductions, and accepted results.
- Preserve the selected project, manifest, runtime, and random-state context for replay.
- Verify numerical properties separately from successful compilation or stable execution.

## Anti-Patterns

- Broadcasting produces a legal array with the wrong domain shape.
- A view is mutated as though it were an independent copy.
- `missing` reaches a Boolean decision without an explicit policy.
- The same seed is claimed to guarantee identical results across Julia releases.

## Targeted References

- No task-local Reference is indexed for this Skill.
