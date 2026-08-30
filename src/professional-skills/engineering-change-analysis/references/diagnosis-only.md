# Diagnosis Only

Use this contract only when the selected mode is `diagnosis-only`. Remain
read/search-only and determine cause from bounded evidence; do not repair the
failure or convert the result into implementation preparation.

## Analysis Requirements

1. State the observed failure, expected behavior, reproduction or observation
   boundary, and relevant constraints.
2. Trace the causal path through the owning rule, state transitions, inputs,
   side effects, failure handling, and affected consumers only as evidence
   requires.
3. Separate observed facts, verified causal conclusions, plausible but unproved
   hypotheses, and unavailable evidence.
4. Use the smallest non-mutating validation that can confirm or falsify the
   cause, with freshness and proof limits stated explicitly.

## Output Contract

Return one Markdown diagnosis containing:

- `Problem`: observed and expected behavior plus the bounded scope.
- `Source Evidence`: file, symbol, test, trace, log, or command evidence tied to
  each material claim.
- `Verified Cause`: the proven causal chain; if cause is not proved, state that
  explicitly and report only bounded conclusions.
- `Unknowns and Proof Limits`: missing evidence, competing explanations, and
  what the performed checks cannot establish.
- `Validation or Next Diagnostic Step`: non-mutating validation performed or
  the smallest evidence-gathering step that would resolve the remaining gap.

Do not include an Engineering Brief, implementation plan, First Executable
Slice, Task Contract, Review Boundary, or Task DAG. Do not recommend a repair
as if it were authorized implementation work.
