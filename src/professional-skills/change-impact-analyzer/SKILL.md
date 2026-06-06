---
name: change-impact-analyzer
description: Analyzes change blast radius across product behavior, UX, domain model, API, data, frontend, backend, integrations, security, testing, deployment, observability, compatibility, and documentation before implementation or release.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---

# Change Impact Analyzer

## Mission
Expose the complete blast radius of a proposed change before design or implementation begins — mapping every affected surface, distinguishing direct from downstream impacts, identifying compatibility and rollback implications, and surfacing unknown ownerships — so that the implementation path, specialist routing, gates, and rollback plan are calibrated to actual risk rather than first-impression scope.

## When To Use
- Before implementation begins on any change that may touch multiple system layers, contracts, or ownership boundaries.
- Before design decisions are locked when cross-cutting concerns (auth, data model, API, events) are involved.
- Before a release or migration when downstream impact on consumers, integrations, or dependent services is unclear.
- When a change request arrives with narrow stated scope but hints at wider behavioral, data, or contract implications.
- When a rollback plan cannot be defined without understanding the full write path and state mutations involved.
- When an agent proposes a local fix and has not scanned for the same defect pattern across the affected codebase.

## Do Not Use When
- The change is a narrowly scoped mechanical edit with fully understood ownership, no behavioral change, and no contract, migration, or release risk.
- The change is a typo fix, comment update, or test data cleanup with zero behavioral surface area.

## Non-Negotiable Rules
- Inspect every potentially affected surface — do not stop at the first impacted component and assume the rest is safe.
- Distinguish impact types: Direct (code must change), Indirect (behavior or contract changes), Downstream (consumers must adapt), Latent (no immediate change but risk is created).
- Never mark a surface as "not impacted" without explicit reasoning — unknown is not the same as unimpacted.
- Identify compatibility implications: backward compatibility for API consumers, schema migration readiness for data consumers, version skew tolerance for distributed systems.
- Rollback implications must be analyzed for every stateful change — "just redeploy the old version" is not a rollback plan when data has been migrated.
- Make unknown ownership explicit — do not assume a surface is safe because its owner is not on the current thread.
- Surface all open questions as actionable placeholders with proposed owners, not hidden assumptions.
- Local fixes require same-pattern scan evidence: name the pattern searched, scope scanned, related occurrences, and why the fix is local or broader.

## Industry Benchmarks
- **Architecture Review Board (ARB) Impact Analysis**: Structured surface-by-surface review before implementation approval — mandatory for tier-1 systems in regulated industries.
- **RFC 2119 (Must/Should/May)**: Distinguish mandatory compatibility requirements from recommended guidance when communicating impact to stakeholders.
- **SemVer (Semantic Versioning)**: Any API or library change that is not backward-compatible is a major version change — consumers must be notified before release.
- **TOGAF Business Impact Analysis**: Maps technical changes to business capability impact — required for enterprise change management.
- **OWASP Threat Modeling (STRIDE)**: Changes that introduce new attack surfaces require a threat model update alongside the blast radius analysis.
- **ISO/IEC 25010 (Software Quality Model)**: Impact dimensions include Functionality, Reliability, Performance Efficiency, Security, Maintainability, and Portability — all may be affected.
- **Change Management (ITIL CAB)**: Changes to production systems require documented impact, risk, rollback, and communication plan before approval.

### Impact Classification Matrix

| Surface | Direct Impact | Indirect Impact | Downstream Impact | Rollback Risk |
|---|---|---|---|---|
| Product behavior (UI/UX flows) | Behavior change | Flow dependency change | Consumer UX expectation | State loss on rollback |
| Domain model (entities, rules) | Rule/state change | Derived state change | Downstream event handlers | Schema migration required |
| API contract (endpoints, shapes) | Endpoint change | Error code change | API consumers must adapt | Breaking if rolled back |
| Database schema | Column/table change | Index/query impact | ORM model change | Migration required |
| Frontend (components, state) | Component change | State model change | A/B test / analytics | UI regression risk |
| External integration | Webhook / protocol | Error handling | Provider dependency | No provider rollback |
| Security (authz, permissions) | Permission change | Access pattern change | Audit trail change | Permission rollback risk |
| Observability (alerts, SLOs) | Alert threshold | Dashboard | On-call procedure | Alert gap during rollback |

## Technical Selection Criteria
Systematically assess each surface below — declare impact level (Direct / Indirect / Downstream / None-with-rationale / Unknown):
- **Product behavior**: Does the visible user experience, workflow, or user-observable state change?
- **UX / interaction model**: Do screen flows, navigation, or interaction states change?
- **Domain model**: Do entities, aggregates, invariants, state transitions, or domain events change?
- **API contract**: Do endpoint paths, request schemas, response shapes, status codes, error codes, or pagination change?
- **Data model / schema**: Do tables, columns, indexes, constraints, or normalization change?
- **Frontend**: Do components, routes, client state, data fetching, or rendering logic change?
- **Backend**: Do service methods, command handlers, authorization rules, or transaction boundaries change?
- **External integrations**: Do third-party API calls, webhooks, credentials, or provider contracts change?
- **Security posture**: Do permission rules, authentication flows, data access patterns, or audit trails change?
- **Testing**: Do acceptance criteria, test fixtures, contract tests, or test data change?
- **Deployment / infrastructure**: Do environment variables, container config, Kubernetes manifests, or migration scripts change?
- **Observability**: Do log schemas, metric names, alert thresholds, SLO targets, or on-call runbooks change?
- **Compatibility**: Are there backward compatibility obligations to existing consumers, mobile clients, or versioned APIs?
- **Documentation**: Do user guides, API docs, runbooks, ADRs, or changelogs need updating?

