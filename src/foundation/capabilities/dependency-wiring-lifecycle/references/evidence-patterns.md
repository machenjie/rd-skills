# Dependency Wiring Lifecycle Evidence Patterns

Use this reference when wiring closure depends on validation freshness, prior source or task evidence claims, resource lifecycle proof, tool permission boundaries, or proof limits. Keep it as an evidence map, not a dependency injection guide.

## Dependency-Claim-To-Validation Map

| Wiring claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Construction owner is explicit | Composition root, constructor/factory/provider path, owner, consumers, and rejected locations | The inspected dependency has a named construction boundary | All dynamic container registrations are known |
| Lifecycle scope is correct | Scope matrix, resource type, identity/tenant/transaction coupling, startup validation, shutdown owner, and metrics | Obvious scope mismatch was considered | Production load or leak behavior is fully proven |
| Graph is acyclic and directed | Current graph slice, imports/providers, config variants, generated clients, cycle result, and omitted dynamic edges | Inspected graph does not knowingly violate direction | Runtime plugin discovery or reflection creates no hidden edge |
| Reusable resource is reused safely | Client/pool construction site, reuse scope, health check, pool config, close/drain path, and tests or review | The inspected hot path avoids per-operation construction | Capacity, latency, or resource leaks are proven under production load |
| Lazy/provider/service locator is bounded | Lazy/eager decision, race behavior, error caching, retry, first-use latency, observability, and test override | The inspected indirection has explicit semantics | The indirection is the best architecture choice |
| Test override preserves semantics | Public seam, fake/stub/mock/spy type, fixture owner, production graph comparison, and contract/integration proof | Tests do not knowingly rely on impossible production wiring | Every test double matches provider behavior forever |
| Validation is fresh after final wiring edit | Command/report/review path, changed dependency, graph edge, lifecycle path, exit code or status, and final edit scope | Evidence covers the final inspected wiring state | Unmeasured runtime load, leak, or shutdown paths are proven |
| Tool output is safe to retain | Action class, permission state, redaction rule, artifact path, retention owner, and rollback or cleanup path | Evidence collection avoids obvious secret/PII leakage | Every future graph export or connector output is safe |

## Current Evidence And Freshness

- Treat repository inspection, DI/container reports, generated clients, prior task evidence, prior incidents, validation output, and test fixture history as selectors until current source, config, tests, and owner evidence confirm them.
- Accept prior "graph is acyclic", "singleton is safe", "client is reused", "cleanup works", or "test override is equivalent" only when current constructors, providers, config variants, generated artifacts, and validation still match.
- Mark wiring evidence stale after edits to composition roots, constructors, factories, providers, config binding, generated clients, module boundaries, lifecycle hooks, test fixtures, shutdown paths, or build outputs.
- Map each final wiring or lifecycle claim to fresh evidence for the affected graph surface. Otherwise, record the claim as not run with its residual risk.

- If staging startup validation, leak check, shutdown rehearsal, sandbox provider run, record data class, lifecycle effect, stop condition, cleanup, rollback, and redaction.
- If production restart, pool/client mutation, secret/provider change, live connector write, require owner approval, blast-radius limit, rollback or containment path, and redaction rule.
