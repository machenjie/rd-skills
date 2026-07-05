# Requirement Structuring Benchmarks And Patterns

Use this reference when `requirement-structuring` needs benchmark anchors, requirement quality matrices, behavior-first conversion rules, compatibility and constraint depth, graph/memory/execution coupling, or anti-pattern review beyond the inline `SKILL.md` body.

## Contents

- Benchmark Anchors
- Structured Brief Quality Matrix
- Behavior-First Conversion Pattern
- Traceability Matrix Pattern
- Constraint And Dependency Classification
- Graph, Memory, And Execution Coupling
- Anti-Patterns To Reject
- Handoff Boundaries

## Benchmark Anchors

| Benchmark | Structuring implication | Evidence to require |
| --- | --- | --- |
| ISO/IEC/IEEE 29148 | Requirements must be complete, consistent, unambiguous, feasible, verifiable, and traceable before design starts. | Requirement id, authority source, evidence source, verification path, and unresolved gap. |
| IEEE 830 | A requirement statement should separate function, external interface, performance, design constraint, attribute, and dependency. | Classification per brief item and explicit "not authorized" boundary. |
| BDD / Gherkin | Acceptance should express actor, state, trigger, and observable outcome. | Given/When/Then or equivalent scenario with a verifier. |
| ATDD / Specification by Example | Shared examples prevent stakeholder and implementer interpretation drift. | Concrete examples, boundary values, and owner-reviewed acceptance signal. |
| INVEST | Brief slices should be independent, small, and testable enough to plan without hidden scope. | One behavior per requirement and explicit adjacent non-goals. |
| Agile Definition of Ready | Work should not enter planning with unresolved blockers, authority gaps, or missing acceptance. | Blocking vs non-blocking unknowns and owner response path. |
| RFC 2119 | Binding terms should be separated from informative notes. | MUST/MUST NOT/SHOULD meaning or local equivalent. |
| ISO/IEC 25010 | Quality constraints need named attributes such as performance, security, reliability, usability, compatibility, or maintainability. | Quality attribute, threshold, environment, and validation artifact. |

## Structured Brief Quality Matrix

| Brief field | Strong answer | Weak answer to reject |
| --- | --- | --- |
| Current behavior | Actor plus precondition plus observable output, side effect, or state. | "The service calls X" or "currently broken" without an observation. |
| Desired behavior | Outcome the actor or system must observe. | Endpoint, table, class, component, or task list as the requirement. |
| Actor | Role, system, tenant, integration, or operator with relevant authority. | "User" or "system" when role, trust, or permission matters. |
| Trigger | Event, request, job, command, UI action, or dependency condition that starts behavior. | "When needed" or hidden trigger inferred from implementation. |
| Scope | Named surfaces, data, APIs, screens, jobs, events, docs, or configs. | Broad module names with no included/excluded surfaces. |
| Non-goals | Behavior-bound exclusions with not-present checks. | Time-box language such as "not this sprint." |
| Constraint | Binding criterion with threshold, scope, environment, or standard. | "Fast", "secure", "compatible", or "simple" without measurement. |
| Dependency | External contract, owner, feature flag, migration, rollout, or data condition. | Implicit ordering hidden in task notes. |
| Acceptance signal | Falsifiable scenario, test, review, query, dashboard, or owner sign-off. | "Works", "reviewed", or "tests pass" without artifact scope. |
| Traceability | Each requirement, non-goal, constraint, and dependency maps to downstream owner and evidence. | Separate requirement and test lists with no mapping. |

## Behavior-First Conversion Pattern

Use this pattern when a request arrives as an implementation instruction:

```text
Implementation phrase:
  "Add/change/remove [mechanism]."

Ask:
  Which actor or system initiates it?
  What precondition makes it relevant?
  What observable output, side effect, state transition, or absence must result?
  Which existing behavior must remain unchanged?
  Which implementation choices are not yet authorized?

Structured requirement:
  Given [precondition], when [actor/system trigger], then [observable outcome],
  without changing [non-goal/compatibility boundary].
```

Reject the conversion when current behavior, actor, trigger, or desired outcome is unknown and the answer could change public contract, data, authorization, migration, rollout, or compliance behavior.

## Traceability Matrix Pattern

