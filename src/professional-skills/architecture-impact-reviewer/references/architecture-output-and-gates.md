# Architecture Output And Gates

Load this reference when `architecture-impact-reviewer` needs the full output field list, exhaustive quality gate, or detailed handoff table. The skill body keeps default runtime context compact.

## Output Contract
Return a structured architecture review with:
- **Mode selected**: architecture mode and trigger signal that selected it.
- **Decision**: Approved / Approved with conditions / Returned for redesign.
- **Alternatives considered**: at least one simpler alternative with explicit reason for rejection.
- **Boundary impact**: new or changed module and service boundaries with ownership declarations.
- **Module graph**: monorepo package/module graph, owners, public interfaces, allowed dependency directions, and generated-file ownership when applicable.
- **Dependency impact**: new dependencies with direction, coupling level, and availability analysis.
- **Dependency wiring and lifecycle**: composition root, dependency graph, lifecycle scope, service locator decision, singleton/global-state ownership, startup validation, and shutdown cleanup when architecture changes wiring.
- **Architecture enforcement plan**: import/cycle/export/forbidden-dependency rules, tool choice, CI command, generated-code exceptions, migration path, and residual unenforced rule.
- **Consumer impact report**: changed public contract, known/unknown consumers, compatibility, migration/deprecation, telemetry, and rollout/rollback when public boundaries change.
- **Data ownership impact**: any changes to authoritative data ownership with contract requirements.
- **Tradeoff analysis**: explicit tradeoffs accepted (performance vs. consistency, simplicity vs. extensibility, etc.).
- **Failure blast radius**: operational impact if the new component fails.
- **Observability requirements**: metrics, traces, and alerts required for the new component.
- **Build and test impact**: affected tests, incremental build approach, build cache key inputs, generated file policy, and full-suite fallback when applicable.
- **ADR requirement**: yes/no, whether a written ADR is required before implementation.
- **Open risks**: unresolved design risks with proposed owners and review dates.
- **Boundaries inspected**: modules, packages, services, public APIs, data owners, generated files, dependency edges, release topology, and tests inspected.
- **Professional judgment**: over-engineering vs under-design decision, reversibility, hidden coupling ruled out, and owner accountability.
- **Reuse and placement rationale**: existing module/service/API/contract reused or new boundary justified, with public/private decision.
- **Behavior preservation statement**: existing contract, dependency direction, ownership, rollout, and operational behavior preserved or intentionally changed.
- **Validation evidence**: dependency-graph, affected-test, build-cache, ADR, or not-verified disclosure with outcome.
- **Evidence limits**: what architecture evidence proves and does not prove about scale, org ownership, production traffic, and future requirements.
- **Residual risk and next gate**: accepted tradeoff, deferred ADR, rollout/reliability/docs handoff, and owner.

## Quality Gate
1. The chosen design is demonstrably simpler than at least one alternative that was explicitly considered.
2. Every new boundary has a named owner and a failure handling strategy.
3. Dependency direction is correct; no dependencies point from stable to volatile layers.
4. Data ownership is unambiguous; no entity has two authoritative owners.
5. All tradeoffs are explicitly documented, not assumed.
6. No speculative extensibility abstractions without existing concrete use cases.
7. Availability implications of new synchronous dependencies are quantified.
8. Irreversible decisions are explicitly acknowledged and approved.
9. Rollback path exists or the absence is explicitly documented and accepted.
10. Observability requirements for the new component are stated.
11. Monorepo changes include module graph, affected tests, cache key inputs, generated-file policy, and ownership boundaries.

## Handoff
- **data-api-contract-changer**: new or changed data models, schemas, or API contracts require design.
- **backend-change-builder**: implementation direction is confirmed and coding can begin.
- **integration-change-builder**: new external service dependencies are introduced.
- **reliability-observability-gate**: new components require SLI/SLO definition and observability design.
- **delivery-release-gate**: architectural changes affect deployment topology, migration sequencing, or rollback safety.
- **change-documentation-gate**: an ADR, runbook, or developer guide update is required.
- **ci-cd**: module graph decisions must be enforced through affected tests, incremental builds, or cache policy.
- **package-dependency-management**: workspace dependencies, lockfiles, generated packages, or hoisting affect architecture boundaries.
- **architecture-enforcement-tooling**: architecture rules need import, cycle, export, forbidden dependency, lint, type, dead-code, or CI enforcement.
- **dependency-wiring-lifecycle**: dependency graphs, composition roots, service locators, singleton lifecycle, or shutdown ownership affect architecture boundaries.
- **consumer-impact-analysis**: public exports, SDKs, APIs, schemas, or events can affect downstream consumers.
- **algorithm-data-structure-selection**: architecture-level caches, registries, batch flows, rankings, or graph/routing structures need scale and memory proof.
- **data-side-effect-flow-tracing**: architecture decisions hide persistence, cache, event, external IO, or telemetry side effects across boundaries.
- **cleanup-deletion-governance**: architecture cleanup removes stale modules, flags, compatibility branches, deprecated APIs, or dead code.
