# Domain Logic Implementation Benchmarks And Patterns

Use this reference when `domain-logic-implementation` needs deeper support for rule authority, invariant placement, calculation contracts, graph/memory/execution coupling, validation maps, or anti-pattern review. Keep examples generic and do not include customer data, secret values, private policy text, or regulated identifiers.

## Authority Decision Matrix

| Rule Surface | Preferred Authority | Evidence Required | False Proof |
| --- | --- | --- | --- |
| Aggregate invariant | Aggregate root method or factory. | Entry-point inventory, allowed/denied cases, persistence reinforcement. | Controller or service precheck catches one route. |
| Entity-local invariant | Entity method protected by aggregate boundary. | Parent aggregate path, mutation API, forbidden direct writes. | Public field setter or ORM hook only. |
| Value validity | Value object constructor or named factory. | Boundary values, equality/format rules, serialization boundary. | Later service validation of raw primitives. |
| Cross-object policy | Domain policy/specification or pure domain service. | Objects read, policy inputs, failure reasons, no side effects. | Application service mutates state and calls infrastructure. |
| Lifecycle transition | Domain operation plus transition table. | Source/target states, actor/policy inputs, terminal-state denial tests. | UI disables the button but imports/jobs can still mutate. |
| Calculation or derivation | Named domain calculation object/method. | Formula basis, precision, timezone/currency, effective date/version, edge cases. | Copied formula in reporting or API mapper. |

## Entry-Point And Bypass Scan

Inspect every path that can create, mutate, calculate, or project the rule.

- API handlers, controllers, command handlers, resolvers, admin paths, import scripts, jobs, queue consumers, tests, fixtures, migrations, and support tooling.
- Repository save/update methods, ORM setters/hooks, SQL scripts, direct field writes, and generated clients that expose mutation paths.
- UI or frontend validation that may be useful for user feedback but cannot be the rule authority.
- Reporting, billing, analytics, reconciliation, and support projections that may copy calculations.
- Historical data and replay paths when old and new rule versions coexist.

Strong evidence names scanned paths, rejected bypasses, accepted prechecks, and paths not verified.

## Graph, Memory, And Trajectory Coupling

| Input | Accept When | Reject Or Downgrade When |
| --- | --- | --- |
| Repository graph | Current callers, mutators, tests, imports, events, and projections for the rule were inspected. | Graph proximity is treated as proof without reading source. |
| Project memory | Prior rule authority, incident, fragile path, or owner note has timestamp and unchanged source boundary. | Memory predates model moves, generated clients, tests, or rule version changes. |
| Execution trajectory | Validation, owner review, and graph scans ran after the final material edit. | Tests predate the final rule, fixture, or generated-artifact change. |
| Validation broker | Changed rules map to allowed/denied cases, bypass scans, transition tests, and residual risks. | A broad test command is reported without changed-rule coverage. |

## Domain Validation Patterns

| Claim | Evidence Pattern | What It Proves | What It Does Not Prove |
| --- | --- | --- | --- |
| Single rule authority | Source path, owner, and bypass scan all point to one aggregate/value/policy/domain service. | Inspected entry points use the named authority. | Runtime-only tools or future entry points not inspected. |
| Invalid state rejected early | Domain-level denied test asserts typed failure before persistence. | Domain behavior rejects the tested invalid state. | Database constraint coverage for all concurrent writes. |
| Transition table complete | Allowed and forbidden transitions with terminal-state tests. | Modeled states behave as tested. | New states added after validation. |
| Formula is stable | Boundary/property cases, rounding/time/currency version, and consumer impact note. | Calculation semantics for inspected cases. | External reporting copies not inspected. |
| Layer cleanup is safe | Duplicate-rule scan, removed/demoted checks, retained defense-in-depth rationale. | Selected duplicates were reconciled. | Hidden copies outside searched scope. |
| Cross-aggregate rule is controlled | Transaction/idempotency/outbox/compensation decision with owner and test or handoff. | Consistency path is intentionally designed. | All production race windows without load/concurrency proof. |

## Anti-Patterns To Reject

- Treating controller, UI, SQL, fixture, or migration checks as the only domain rule authority.
- Adding a domain service because a method is large, without proving no aggregate or value object owns the rule.
- Returning `true`, `false`, `null`, or generic exceptions for domain denials that need typed outcomes.
- Accepting ORM entities, DTOs, requests, raw rows, cache clients, queues, or external API payloads as native domain inputs.
- Copying money, entitlement, status, quota, deadline, or eligibility formulas across billing, reporting, UI, and support code.
- Claiming a transition is safe because a button is hidden while imports, jobs, admin tools, or events can still mutate state.
- Reporting green validation while graph scans, owner review, or denied-case tests predate the final edit.

## Handoff Boundaries

- Use `business-rule-extraction` when the rule, exceptions, examples, or owner are still unclear.
- Use `domain-object-identification` when aggregate, entity, value-object, or policy ownership is unresolved.
- Use `state-machine-modeling` when lifecycle states, terminal states, or transitions are not fully enumerated.
- Use `service-business-logic` when orchestration, authorization order, transaction scope, or external effects dominate.
- Use `repository-persistence` when ORM mapping, constraints, query behavior, or storage failure semantics are primary.
- Use `transaction-consistency` or `idempotency-retry-design` when concurrency, retry, outbox, compensation, or duplicate side effects are primary.
- Use `data-api-contract-changer` when domain failure or calculation semantics are externally visible contracts.
