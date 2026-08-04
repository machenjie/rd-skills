# Backend Proactive Professional Triggers

Owner: `backend-change-builder` in `task-agent` implementation or accepted repair mode.
Load only when a changed backend path contains one of the signals below.
A review handoff may cite the trigger.
This reference does not authorize self-review or broaden the Task Capsule.

## Hidden-Risk Escalators

| Signal in the changed path | Required decision and evidence | Route only when triggered |
| --- | --- | --- |
| Resource, owner, account, user, or tenant identifier is resolved without an authoritative scope predicate. | Trace caller identity through every scoped access found; prove server-side owner/tenant/policy enforcement plus allowed and denied cases. Scan the same credible access pattern and disclose unsearched surfaces. | `permission-boundary-modeling`, `authentication-authorization`, `security-privacy-gate`; add `regression-testing` for a verified bug. |
| Retry, redelivery, webhook, scheduled work, or external callback can repeat a side effect. | Define logical idempotency scope, durable dedupe/result behavior, bounded retry, poison/terminal handling, and safe replay; prove a duplicate leaves one intended outcome. | `idempotency-retry-design`, `message-queue-design`, `async-job-design`, `reliability-observability-gate`. |
| Multiple writes, state-plus-event publication, or an external call can partially complete. | Name the atomic boundary and commit/effect order; prove rollback, compensation, Saga, reconciliation, or explicit partial-success behavior through a failure case. | `transaction-consistency`, `data-side-effect-flow-tracing`, `domain-impact-modeler`, `data-api-contract-changer` when contracts/data change. |
| Catch/default fallback converts failure to null, empty, false, a default object, or apparent success. | Define whether fallback is approved product behavior or a typed failure; preserve correlation and a safe diagnostic signal, client outcome, and negative test. | `logging-error-handling`, `observability`, `failure-contract-design`, `quality-test-gate`. |
| Business vocabulary or policy is placed in `utils`, `common`, `helpers`, or another shared bucket. | Identify the semantic owner and search existing reuse. Owner-internal placement stays with `implementation-structure-design`. Prove visibility, consumers, test owner, and deletion path. If module ownership, public surface, or dependency direction changes, stop implementation. Route Analyzed Work to `architecture-impact-reviewer` with `module-boundary-design`. | Use `implementation-structure-design` only while the established module boundary stays fixed. |
| Public DTO, enum, error/status, pagination/filter/sort, event/webhook, or generated-client shape changes. | Inventory consumers and old/new behavior; prove compatibility, generated artifacts, contract tests, migration/deprecation, docs, rollout, and rollback as applicable. | `data-api-contract-changer`, `version-compatibility`, `contract-testing`, `consumer-impact-analysis`, `change-documentation-gate`. |
| Worker/consumer/job chain lacks an explicit claim, ack/commit, retry/terminal, replay, progress, or failure signal. | Define validate/claim/dedupe/effect/status/ack order, shutdown/cancel behavior, lag/failure visibility, and operator replay/quarantine; prove a forced failure and duplicate. | `async-job-design`, `message-queue-design`, `idempotency-retry-design`, `reliability-observability-gate`. |
| Permission, money, ledger, billing, subscription, transfer, delete/export, admin, or other sensitive mutation is irreversible or hard to repair. | Prove actor/action/scope authorization, required reauthentication/approval/confirmation, audit integrity, reconciliation or rollback/compensation, explicit irreversibility acceptance, and release owner. | `security-privacy-gate`, `delivery-release-gate`, `permission-boundary-modeling`, `change-documentation-gate`. |

## Mode And Proof Boundary

The task agent records only triggered decisions in its implementation handoff.
It runs mapped validation after the final edit.
It sends the actual diff and evidence to an independent reviewer.
Source search does not prove unknown entry points, deployed policy, broker or provider behavior, production replay, external consumers, or audit immutability.
Name those limits instead of loading every nearby capability.

Stop implementation when a triggered owner, invariant, compatibility policy, failure/repair path, or safe validation remains implicit. Do not turn this trigger catalog into a mandatory full-backend checklist.
