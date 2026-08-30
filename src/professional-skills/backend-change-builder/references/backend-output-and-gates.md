# Backend Output And Gates

Load only for a `task-agent` implementing or repairing a bounded backend service, API, worker, job, or persistence behavior that needs the extended proof contract.

## Do Not Load

Do not load for diagnosis, independent review, or work without a backend behavior change. Specialized architecture, security, schema, lifecycle, algorithm, and release decisions remain with their authoritative capability boundaries.

## Output Contract

The implementation contract owns the result, diff, changed files, final-edit ordering,
validation commands/freshness, independent-review input, unverified scope, and residual
risk. Do not duplicate them here. Add the backend fields selected by triggered risk:

1. **Trust and resource scope:** identity source, validation boundary, permission/tenant rule, denied behavior, and—when attacker-controlled—server-side ownership/policy plus cross-user/tenant proof.
2. **Consistency and side effects:** when partial success threatens an invariant, order, commit boundary, recovery, effect visibility, and transaction/compensation evidence for risky multi-step writes.
3. **Repeatable execution and delivery:** retry source, duplicate outcome, idempotency scope, and recovery limit; message/job delivery additionally needs guarantee, acknowledgement timing, replay, poison handling, and broker/job recovery evidence.
4. **API and data compatibility:** changed request/response/error/persistence/event/message consumers, compatibility evidence, and any version, migration, dual-operation, or rollout boundary.
5. **Material rollout risk:** detection, rollout/watch, containment, and rollback/forward-repair conditions.

## Quality Gate

1. Boundary-crossing input needs invariant-relevant validation and safe failure, using evidence-backed parsers, allowlists, schemas, or validators.
2. Attacker-controlled identity/scope needs authenticated server-side disclosure/mutation constraints proved through the repository's ownership, tenant-query, or policy model.
3. Partially successful writes/effects need failure-path proof of atomicity or recovery chosen from actual boundaries and reversibility.
4. Repeatable execution needs a duplicate outcome and bounded recovery; message/job delivery additionally proves acknowledgement, replay, and poison handling.
5. Persistence plus event/cache/queue/external effects needs supported ordering that preserves the invariant and exposes partial success.
6. Public API/schema/event/error/message changes need reach-proportional consumer and compatibility proof; current contracts choose versioning, tolerant/additive change, migration, dual operation, or cutover.
7. Map each triggered risk to fresh post-edit unit, integration, contract, replay, fault, concurrency, or manual evidence that exercises the changed behavior.
8. Irreversible data, broad consumers, unsafe replay, or hidden partial failure needs evidence-backed detection and containment, rollback/repair, staged exposure, feature control, or watch.
