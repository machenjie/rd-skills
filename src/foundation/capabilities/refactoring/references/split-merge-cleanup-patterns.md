# Split, Merge, And Cleanup Patterns

Use this reference when a refactor changes file/object/module shape, merges small files, removes code, expires compatibility branches, or claims complexity reduction. The goal is to prevent structural cleanup from hiding behavior change, dependency drift, or permanent compatibility debt.

## Split Decision Matrix

| Split target | Accept when | Reject when | Required evidence |
| --- | --- | --- | --- |
| Function extraction | Named behavior boundary, repeated logic, or test seam becomes clearer. | Extraction only shortens a method while increasing parameter coupling. | Before/after tests, extracted owner, rejected private-helper export. |
| Class/object split | Distinct lifecycle, invariant, collaborator set, or failure mode exists. | Split follows method names or creates anemic pass-through objects. | Owner map, invariant list, public behavior tests, rollback step. |
| File split | Each resulting file has a stable responsibility and test/change rhythm. | Later changes still edit all files together. | Import/export diff, caller search, dependency-direction check. |
| Module split | Dependency direction, deployability, ownership, or public contract improves. | Split creates cycles, duplicated adapters, or cross-module data leakage. | Module relationship type, architecture rule, contract compatibility evidence. |

## Merge Restraint Matrix

| Candidate | Merge only if | Keep separate when |
| --- | --- | --- |
| Small helper file | It has no independent owner, lifecycle, invariant, side effect, public contract, generated boundary, or focused test. | It protects adapter/client/gateway/repository/protocol boundaries, value-object invariants, strategy variants, public behavior tests, or dependency direction. |
| Tiny policy object | The policy is not independently named by domain, config, tests, or callers. | It expresses an authorization, pricing, validation, routing, retry, or state-machine rule. |
| Generated or barrel file | The source-of-truth and consumers remain unchanged after merge. | Generated clients, public exports, reflection, plugin loading, or package entry points depend on it. |
| Test fixture/helper | It is pure technical setup with one owner. | It carries business cases, golden data, tenant/security behavior, or cross-module contracts. |

## Cleanup Exit Matrix

| Cleanup target | Removal condition | Validation | Rollback limit |
| --- | --- | --- | --- |
| Dead code | Caller search, generated/reference scan, telemetry or not-present evidence. | Deletion diff, affected tests, import graph, generated artifact check. | Revert deletion while callers remain compatible. |
| Deprecated API | Consumer migration complete and sunset reached. | Consumer inventory, contract tests, docs/release note, old/new usage telemetry. | Keep expand phase until old consumers are gone. |
| Feature flag | Rollout complete, old behavior unused, owner approves removal. | Old/new behavior tests, config scan, cleanup issue, release/rollback note. | Restore flag only before cleanup deploy removes old path. |
| Compatibility branch | Expiry condition met and no active consumer needs dual behavior. | Branch coverage, caller search, generated-client diff, validation freshness. | Reintroducing branch after contract removal may require new compatibility work. |

## Review Sequence

1. Define the split, merge, or cleanup target and rejected alternatives.
2. Capture public behavior, import/export, side-effect, and dependency-direction evidence before movement.
3. Separate formatting, movement, import/export cleanup, deletion, and behavior changes.
4. Run the mapped validator after each material movement or deletion step.
5. Record before/after complexity evidence: branch count, collaborator count, dependency count, public API surface, directory density, or test clarity.
6. Stop pure-refactor closure when a schema, public API, config key, event, metric, generated client, or caller-visible error changes.

## Anti-Patterns

- Splitting by method name instead of owner, lifecycle, invariant, collaborator, side effect, or test boundary.
- Merging small files to reduce file count while hiding adapter, policy, generated-code, or public-contract boundaries.
- Deleting fallback or compatibility code without owner, expiry, telemetry, caller search, and rollback note.
- Reporting complexity reduction without before/after evidence or after making tests more coupled to private helpers.
- Treating generated reference updates as harmless when runtime registration or public exports changed.
