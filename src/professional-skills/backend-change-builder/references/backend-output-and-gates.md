# Backend Output And Gates

Load only for a `task-agent` implementing or repairing a bounded backend service, API, worker, job, or persistence behavior that needs the extended proof contract.

## Do Not Load

Do not load for diagnosis, independent review, or work without a backend behavior change. Named Layer 3 Skills own specialized architecture, security, schema, lifecycle, algorithm, and release decisions.

## Output Contract

Return fields whose trigger is present in the implemented change, together with any unverified triggered risk:

1. **Implementation result and diff:** Name the implementation mode, acceptance obligation, actual diff or accessible host-native diff reference, changed files and owning boundaries, behavior added or preserved, and the final material edit.
2. **Trust and resource scope:** When untrusted identity or scope is affected, state the identity source, validation boundary, permission and tenant rule, and denied behavior. For attacker-controlled resource identity or scope, include server-side ownership/policy and cross-user or cross-tenant proof.
3. **Consistency and side effects:** when partial success can violate an invariant, state order, commit boundary, recovery, and effect visibility, with transaction or compensation evidence limited to risky multi-step writes.
4. **Repeatable execution and delivery:** For repeatable synchronous requests, webhooks, or provider calls, state retry source, duplicate outcome, idempotency scope, and recovery limit. Only for message or job delivery, additionally state delivery guarantee, acknowledgement timing, replay behavior, poison handling, and broker/job recovery evidence.
5. **API and data compatibility:** When a request, response, error, persistence, event, or message contract changes, state affected consumers, compatibility evidence, and any selected version, migration, dual-operation, or rollout boundary.
6. **Repair and validation proof:** Record each command and outcome run after the last material edit. For an accepted finding or verified defect, name the original finding or failure mechanism, repair scope, and fresh post-repair validation. Recurrence signals and same-pattern results apply only when triggered; otherwise map only triggered risks to current checks.
7. **Rollout, limits, and next owner:** For material behavior or data risk, state detection, rollout/watch, containment, and rollback or forward-repair conditions. Name unverified triggered scope and residual risk, then hand the diff/reference and fresh results to the independent-review owner without claiming approval.

## Quality Gate

1. When external input crosses a boundary, require validation and safe failure behavior for fields that can violate the affected invariant. Supported mechanisms include validators, parsers, allowlists, or typed schemas backed by current boundary evidence.
2. When an attacker controls resource identity, tenant, parent scope, filter, or indirect reference, require proof that authenticated server-side context constrains disclosure and mutation. Ownership predicates, tenant-scoped queries, or policy checks are candidates selected from the repository's authorization model.
3. When multiple writes or side effects can partially succeed and create inconsistent state, require an atomicity or recovery outcome plus failure-path proof. A storage transaction, conditional write, outbox, saga, or compensation is a candidate chosen from actual atomic boundaries and reversibility.
4. When execution or delivery can repeat, require a defined duplicate outcome and bounded recovery behavior. Idempotency or dedupe follows delivery and storage guarantees; message or job delivery alone adds acknowledgement, replay, and poison-message proof.
5. When persistence interacts with an event, cache, queue, or external call, require ordering evidence that protects the affected invariant and exposes partial success. Select publish-after-commit, transactional messaging, invalidation, replay, or reconciliation only when the system boundary supports the choice.
6. When a public API, schema, event, error, or message contract changes, require affected-consumer and compatibility proof proportional to reach. Versioning, tolerant reads, additive change, migration, dual operation, or coordinated rollout are candidates determined by current contracts and consumers.
7. Choose fresh unit, integration, contract, replay, fault-injection, concurrency, or manual checks after the last material edit for each triggered risk, with coverage claims limited to reachable validated behavior.
8. When release can expose irreversible data change, broad consumer impact, unsafe replay, or hard-to-detect partial failure, require a detection and containment outcome. Rollback, forward repair, staged rollout, shadowing, feature control, or operational watch are candidates selected from reversibility and deployment evidence.
