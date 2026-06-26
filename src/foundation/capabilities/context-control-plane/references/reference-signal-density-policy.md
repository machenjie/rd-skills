# Reference Signal Density Policy

Selected references must have high signal for the current route. Prefer a short allow-list over loading every companion capability.

## Select When

- The reference contains a rule needed for the current stage, risk trigger, changed path, or output contract.
- The reference is required to verify selected/skipped reference behavior.
- The reference defines validation, privacy, compaction, repair, or benchmark evidence needed for closure.

## Skip When

- The reference only provides general background.
- The same rule is already covered by the loaded `SKILL.md`.
- The topic is out of scope for changed files and selected gates.
- Loading it would create context bloat without reducing residual risk.

Every skipped relevant reference needs a one-line reason. Missing skipped-reference rationale is itself a context-control defect.