### Decision Tree: How Deep to Analyze?

```
Is the change modifying a shared contract (API, event schema, data model)?
├── Yes → Full downstream consumer analysis required
│   └── Unknown consumers → Escalate before proceeding
Is the change modifying authorization or permission logic?
├── Yes → Security surface and audit trail analysis required
Is the change modifying data that must be migrated?
├── Yes → Schema migration, rollback, and data consistency analysis required
Is the change affecting an SLO-critical path?
├── Yes → Observability, alerting, and reliability impact analysis required
Change touches only internal module with no interface change?
└── Minimal analysis sufficient, confirm no latent impact
```

## Solution Optimality Self-Check
Apply during blast-radius analysis to expose performance-surface impacts invisible from functional analysis. For every change, answer four questions ("N/A" needs a one-line rationale): does it add CPU to a hot path, increase memory at scale, add network calls (N+1 fan-out), or alter disk I/O patterns? Add a performance-impact classification (Direct / Indirect / None with evidence) to the blast radius before declaring "no performance impact".

Load [references/solution-optimality.md](references/solution-optimality.md) for the performance-impact classification matrix and the latent-risk checklist (schema rewrites, N+1 multipliers, job overlap, cache-invalidation scope, new synchronous dependencies) when the change touches a performance-sensitive path. Method compiled from `solution-optimality-evaluation`.

## Risk Escalation Rules
- Escalate when a public API contract change affects external consumers who have not been notified.
- Escalate when a schema migration is required but no tested rollback migration exists.
- Escalate when permission or authorization logic changes could inadvertently broaden access to sensitive data.
- Escalate when the blast radius cannot be fully determined because ownership of a dependent surface is unknown.
- Escalate when an irreversible write (financial transaction, destructive migration, audit record) is on the change path.
- Escalate when concurrent changes from other teams affect overlapping surfaces — coordination risk is high.
- Escalate when the change requires feature flags that are not yet in place and the release window is fixed.
- Escalate when the observability gap during rollout would prevent early detection of a regression.
- Escalate to `agent-execution-discipline` when an agent attempts to hand off impact analysis without evidence inventory, boundary, residual risk, and validation result.

## Critical Details
- The quietest surfaces are the most dangerous: documentation, alert thresholds, test fixtures, client SDKs, and feature flag configurations are frequently overlooked in blast radius analysis.
- "It's a small change" is the most common precursor to a high-severity incident — size of code change is uncorrelated with blast radius.
- Downstream impact requires consumer enumeration — not just "API consumers in general" but specific named consumers with their version and migration readiness.
- Rollback is not symmetric: deploying the old version is only a valid rollback plan if no state mutations have occurred that would be incompatible with the old version.
- Unknown ownership is a blocking risk — changes that touch surfaces with unknown owners must identify the owner before the change can proceed safely.
- Version skew tolerance analysis: in distributed systems, the old version of service A may coexist with the new version of service B for minutes to hours during a rolling deployment — the behavior during that window must be analyzed.
- Feature flag cutover: when a change is behind a flag, the full blast radius still exists once the flag is enabled — document the pre-flag and post-flag impact separately.

### Anti-Examples

| Analysis Pattern | Problem | Corrected Approach |
|---|---|---|
| "Only the login endpoint changes" | Misses auth token format change affecting all authenticated calls | Trace all callers of auth tokens, not just the login surface |
| "Docs will be updated later" | Documentation is a release blocker, not a follow-up | Include documentation impact in the same analysis |
| "Unknown consumers can just re-read the API" | Breaking change without migration guide harms known and unknown consumers | Enumerate consumers; provide migration guide before release |
| "Rollback is just reverting the deploy" | Data migration already ran; old code cannot read new schema | Require rollback migration before approving forward migration |
| "Security isn't affected, it's just a data field" | New field exposed in API may contain PII or sensitive data | Assess every new API field for data classification and access control |

