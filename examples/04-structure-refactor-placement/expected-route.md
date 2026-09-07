# Expected Route

## Path

Analysis answers the user's explicit question about conflicting rounding rules
and ownership, then one Task implements only the supported extraction and runs
targeted validation. Analysis is justified by a decision that changes behavior,
not merely by unknown file locations or a multi-file change. No independent
Review is selected under the stated facts.

## Analysis Assignment

- Profile: `analysis-agent`
- Primary Professional Skill: `architecture-impact-reviewer`
- Layer 3 Skills: `module-boundary-design`, `architecture-tradeoff-analysis`
- Question: which calculation rules can share an owner without changing checkout,
  invoice, or refund semantics?
- Output: source-backed placement and preserved differences, relevant validation,
  and unresolved business decisions. Ask the user only if intended behavior cannot
  be established from current source and tests.

## Task Assignment

- Profile: `task-agent`
- Primary Professional Skill: `backend-change-builder`
- Layer 3 Skills: none
- Allowed scope: the existing calculation owners and adjacent tests; preserve
  intentional differences and do not introduce a generic shared utility without
  ownership evidence
- Verify: targeted characterization and regression tests for affected paths,
  including rounding and stored-total behavior

Keep one Task unless inspection establishes a real dependency or independently
useful implementation boundary. If no behavior-preserving extraction is supported,
report that conclusion instead of forcing a new abstraction.
