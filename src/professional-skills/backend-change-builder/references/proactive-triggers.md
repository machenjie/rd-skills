# Backend Proactive Professional Triggers

Scope: backend implementation or accepted repair only.
Load only when a changed backend path contains one of the signals below.
A review input may cite the trigger.
This reference does not authorize self-review or broaden the accepted task scope.

## Hidden-Risk Escalators

When the change affects untrusted input, identity, resource scope, or tenant scope, preserve validation and server-side authorization before disclosure or mutation.

| Signal in the changed path | Required decision and evidence | Capability boundary when triggered |
| --- | --- | --- |
| Resource, owner, account, user, or tenant identifier is resolved without an authoritative scope predicate. | Trace caller identity through every scoped access found; prove server-side owner/tenant/policy enforcement plus allowed and denied cases. Scan the same credible access pattern and disclose unsearched surfaces. | Authorization, permission-boundary, and security/privacy judgment; add recurrence proof for a verified bug. |
| Retry, redelivery, webhook, scheduled work, or external callback can repeat a side effect. | Define logical idempotency scope, durable dedupe/result behavior, bounded retry, poison/terminal handling, and safe replay; prove a duplicate leaves one intended outcome. | Idempotency, asynchronous delivery, queue/job lifecycle, and reliability judgment. |
| Multiple writes, state-plus-event publication, or an external call can partially complete. | Name the atomic boundary and commit/effect order; prove rollback, compensation, Saga, reconciliation, or explicit partial-success behavior through a failure case. | Transaction, side-effect flow, domain-invariant, and contract/data compatibility judgment. |
| Catch/default fallback converts failure to null, empty, false, a default object, or apparent success. | Define whether fallback is approved product behavior or a typed failure; preserve correlation and a safe diagnostic signal, client outcome, and negative test. | Failure-contract, diagnostic-signal, observability, and negative-test judgment. |
| Business vocabulary or policy is placed in `utils`, `common`, `helpers`, or another shared bucket. | Identify the semantic owner and search existing reuse. Keep placement owner-internal only while the module boundary remains fixed. Prove visibility, consumers, test owner, and deletion path. If module ownership, public surface, or dependency direction changes, stop implementation. | Local structure judgment only; architecture ownership and module-boundary decisions are outside this implementation boundary. |
| Public DTO, enum, error/status, pagination/filter/sort, event/webhook, or generated-client shape changes. | Inventory consumers and old/new behavior; prove compatibility, generated artifacts, contract tests, migration/deprecation, docs, rollout, and rollback as applicable. | Data/API contract, version compatibility, consumer-impact, contract-test, and documentation judgment. |
| Worker/consumer/job chain lacks an explicit claim, ack/commit, retry/terminal, replay, progress, or failure signal. | Define validate/claim/dedupe/effect/status/ack order, shutdown/cancel behavior, lag/failure visibility, and operator replay/quarantine; prove a forced failure and duplicate. | Async-job, message-delivery, idempotency, and reliability judgment. |
| Permission, money, ledger, billing, subscription, transfer, delete/export, admin, or other sensitive mutation is irreversible or hard to repair. | Prove actor/action/scope authorization, required reauthentication/approval/confirmation, audit integrity, reconciliation or rollback/compensation, explicit irreversibility acceptance, and release owner. | Security/privacy, permission-boundary, release approval, and affected-user documentation judgment. |

## Mode And Proof Boundary

The implementer records only triggered decisions in its implementation result.
It runs mapped validation after the final edit.
It sends the actual diff and evidence to an independent reviewer.
Source search does not prove unknown entry points, deployed policy, broker or provider behavior, production replay, external consumers, or audit immutability.
Name those limits instead of loading every nearby capability.

Stop implementation when a triggered owner, invariant, compatibility policy, failure/repair path, or safe validation remains implicit. Do not turn this trigger catalog into a mandatory full-backend checklist.
