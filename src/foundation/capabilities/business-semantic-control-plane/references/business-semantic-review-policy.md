# Business Semantic Review Policy

Review the final diff against the BSP and current source:

- New or changed business terms have object/vocabulary entries.
- New or changed rules have catalog records.
- Controller, mapper, UI, SQL, fixture, and migration changes do not hide rule authority.
- Status and workflow edits update allowed and forbidden transitions.
- Memory claims are accepted, rejected, stale, or not verified.
- Golden cases cover material business behavior and negative paths.
- Validation evidence is current after final material edits.
- Refactors preserve business semantics or explicitly route semantic change.

Findings should name the business claim, affected source path, expected BSP section, missing validation or owner review, and required repair.
