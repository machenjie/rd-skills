# Example Output

```markdown
## Task DAG

mode_selected: safety sequencing with multi-surface DAG

boundaries_inspected:
- Source: webhook handler, invoice service, idempotency repository conventions, migration folder.
- Tests: existing webhook duplicate-event tests and provider retry integration test.
- Registry/config/docs: existing feature flag and runbook references.
- Repository graph: accepted handler -> service -> repository edge after source check.
- Project memory: rejected prior note that duplicate webhooks are already deduped; no current repository evidence.
- Execution trajectory: no prior failed repair for this area.
- Not inspected: provider sandbox behavior; integration owner must confirm.

graph_memory_trajectory_judgment:
- Accepted: graph edge from webhook handler to invoice service after source inspection.
- Rejected: stale memory claiming dedupe exists.
- Not verified: provider sandbox retry behavior.

tasks:
- id: T1
  title: Add idempotency persistence
  owner_surface: backend/data
  goal: Persist provider event IDs with unique constraint before handler writes invoices.
  files_to_inspect:
    - db/migrations
    - src/billing/repositories
  allowed_files:
    - db/migrations/20260801_add_webhook_idempotency.sql
    - src/billing/repositories/idempotency_repository.ts
  dependencies: []
  parallel_group: null
  reuse_and_placement: Reuse existing repository pattern; no shared utils.
  validation_command: npm test -- billing/idempotency
  expected_output: duplicate event insert is rejected without invoice mutation
  rollback_notes: additive table can remain unused; down migration drops table only before production writes
  review_gate: data-api-contract-changer
  repair_route: data-migration-design
  safety_flag: false

- id: T2
  title: Use idempotency in webhook handler
  owner_surface: backend
  goal: Check idempotency before invoice mutation and preserve existing success response.
  files_to_inspect:
    - src/billing/webhook_handler.ts
    - src/billing/invoice_service.ts
  allowed_files:
    - src/billing/webhook_handler.ts
  dependencies:
    - T1
  parallel_group: null
  validation_command: npm test -- billing/webhook
  expected_output: duplicate webhook returns success without duplicate invoice mutation
  rollback_notes: disable handler path with existing feature flag
  review_gate: quality-test-gate
  repair_route: backend-change-builder
  safety_flag: false

- id: T3
  title: Add provider retry integration test
  owner_surface: tests/integration
  goal: Prove provider retry succeeds without duplicate invoice mutation.
  files_to_inspect:
    - tests/integration/billing
  allowed_files:
    - tests/integration/billing/provider_retry.test.ts
  dependencies:
    - T2
  parallel_group: null
  validation_command: npm test -- tests/integration/billing/provider_retry.test.ts
  expected_output: retry returns success and invoice count remains one
  rollback_notes: test-only change; revert test file if fixture blocks CI
  review_gate: quality-test-gate
  repair_route: integration-testing
  safety_flag: false

- id: T4
  title: Update webhook runbook
  owner_surface: docs
  goal: Document duplicate-event behavior and rollback flag.
  allowed_files:
    - docs/runbooks/billing-webhooks.md
  dependencies:
    - T2
  parallel_group: docs-after-handler
  validation_command: markdownlint docs/runbooks/billing-webhooks.md
  expected_output: markdownlint exits 0
  rollback_notes: docs-only revert
  review_gate: change-documentation-gate
  repair_route: documentation-generation
  safety_flag: false

dependency_graph:
- T1 -> T2: migration/data dependency.
- T2 -> T3: behavior dependency.
- T2 -> T4: documentation accuracy dependency.

parallel_groups:
- docs-after-handler: T4 may run while T3 is prepared; no shared files or validation inputs.

critical_path: T1 -> T2 -> T3
cycle_check: acyclic by inspection; no reverse dependency to T1.

changed_task_to_validation_map:
- T1 -> migration/repository unit test and schema review.
- T2 -> webhook duplicate-event unit test.
- T3 -> provider retry integration test.
- T4 -> markdownlint and documentation review.
- stale memory rejection -> current source inspection recorded.

plan_execution_consistency:
- Must compare final changed files against T1-T4 allowed_files before handoff.
- Validation is stale if any listed file changes after the command runs.

evidence_limits:
- Provider sandbox retry behavior was not inspected; integration owner owns residual risk.

next_gate: context-packaging for T1, then data-api-contract-changer review.
```
