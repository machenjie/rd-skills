# Scenario Decomposition Benchmarks And Patterns

Load this reference when one accepted behavior needs risk-based normal, alternate, edge, failure, abuse, recovery, or operational paths before acceptance or planning. Do not load it to force irrelevant categories into a simple bounded behavior.

## Coverage Selection

| Category | Trigger and required outcome | Route when depth is needed |
| --- | --- | --- |
| Normal/alternate | Approved actor reaches the primary or another allowed outcome under named preconditions. | `use-case-modeling`, `user-flow-modeling`. |
| Edge | Boundary, empty, max/min, stale, first/last, lifecycle, version, locale, or unusual but valid state changes the result. | `quality-test-gate` or the owning domain capability. |
| Failure | Validation, dependency, permission, concurrency, partial write, timeout, retry exhaustion, or contract rejection can occur. | `failure-diagnosis`, `transaction-consistency`, contract owner. |
| Abuse | A caller can replay, enumerate, flood, inject, probe privilege, or infer restricted data. | `security-privacy-gate`, `threat-modeling`. |
| Recovery | Retry, idempotent resubmit, undo, rollback, compensation, cleanup, reconciliation, or manual correction is required. | `idempotency-retry-design`, `state-machine-modeling`, reliability owner. |
| Operational | Support diagnosis, alert/audit, backfill, incident action, or release rollback is part of safe operation. | `reliability-observability-gate`, `delivery-release-gate`, `change-documentation-gate`. |

Each selected scenario names actor, precondition, stimulus, expected durable/user-visible outcome, unacceptable outcome, verification owner, criticality/blocking status, and evidence limit. An omitted applicable category needs a named owner/deferral; an inapplicable category needs no filler scenario.

For external calls, queues, jobs, payments, imports/exports, and notifications, distinguish timeout/unexpected schema/rejection/partial effect, duplicate stimulus, terminal state, and operator repair when applicable. For roles/tenants/support/machine actors, distinguish valid alternate from denied/abuse without leaking restricted facts.

## Evidence And Proof Limits

Use current requirements/use cases plus inspected source, tests, contracts, runbooks, and current incident/support signals. A scenario matrix is not executable proof. A source scan does not cover unknown paths. An undrilled runbook does not prove recovery. Local failure simulation does not prove provider or production behavior.

Reject success plus generic invalid input and abuse equated with malformed data.
Reject retry without a duplicate outcome and “support investigates” without an owned action.
Reject routing every gap to “engineering” and omitting release criticality.
Route newly exposed blockers to `requirement-clarification`.
Route stable pass/fail outcomes to `acceptance-standard-definition`.
Route executable layer selection to `quality-test-gate`.
