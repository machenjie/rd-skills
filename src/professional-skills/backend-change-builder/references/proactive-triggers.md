# Backend Proactive Professional Triggers

Owner: `backend-change-builder`.

Responsibility: define hidden-risk backend escalators that force route repair,
capability loading, and evidence collection before implementation, review, or
handoff. Load this reference when a backend change touches authorization,
tenancy, retries, async work, public contracts, transactions, irreversible
mutation, or AI-generated backend code.

## IDOR Or Tenant Leak

- **Signal:** A `resource_id`, `user_id`, `tenant_id`, account, order, invoice,
  asset, subscription, or permission query fetches by identifier without an
  ownership predicate, tenant filter, or policy call.
- **Hidden risk:** IDOR, tenant data leak, or object-level authorization bypass.
- **Required professional action:** stop treating the change as local; trace every
  resource access path, confirm the authoritative caller identity, and add denied
  cases before accepting the fix.
- **Route to:** `permission-boundary-modeling`, `authentication-authorization`,
  `security-privacy-gate`, and `regression-testing` for bug fixes.
- **Evidence required:** query or policy path showing owner/tenant enforcement,
  same-pattern search for sibling resource access, denied-case test, and residual
  risk for unscanned surfaces.

## Retry Or Queue Without Idempotency

- **Signal:** Retry, queue redelivery, cron, consumer, webhook ingest, scheduled
  job, or external callback lacks an idempotency key, dedupe store, DLQ, replay
  policy, or bounded retry.
- **Hidden risk:** duplicate side effects, poison message loops, retry storm,
  external rate-limit burn, or irreversible repeated mutation.
- **Required professional action:** define retry semantics before code closure:
  idempotency key scope, dedupe storage, backoff, poison-message route, and
  replay behavior.
- **Route to:** `idempotency-retry-design`, `message-queue-design`,
  `async-job-design`, `reliability-observability-gate`.
- **Evidence required:** duplicate-delivery test, dedupe lookup/write path,
  retry/DLQ configuration, replay procedure, and metric/log signal for failures.

## Multi-Step Write Without Atomicity Or Compensation

- **Signal:** A backend flow performs multiple writes, emits events after writes,
  calls external systems inside a write flow, or mutates multiple aggregates
  without explicit transaction, compensation, saga, or partial-success behavior.
- **Hidden risk:** inconsistent state, orphaned record, event without state,
  state without event, or manual production repair after partial failure.
- **Required professional action:** name the atomic boundary and define rollback,
  compensation, or saga behavior before implementation is complete.
- **Route to:** `transaction-consistency`, `data-api-contract-changer`,
  `domain-impact-modeler` when invariants or domain events are involved.
- **Evidence required:** transaction scope, isolation or lock decision,
  partial-failure test, compensation path, and rollback limitation owner.

## Silent Catch Or Default Fallback

- **Signal:** `catch`/`except` returns null, false, empty collection, default DTO,
  generic success, or silent fallback without typed error, structured log,
  correlation ID, or metric.
- **Hidden risk:** silent failure, corrupted downstream state, invisible incident,
  misleading client behavior, or impossible debugging.
- **Required professional action:** replace silent fallback with typed error and
  correlated observability, or document why the fallback is a safe product
  behavior with test coverage.
- **Route to:** `logging-error-handling`, `observability`,
  `code-clarity-maintainability`, `quality-test-gate`.
- **Evidence required:** error taxonomy, client-visible behavior, structured log
  fields, trace/correlation propagation, metric/alert implication, and negative
  test.

## Business Logic In Shared Utility

- **Signal:** New or changed `utils`, `common`, `helpers`, `shared`, or generic
  package contains terms such as user, tenant, order, payment, invoice, balance,
  subscription, asset, permission, policy, or role.
- **Hidden risk:** shared utility pollution, domain ownership drift, hidden
  dependency cycle, and future changes needing broad coordination.
- **Required professional action:** apply the reuse ladder and place business
  logic in the owning module, service, domain object, adapter, or local helper
  unless truly cross-domain with an owner.
- **Route to:** `implementation-structure-design`, `module-boundary-design`,
  `architecture-impact-reviewer` when a module boundary changes.
- **Evidence required:** reuse search, owner, rejected placement options,
  dependency direction, public/private visibility, deletion path, and test
  placement.

## Public Contract Change Without Compatibility Review

- **Signal:** New or changed public DTO field, enum value, validation error, API
  error code, status mapping, pagination behavior, filter, sort, webhook payload,
  or generated client shape lacks compatibility/deprecation/client analysis.
- **Hidden risk:** client contract break, generated client drift, mobile version
  skew, dashboard breakage, or hidden release coordination.
- **Required professional action:** route to contract review before closing the
  backend change and preserve old/new behavior until consumers are migrated.
- **Route to:** `data-api-contract-changer`, `version-compatibility`,
  `contract-testing`, `change-documentation-gate` when docs change.
- **Evidence required:** consumer list, compatibility decision, error/DTO docs,
  contract tests, deprecation or migration note, and rollback impact.

## Async Chain Without Worker Semantics

- **Signal:** Background task, queue consumer, scheduled job, webhook processor,
  event handler, or async chain lacks ack/nack boundary, retry policy, DLQ,
  replay mechanism, progress tracking, idempotency, or observability.
- **Hidden risk:** lost work, invisible failure, duplicate processing, poison
  message backlog, or manual recovery without evidence.
- **Required professional action:** define worker semantics and operational
  signals before implementation/release.
- **Route to:** `async-job-design`, `message-queue-design`,
  `idempotency-retry-design`, `reliability-observability-gate`.
- **Evidence required:** ack/nack point, retry/DLQ config, replay runbook,
  idempotency behavior, lag/failure metrics, and failure-path test.

## Irreversible Sensitive Mutation Without Audit Or Rollback

- **Signal:** Permission grant/revoke, balance, ledger, billing, subscription,
  asset transfer, delete, export, admin action, or other irreversible operation
  lacks audit event, re-authentication, approval, rollback, or explicit
  irreversibility acceptance.
- **Hidden risk:** unauthorized irreversible mutation, compliance evidence gap,
  financial inconsistency, or unreviewable incident recovery.
- **Required professional action:** require security and release gates before
  merge, including audit and rollback evidence or documented irreversible
  acceptance.
- **Route to:** `security-privacy-gate`, `delivery-release-gate`,
  `permission-boundary-modeling`, `change-documentation-gate` when runbooks or
  audit docs change.
- **Evidence required:** immutable audit record, authorization/re-auth path,
  approval or confirmation flow, rollback/compensation plan, and release owner.