## Failure Modes
- **Local-only analysis misses dependent clients**: An API field is renamed; 3 downstream microservices crash at deployment because the blast radius analysis only covered the originating service.
- **No compatibility review breaks consumers**: A response field changes from a string to an integer; clients that parse it as a string fail at runtime with no compile-time warning.
- **No observability review makes release impact invisible**: A performance-critical query changes and no metric baseline or alert exists — degradation accumulates for 2 hours before manual detection.
- **Hidden migration makes rollback impossible**: A column is renamed and data is migrated; the rollback plan says "revert the service" but the old service expects the old column name — rollback fails.
- **Unknown owner delays incident response**: A component affected by the change has no declared owner — during the post-release incident, the on-call team has no one to escalate to.
- **Concurrent team changes collide**: Two teams are modifying the same shared schema simultaneously; neither impact analysis accounts for the other — the combined change is incompatible.
- **Feature flag analysis skipped**: A change is marked "safe because it's behind a flag" — but the flag is enabled 2 weeks later without re-analyzing the full blast radius in the new system state.
- **Test fixture drift**: A change to the domain model is not reflected in test fixtures — all tests pass with the old fixture data and a regression is discovered only in production.

## Reference Loading Policy
Do not load every reference by default. Treat references as targeted support selected by the router and the task risk.

- L1 changes: do not read references unless the task touches security, data, auth, external integration, performance, release, or irreversible behavior.
- L2 changes: read `references/capabilities/index.md` and only capability files explicitly selected by `change-forge-router`.
- L3 changes: read all selected capability references and `references/checklist.md` when present.
- L4/L5 changes: read all selected capability references, `references/checklist.md` when present, and domain extension references when selected.
- Selected capability reference path format: `references/capabilities/<capability-id>-<capability-name>.md`.

Examples:
- `42 idempotency-retry-design` -> `references/capabilities/42-idempotency-retry-design.md`
- `82 solution-optimality-evaluation` -> `references/capabilities/82-solution-optimality-evaluation.md`

## Output Contract
Return a structured impact analysis with:
- **Surface inventory**: Every assessed surface with impact level (Direct / Indirect / Downstream / None + rationale / Unknown + proposed owner).
- **Compatibility assessment**: Backward compatibility status for API and data model changes; consumer list and migration readiness.
- **Rollback analysis**: Whether rollback is safe without data intervention; required rollback migration scripts if schema has changed.
- **Specialist routing**: Which professional skills must be engaged based on identified impacts.
- **Release concerns**: Feature flag dependencies, deployment sequencing, staged rollout requirements.
- **Open questions**: Unknown surfaces, undetermined owners, or impact dimensions requiring further investigation — each with proposed owner and urgency.
- **Same-pattern scan record**: Pattern signature, directories or globs searched, other occurrences found, and local-only or broad-fix rationale when a bug fix is proposed.
- **Risk summary**: Overall blast radius classification (Low / Medium / High / Critical) with key risk factors listed.

## Evidence Contract
Close an impact analysis only when all five canonical answers are concrete (answer schema: `agent-execution-discipline`):
- **Basis**: the change under analysis and the surfaces it plausibly reaches, stated before scanning so nothing is assumed safe by omission.
- **Files and boundaries inspected**: the hard blast-radius scan actually run — call chain and callers, configuration and environment variables, database tables and migrations, message topics, cache keys, API consumers, test directories, documentation, CI/CD pipelines, and deployment resources — with what each surface revealed or "none found".
- **Placement rationale**: why each surface is classified Direct, Indirect, Downstream, or None, and why each specialist routing is required.
- **Validation commands**: the greps, call-graph queries, schema or consumer lookups run to confirm each impact, each with its outcome.
- **Residual risk**: the Unknown surface or unverified downstream effect that remains, with its proposed owner and urgency.

## Quality Gate
1. Every relevant surface is marked as: Direct / Indirect / Downstream / None (with explicit rationale) / Unknown (with proposed investigation owner).
2. All public or internal API contract impacts are identified with named consumer list and compatibility assessment.
3. Schema migration rollback safety is explicitly analyzed — not assumed.
4. Permission and security surface impacts are identified and routed to the appropriate gate.
5. Observability and alerting gaps during rollout are identified and addressed.
6. Concurrent change risks from other teams are acknowledged.
7. Unknown ownership surfaces are escalated, not left as silent assumptions.
8. Open questions are listed with proposed owners and not silently resolved.
9. Specialist skills required are named and routed.
10. A rollback plan exists that accounts for all stateful changes.
11. Agent-assisted local fixes include same-pattern scan evidence and closure boundary.

## Handoff
- **domain-impact-modeler** — when business rules, invariants, state machines, or domain events are affected.
- **experience-impact-modeler** — when user-facing flows, interaction states, or accessibility is affected.
- **data-api-contract-changer** — when API contracts, schemas, or data migrations are affected.
- **backend-change-builder** — when backend service logic, authorization, or data mutations are affected.
- **security-privacy-gate** — when permission rules, auth flows, data access, or audit trails are affected.
- **reliability-observability-gate** — when SLO paths, alert thresholds, or performance-critical paths are affected.
- **task-dag-planner** — when the impact analysis reveals a multi-phase implementation requiring dependency sequencing.
- **agent-execution-discipline** — when analysis lacks evidence, same-pattern scan, residual risk, or handoff package.

## Completion Criteria
The implementation plan can be scoped and executed with clear risk boundaries, verified specialist routing, explicit compatibility and rollback analysis, identified ownership for every impacted surface, and no silently assumed safe-by-default surfaces.
