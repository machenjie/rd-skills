# Backend Output And Gates

Load this reference when `backend-change-builder` needs the full output field list, exhaustive quality gate, or detailed handoff table. The skill body keeps default runtime context compact.

## Output Contract
Return a backend implementation plan or review with:
- **Mode selected**: New-build / modify-existing / bug-fix / debugging-diagnosis / code-review / refactoring / performance-reliability / release-delivery, with the trigger signal that selected it.
- **Professional judgment**: backend decision made, plausible auth/consistency/idempotency/contract risks ruled out, and risks still possible.
- **Validation model**: Inputs, types, constraints, injection prevention at trust boundary.
- **Authentication mechanism**: Token type, expiry, verification method.
- **Authorization model**: Role/permission check, object-level check per operation.
- **Trust boundary analysis**: HTTP/message/webhook/CLI boundary, caller identity source, tenant boundary, and untrusted fields rejected.
- **Authorization/tenant/object ownership analysis**: resource access path, ownership filter or policy check, denied cases, and same-pattern scan result.
- **Transaction boundaries**: Explicit commit/rollback scope, isolation level, compensating actions.
- **Transaction/partial-success analysis**: atomicity requirement, partial failure point, compensation or saga path, and rollback limitation.
- **Dependency wiring and lifecycle**: composition root, dependency graph, lifecycle scope, construction/shutdown owner, reusable client/pool policy, test override, and circular dependency check.
- **Failure contract**: typed failure taxonomy, controller/service/repository/adapter translation, retryability, fallback/degradation, safe user message, cause preservation, and negative-path tests.
- **Data and side-effect flow**: validation, mapping, policy, mutation, transaction, persistence, cache, event, external IO, ordering, publish-after-commit, idempotency, and compensation.
- **Algorithm/data-structure decision**: input size/distribution, complexity, memory budget, streaming/chunking, rejected alternatives, and benchmark/profile evidence when backend scale is material.
- **Configuration runtime policy**: typed config, safe defaults, validation/fail-fast behavior, feature flag lifecycle, mode/kind governance, rollout/rollback, and cleanup owner.
- **Idempotency design**: Key source, scope, deduplication window, expired-key behavior.
- **Idempotency/retry analysis**: retry source, duplicate-delivery behavior, dedupe storage, backoff, DLQ/replay plan when async.
- **Error model**: Error code taxonomy, HTTP status mapping, client-visible vs. server-log distinction.
- **Error/logging/observability analysis**: typed errors, structured logs, correlation ID, metric/trace signal, and alert/runbook implication.
- **Observability plan**: Log fields with correlation ID, metrics emitted, alert thresholds.
- **Concurrency analysis**: Race condition risk, locking strategy, ordering assumptions.
- **Boundaries inspected**: controllers, services, repositories, validators, jobs, mappers, configs, callers, API contracts, data boundaries, permission boundaries, and release boundaries inspected or explicitly skipped with reason.
- **Reuse and placement rationale**: Existing services/repositories/helpers inspected; reuse vs. new decision; function/class/file placement; public/private boundary; ownership; new imports and dependency direction.
- **Minimal Correctness Decision**: simplicity ladder result, deleted or rejected backend machinery, accepted direct/local implementation, and any shortcut ceiling with upgrade trigger.
- **Behavior preservation statement**: old behavior, public contract, error semantics, auth semantics, transaction semantics, and side effects preserved or intentionally changed.
- **Code clarity and maintainability**: main-flow readability, side-effect boundary, signature clarity, next-change location, and cleanup/deprecation plan.
- **Validation evidence**: commands run, outputs, same-pattern scan, regression/contract/integration coverage, and manual checks when tests are not possible.
- **Evidence limits**: what each backend check proves and what it does not prove about tenants, concurrency, async replay, rollback, load, or consumers.
- **Residual risk**: unverified concurrency, partial-write, DLQ, rollback, load, or consumer risk with owner.
- **Next gate/handoff**: next professional skill, capability, release gate, or explicit no-next-gate rationale.
- **Test obligations**: Unit tests for auth, validation, error paths; integration tests for transactions.

## Quality Gate
1. Every trust boundary has explicit input validation covering type, range, presence, and injection prevention.
2. Object-level authorization is enforced server-side for every resource operation; IDOR prevention verified.
3. All multi-step write operations have explicit transaction boundaries and compensation plans.
4. All mutating operations that can be retried have idempotency design.
5. Error responses are machine-readable, use generic client messages, and include correlation IDs.
6. Logs are structured, contain correlation IDs, and contain no plaintext secrets or PII.
7. Background jobs have DLQ routing and failure alerting.
8. Unit tests cover authorization logic, validation logic, and error paths.
9. Concurrency race conditions are analyzed and mitigated for shared-state operations.
10. No hardcoded secrets, API keys, or connection strings in source code.
11. Existing backend functions, classes, services, repositories, validators, mappers, helpers, and adapters were checked before new code was added.
12. Every new backend function, class, or file has placement rationale and ownership.
13. No backend business logic is added to shared, common, or utils.
14. New imports respect module and layer dependency direction.
15. Agent-assisted backend changes include evidence, same-pattern scan for local fixes, and closure package.
16. Backend use-case flow remains readable; large services/functions, boolean traps, weak parameter bags, side-effect pollution, and stale compatibility branches are split or justified.

## Handoff
- **security-privacy-gate**: authorization logic, PII handling, or sensitive data access requires adversarial review.
- **data-api-contract-changer**: API response shapes, error codes, or pagination contracts are affected.
- **data-middleware-change-builder**: schema, index, or query performance impact is significant.
- **reliability-observability-gate**: SLO-affecting paths, async job reliability, or saturation risks are identified.
- **quality-test-gate**: test coverage gaps for authorization, transactions, or concurrency are found.
- **domain-impact-modeler**: business rule invariants, state machine transitions, or domain event emissions are affected.
- **testability-seam-design**: backend tests need seams for time/randomness/external IO or risk private-helper coupling.
- **failure-contract-design**: backend error states, retryability, fallback, or partial failure semantics are unclear.
- **dependency-wiring-lifecycle**: dependency graph, reusable client lifecycle, service locator, or shutdown cleanup is unclear.
- **data-side-effect-flow-tracing**: side effects may be hidden in mappers, policies, domain objects, getters, helpers, or repositories.
- **configuration-runtime-policy**: runtime config, feature flags, mode/kind switches, or kill switches alter backend behavior.
- **model-boundary-mapping**: DTOs, domain objects, persistence models, events, or mappers risk semantic leakage.
- **consumer-impact-analysis**: backend public contracts, SDK types, events, exports, or response fields can affect downstream consumers.
- **architecture-enforcement-tooling**: backend import, layer, export, generated-code, or forbidden-dependency rules need CI enforcement.
- **agent-execution-discipline**: backend implementation evidence, verified cause, same-pattern scan, or handoff boundary is missing.
