---
name: r-professional-usage
description: "For analysis/task/review agents: use for R vector shape, recycling, missing values, evaluation, or reproducibility; skip generic data and non-R work."
---

# r-professional-usage

## Registry Trigger

**Use when**

- R vector recycling, subsetting, dimensions, missing values, or type conversion affects an accepted result.
- Evaluation, random state, or dependency versions affect reproducibility.

**Do not use when**

- R appears only in an unchanged notebook or package inventory.
- Generic data transport or decimal accounting changes without R semantics.

## Skill Role

Protect R shape, value, evaluation, and reproducibility contracts.

## High-Value Rules

- Bind vector lengths, dimensions, names, and units to the domain before arithmetic or joins.
- Reject unintended recycling even when the language permits the operation.
- Preserve dimensions and class semantics through subsetting and conversion.
- Distinguish missing values, NaN, infinities, and absent observations according to the analysis contract.
- Inspect lazy argument evaluation and retained environments when effects or mutable state matter.
- Record RNG kind, seed, runtime version, and relevant package versions for reproducible work.
- Validate numerical accuracy independently from successful R evaluation.

## Anti-Patterns

- A valid recycled result silently aligns the wrong observations.
- Dropped dimensions change a matrix operation into vector behavior.
- Missing values disappear through a default filter without a stated population rule.
- A saved seed is presented as a complete cross-version reproduction contract.

## Targeted References

- No task-local Reference is indexed for this Skill.
