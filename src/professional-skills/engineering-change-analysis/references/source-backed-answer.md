# Source-Backed Answer

For mode `source-backed-answer`, remain read/search-only and answer the
repository question without diagnosis or implementation preparation.

## Analysis Requirements

1. Bound the exact question and repository scope.
2. Find the owner and minimum relevant definitions, consumers, tests, contracts,
   configuration, documentation, or generated surfaces.
3. Separate observed facts from evidence-backed inference.
4. Resolve stale/conflicting evidence or expose uncertainty and consequence.

## Output Contract

Return one Markdown answer: `Question`; conclusion-first `Answer`; precise
`Source Evidence` for each material claim; `Inferences, Unknowns, and Proof
Limits`; and performed non-mutating `Validation or Next Lookup`.

Do not include an Engineering Brief, implementation plan, First Executable
Slice, Task Contract, Review Boundary, or Task DAG. Do not invent change
acceptance, execution work, or review work when the user asked only for an answer.
