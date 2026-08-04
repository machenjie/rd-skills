# Source-Backed Answer

Use this contract only when the selected mode is `source-backed-answer`.
Remain read/search-only and answer the repository-dependent question without
turning the response into diagnosis or implementation preparation.

## Analysis Requirements

1. Restate the exact question and bound the repository scope needed to answer
   it.
2. Find the owning rule and the smallest relevant set of definitions, callers,
   consumers, tests, contracts, configuration, documentation, or generated
   surfaces.
3. Distinguish directly observed source facts from inferences and state the
   evidence behind each material conclusion.
4. Resolve conflicting or stale evidence when possible; otherwise expose the
   uncertainty and its consequence for the answer.

## Output Contract

Return one Markdown answer containing:

- `Question`: the bounded repository-dependent question answered.
- `Answer`: the direct conclusion first, calibrated to the available evidence.
- `Source Evidence`: precise file, symbol, test, contract, configuration, or
  documentation support for each material claim.
- `Inferences, Unknowns, and Proof Limits`: conclusions not directly stated in
  source, missing or conflicting evidence, and what the inspection cannot prove.
- `Validation or Next Lookup`: non-mutating check performed or the smallest
  targeted lookup needed if the answer remains conditional.

Do not include an Engineering Brief, implementation plan, First Executable
Slice, Task Skill, Review Skill, or Task DAG. Do not invent change acceptance,
task routing, or review work when the user asked only for an answer.
