# R Shape, Missing Values, and Reproducibility

Load for vector recycling, dimensions, missing-value policy, or reproducible R execution.
Skip generic pipeline decisions that preserve R semantics.

## Decision Rules

- Match each vector or array axis to its named population or physical dimension.
- Validate lengths before recycling can align incompatible inputs.
- Inspect row and column selection for dimension dropping, including singleton results.
- Check integer, double, logical, character, factor, and class conversions at the actual boundary.
- Define whether missing values propagate, exclude observations, or require explicit failure.
- Distinguish `NA`, `NaN`, infinite values, and absent records in validation and reporting.
- Evaluate formula and function environments where delayed lookup can change an expression's meaning.
- Separate data mutation from environment capture when closures survive the current call.
- Preserve runtime, package environment, RNG kind, and seed with a replayable input.
- Compare numerical invariants and uncertainty separately from matching random draws.

## Failure Probes

| Probe | Required distinction |
|---|---|
| Incompatible vector lengths | Domain validation rejects unintended recycling |
| One-row or one-column subset | Required dimensions remain intact |
| Missing value in a comparison or summary | Population and missing-value policy stay explicit |
| Factor converted to numeric | Values retain intended meaning rather than internal coding |
| Captured variable changes before evaluation | Result follows the documented environment |
| Same seed with different RNG or package versions | Reproduction claim states environment differences |

## Source Limits

- Use manuals matching the selected R release; patched documentation is not a universal version contract.

## Sources

- [R language and data semantics](https://stat.ethz.ch/R-manual/R-patched/doc/manual/R-intro.html)
- [R random-number generation](https://stat.ethz.ch/R-manual/R-patched/library/base/html/Random.html)