| Item type | Required mapping | Preferred evidence | Evidence limit |
| --- | --- | --- | --- |
| Functional requirement | Requirement id -> scenario -> test/review owner. | Unit, integration, contract, E2E, or manual review artifact. | Does not prove unlisted actors, states, or surfaces. |
| Non-goal | Exclusion -> forbidden artifact -> not-present check. | Route/schema/UI/job/event/docs scan or contract diff. | Does not prove future work stays excluded. |
| Constraint | Constraint -> metric/threshold -> validator or specialist gate. | Load test, security scan, accessibility audit, SLO query, or owner review. | Does not prove other environments or data volumes. |
| Dependency | Dependency -> owner/contract -> readiness signal. | Owner decision, contract version, feature flag status, migration plan, or release note. | Does not prove provider uptime or future compatibility. |
| Assumption | Assumption -> reason safe -> expiry/trigger. | Source convention, reversible default, explicit owner follow-up. | Does not prove stakeholder approval. |

## Constraint And Dependency Classification

| Signal | Classify as | Next owner |
| --- | --- | --- |
| Response time, throughput, capacity, SLO, alert, dashboard | Quality constraint | `reliability-observability-gate` or `performance-budgeting` |
| Backward-compatible payload, enum, status code, generated client, event | Compatibility constraint | `data-api-contract-changer` or `version-compatibility` |
| Auth, tenant, role, data visibility, audit, abuse path | Security/privacy constraint | `security-privacy-gate` or `permission-boundary-modeling` |
| Migration, backfill, retention, deletion, irreversible data change | Data/release dependency | `data-api-contract-changer` and `delivery-release-gate` |
| Feature flag, rollout order, config default, rollback limit | Release dependency | `delivery-release-gate` and `release-rollback` |
| External API, partner contract, webhook, queue, async job | Integration dependency | `integration-change-builder` and relevant foundation capability |

## Graph, Memory, And Execution Coupling

| Input | Use as | Reject as |
| --- | --- | --- |
| Repository graph | Selector for affected source paths, consumers, tests, docs, generated artifacts, jobs, routes, configs, and owners. | Proof of behavior or product intent without current source inspection. |
| Project memory | Lead to previous decisions, fragile areas, rejected assumptions, and recurring disputes. | Authority for current requirements without date, owner, and current-source confirmation. |
| Execution trajectory | Freshness ledger for commands run, findings repaired, validations stale after edits, and skipped gates. | Final proof when output predates the final brief or relevant source edit. |
| Stakeholder note | Owner signal or assumption candidate. | Binding fact without scope, date, authority, and validation expectation. |
| Generated artifact | Contract or source evidence only when generated from current source and inspected after generation. | Design intent or proof of future compatibility by itself. |

Strong outputs classify each graph, memory, stakeholder, generated, and execution input as accepted, rejected, stale, partial, or not verified.

## Anti-Patterns To Reject

| Anti-pattern | Why it fails | Corrective action |
| --- | --- | --- |
| "Add endpoint X" becomes the requirement. | Mechanism can ship while the business/system outcome remains false. | Convert to actor, precondition, trigger, outcome, and compatibility boundary. |
| Current behavior copied from code internals. | Internal calls do not describe what users or systems observe. | Inspect observable output, state, side effect, or contract. |
| Non-goals hidden in task comments. | Implementers cannot prove excluded behavior stayed out. | Add behavior-bound exclusions and not-present checks. |
| Constraint says "fast/secure/simple." | No reviewer can prove completion. | Bind to threshold, control, standard, owner, or residual risk. |
| Memory closes a requirement. | Prior context may be stale or from a different scope. | Confirm against current source/owner or mark as memory signal only. |
| Traceability created after coding. | The trace map may rationalize what was built instead of what was required. | Create map before task DAG or implementation planning. |
| Brief authorizes implementation choices. | Requirement intake leaks into design and narrows valid solutions prematurely. | Move design choices to downstream owner and keep brief outcome-first. |

## Handoff Boundaries

- Use `requirement-clarification` when authority, current behavior, desired behavior, constraint, dependency, or acceptance owner is unknown and could change the change boundary.
- Use `acceptance-standard-definition` when the brief is stable but the pass/fail standard, rejection condition, evidence type, or owner needs precision.
- Use `scenario-decomposition` when a single requirement needs normal, alternate, edge, failure, abuse, recovery, or operational paths before planning.
- Use `non-goal-boundary-definition` when exclusions, deferred decisions, forbidden artifacts, or version boundary checks dominate the risk.
- Use `repository-graph-analysis` when affected routes, consumers, generated files, tests, jobs, docs, or ownership are not known.
- Use `project-memory-governance` when prior decisions or recurring failure history affect trust but current source has not confirmed them.
- Use `validation-broker` or `quality-test-gate` when traceability needs command selection, freshness, fixture ownership, or coverage evidence.
