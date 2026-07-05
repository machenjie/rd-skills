# Benchmark Prompt

## Task

Consolidate only boundary-free small files without hiding real boundaries.

## Context

The starter repository has an `OrderCancellationService` plus four small files:
an external payment client adapter, a `CancellationWindow` value object with an
invariant, a `CancellationPolicy` with independent public behavior tests, and a
tiny private helper used only by the service. A previous review asked whether
the directory has too many small files.

Only the tiny private helper lacks an independent owner, lifecycle, invariant,
collaborator family, public contract, side-effect boundary, test boundary, and
change rhythm. The other small files are intentionally small boundary files.

## Requirements

- Inspect the service, adapter/client, value object, policy, imports, and tests.
- Merge only the tiny private helper into the owning service when behavior stays
  unchanged and navigation cost improves.
- Keep the external adapter/client separate because it owns side effects,
  protocol translation, retries, credentials, and error mapping.
- Keep the value object separate because it owns an invariant and public
  construction behavior.
- Keep the policy separate because it has an independent public behavior test
  boundary and current policy responsibility.
- Preserve import/export surfaces, public contracts, dependency direction, and
  behavior tests before and after the merge.
- Record a merge or rejected-merge rationale for each small file.

## Constraints

- Do not merge the adapter/client into the service.
- Do not merge the value object invariant into procedural service code.
- Do not merge a policy with independent behavior tests into orchestration.
- Do not reduce file count without boundary analysis.
- Do not hide side effects, public exports, or dependency direction.

## Deliverables

- Implementation Structure Plan with Small File Merge Decision entries for all
  four small files.
- Refactoring plan with `file_merge_refactor_plan`,
  `merge_restraint_decision`, `import_export_before_after`,
  `public_contract_preserved`, `dependency_direction_preserved`, and
  `behavior_test_before_after`.
- Code Clarity Maintainability Review with file navigation cost assessment and
  next-change location before/after.
- Public behavior tests proving the service, policy, value object, and adapter
  boundaries still behave as before.

## Completion Evidence

- Passing tests before and after the helper merge.
- Merge accepted only for the boundary-free private helper.
- Rejected-merge rationale for adapter/client, value object, and policy files.
- Import/export before/after evidence showing public contract and dependency
  direction were preserved.
- Review evidence that no automatic failure condition applies.
