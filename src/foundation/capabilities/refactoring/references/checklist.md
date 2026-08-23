# Refactoring Decision Checklist

- **Choose reviewable reversible steps.** Preserve a valid build and evidence boundary after each logical move, and separate renames, moves, extraction, rewiring, and deletion when combining them would hide causality.

Load this checklist for a structural transformation whose behavior-preservation evidence or review sequence is material. Do not load it for a trivial rename/formatting-only edit already covered by local validation.

1. Define the structural problem, target structure, and observable behavior that must not change.
2. Inventory public contracts, schema, configuration, metrics/logs, generated artifacts, integrations, ordering, and external effects.
3. Choose preparation and step size from classified behavior, consumer, data, security, and concurrency risk without fixed pull-request or commit counts.
4. Inspect current coverage and add characterization evidence before moving risky, disputed, or poorly understood behavior.
5. Name target owner, placement, visibility, dependency direction, and rejected shared/common/utils location.
6. Sequence rename, extract, move, inline, split, merge, and import/export cleanup as reviewable green transformations; include deletion only after `cleanup-deletion-governance` accepts readiness.
7. Separate formatting churn, mechanical movement, behavior change, schema migration, and optimization so each has its own evidence and rollback.
8. After each risky step inspect the diff, run the mapped validator, and stop rather than stacking further changes on a failure.
9. When a refactoring conclusion depends on structural comparison, record project-relevant branch, collaborator, dependency, public-surface, or test-clarity measures without a universal complexity threshold.
10. State rollback, unverified scope, residual owner, and explicit behavior-change exclusions.
11. Characterization captures current observable behavior, not ideal behavior; fix a known defect in a separate accepted behavior-change step.
12. For critical/public/shared boundaries, name consumer compatibility, migration/deprecation/removal, specialized reviewer, and handoff evidence.
