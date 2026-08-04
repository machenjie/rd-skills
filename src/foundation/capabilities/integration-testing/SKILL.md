---
name: integration-testing
description: "`analysis-agent`/`task-agent`/`review-agent`: use for database, broker, cache, HTTP, framework, process, or transaction seam proof; skip local, portfolio, and release-verdict work."
---

# integration-testing

## Registry Trigger

**Use when**

- test real module database service broker cache HTTP external adapter framework process or transaction boundary interaction

**Do not use when**

- work is limited to local logic external compatibility full user journeys overall portfolio or release readiness

## Skill Role

Select real-seam fidelity, failure injection, oracles, and verification. Consume fixture meaning, created-data namespace, sensitive-data policy, and cleanup from `test-data-management`; own disposable integration infrastructure outside test-data scope.

## High-Value Rules

- **Exercise the seam carrying the risk.** Name the participating components and boundary semantics, then use a real disposable dependency or a contract-calibrated substitute. Record calibration source, versions, and fidelity limits.
- **Assert the complete observable outcome.** Tie the named failure mechanism to caller response, durable state, emitted or queued effects, cache state, acknowledgements, and forbidden partial effects that matter. Status or mock-call assertions alone are insufficient.
- **Inject reachable failures.** Exercise applicable constraint errors, denial, timeout/unknown outcomes, early-write exceptions, duplicate delivery, retry exhaustion, rollback, and cleanup failure. Expected terminal state and recovery ownership are asserted.
- **Verify accepted isolation and cleanup.** Consume the `test-data-management` decision for fixture meaning, created-data namespace, sensitive-data policy, and asynchronous cleanup. State seam-specific requirements and own only disposable integration infrastructure outside test-data scope.
- **Test concurrency and eventual consistency by outcomes.** Assert allowed terminal-result sets, forbidden durable states or duplicate effects, and observable readiness with a bounded deadline. Do not require one scheduler interleaving or use fixed sleeps as synchronization.
- **Contain flake and stale evidence.** Preserve the first failure, reproduction inputs, dependency and schema versions, logs, owner, and remediation condition. Retry or quarantine does not become passing evidence, and material fixture, config, migration, or dependency edits require a fresh run.

## Anti-Patterns

- Reject a mocked primary seam, uncalibrated catch-all stub, shared mutable staging dependency, or container startup reported as interaction proof.
- Reject success-only assertions, response-status-only oracles, rollback-only cleanup for separately committed work, fixed sleeps, and positive-only authorization cases.
- Reject integration evidence promoted to full-journey, consumer-compatibility, production-capacity, managed-service, provider, or release proof.

## Stop Conditions

Stop and return the unresolved integration decision when the risk-carrying seam cannot be exercised, or fixture, namespace, or cleanup ownership is absent. Also stop when cleanup could reach shared resources, unapproved production systems are required, or transaction, authorization, migration, irreversible-effect, or cross-team ownership is unresolved. Local integration evidence proves only exercised versions, data, timing, and boundaries. It does not prove production scale or release readiness.

## Output Contract

- Return an integration-proof decision: state seam fidelity, accepted fixture and data-lifecycle decision, failure mechanism, oracle, seam-specific isolation and cleanup evidence, concurrency, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | an accepted test-data lifecycle leaves seam fidelity disposable non-data infrastructure failure injection oracle or eventual-consistency verification choices open | the test-data decision is absent or one owned setup proves the seam | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | schema auth serialization side effects failures cleanup concurrency or parallel safety need verification against the accepted test-data lifecycle | no real integration boundary participates or test-data ownership is unresolved | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | confidence depends on fresh proof that the seam honors accepted fixture namespace sensitive-data cleanup and parallel-safety decisions | no integration-confidence claim awaits proof or the test-data decision is absent | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
