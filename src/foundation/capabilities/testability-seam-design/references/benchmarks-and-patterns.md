# Testability Seam Benchmarks And Patterns

Use this reference for L3+ seam decisions where the inline rules are not enough. Keep it focused on professional seam choice, not broad testing education.

## Seam Decision Rubric

| Decision pressure | Preferred move | Reject when |
| --- | --- | --- |
| Private helper export request | Test through API/service/component/module facade, or characterize public behavior first | Export exists only for tests or freezes local choreography |
| External provider double | Use fake/stub/mock/spy only at declared boundary and add contract or integration calibration when risk matters | Mock payloads can never occur in the real provider |
| Nondeterministic source | Introduce clock/random/UUID/env/scheduler provider with production default and test override | Global patch, sleep, retry, or CI timing decides pass/fail |
| Dependency graph override | Provide explicit test graph seam with reset/cleanup and production graph comparison | Tests build a graph production cannot construct |
| Fixture/golden pressure | Localize owner, asserted fields, mutation policy, privacy boundary, and deletion path | Shared business fixture becomes an implicit cross-module contract |
| Refactor before tests | Characterize observable behavior before movement, including preserved bugs when required | Structure changes land before current behavior is locked |

## Test Double Fidelity Ladder

1. **Real boundary:** use when constraints, transactions, permissions, serialization, generated schemas, provider quirks, or retry behavior are material.
2. **Fake:** use for stateful local behavior when in-memory semantics are close enough and limitations are recorded.
3. **Stub:** use for fixed collaborator outcomes when the branch under test is local and provider shape is simple.
4. **Spy:** use when an external boundary interaction is behavior and state output is insufficient.
5. **Mock:** use for declared external interactions, not private choreography.

Escalate to `contract-testing` or `integration-testing` when the selected double stands in for HTTP, DB, queue, cache, file storage, auth provider, SDK, generated client, event bus, or sandbox behavior that can drift.

## Deterministic Source Pattern

- Put production defaults at the composition/root boundary, not inside the test.
- Inject or centralize clock, random, UUID, locale/timezone, scheduler, environment, file system, network client, DB/cache/queue gateway, and feature flag reads.
- Reset global or process state after each test, and prefer per-test instances over shared mutable fixtures.
- Replace real sleeps with controlled scheduler advancement or awaited state changes.
- Record seed, frozen time, timezone, locale, concurrency schedule, and cleanup owner when they affect assertions.

## Characterization Before Movement

Before moving legacy, complex, stateful, auth, data, concurrency, or money/time behavior:

- Name the public behavior to preserve.
- Capture success, boundary, invalid, and representative failure cases.
- Preserve known bugs only when the refactor scope is behavior-preserving.
- Run the characterization command before and after structure movement.
- Record what the characterization proves and what remains unverified.

## Anti-Pattern Review

- Test-only interface with no production role.
- Package-visible method added only to satisfy a unit test.
- Mock call-count assertion for private choreography.
- Fake that ignores uniqueness, constraints, authorization, ordering, transactions, or retry semantics that the real provider enforces.
- Fixture factory carrying broad business defaults across unrelated modules.
- Golden file update accepted without naming the behavior changed.
- Validation report reused after seam, fixture, mock, generated input, graph override, or public-boundary changes.
