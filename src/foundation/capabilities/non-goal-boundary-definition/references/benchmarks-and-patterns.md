# Non-Goal Boundary Definition Benchmarks And Patterns

Use this reference when `non-goal-boundary-definition` output needs more detail than the `SKILL.md` body should carry efficiently. Keep the main body focused on routing, evidence, output contract, and gates; use this file for benchmark anchors, classification matrices, templates, decision trees, graph/memory/trajectory coupling, review questions, anti-pattern review, and handoff boundaries.

## Contents

- Benchmark Anchors
- Non-Goal Classification Matrix
- Version Boundary Template
- Scope Boundary Decision Tree
- Forbidden Artifact Matrix
- Acceptance Exclusion Matrix
- Graph, Memory, And Trajectory Coupling
- Review Questions
- Anti-Patterns To Reject
- Handoff Boundaries

## Benchmark Anchors

- INVEST criteria: "Small" and "Testable" require bounded scope and checkable exclusions.
- IETF RFC practice: explicit "out of scope" sections prevent implementer assumptions.
- Shape Up: appetite, fixed time with variable scope, and rabbit-hole calls are practical non-goal controls.
- IEEE/ISO requirements engineering: requirements quality depends on traceability, verifiability, and scope clarity.
- TOGAF scope statements: architecture work should state inclusions, exclusions, constraints, and assumptions.
- Google design-doc convention: non-goals are part of the engineering design contract, not optional prose.
- OKR focus discipline: goals are meaningful only when excluded outcomes are clear.
- Backlog slicing practice: vertical slices must name the depth and adjacent capability deliberately left out.

## Non-Goal Classification Matrix

| Category | In scope example | Non-goal example | Forbidden artifact | Check evidence |
| --- | --- | --- | --- | --- |
| User management | Display existing users. | Create/edit/deactivate users. | POST/PUT/DELETE user endpoints; mutation UI. | API route search, UI action search, OpenAPI diff. |
| Data migration | Store new records going forward. | Backfill historical records. | Backfill job, historical migration, dual-write placeholder. | Migration directory review, job registry review. |
| Internationalization | English copy for v1. | Multi-language support. | Locale selector, translation tables, unused i18n keys. | UI copy scan, route/menu review. |
| Search | Keyword filter on current dataset. | Full-text search, facets, saved searches. | Search index, saved-search schema, background indexer. | Dependency/config/migration review. |
| API versioning | New v1 endpoint. | Legacy API compatibility bridge. | Legacy adapter, nullable v2 fields, reserved enum values. | Contract test, schema diff, consumer list. |
| Performance | Functional correctness at current load. | P99 optimization target. | Cache layer, denormalized table, speculative queue. | Performance budget note, data volume assumption. |
| Platform migration | Use current stack. | Move to new platform. | Dual-platform adapter, migration scaffolding. | Dependency graph and config review. |
| Accessibility | Keyboard navigable critical path. | Full WCAG audit for unrelated surfaces. | Broad unrelated component rewrite. | Acceptance standard and a11y scope review. |
| Operations | Existing dashboards continue. | New incident dashboard. | Unowned metric, alert, or runbook stub. | Observability diff and release gate note. |

## Version Boundary Template

```text
Feature: [Name]
Version: v[N]
Owner: [scope authority]
Date: [ISO date]

IN SCOPE:
  - [Behavior, actor, context, affected surface]
  - [API/schema/UI/job/event included now]

OUT OF SCOPE:
  - [Capability]: excluded from v[N], deferred to [version/backlog/ref].
    Reason: [priority/dependency/risk/time]
    Owner: [decision owner]
    Forbidden artifacts: [endpoints/fields/roles/UI/jobs/events/flags/docs]

VERSION BOUNDARY:
  - Current contract: [API, schema, permissions, UI, job/event behavior]
  - Immutable after release: [fields, status codes, response shape, user workflow]
  - Future compatibility: [what v1 must preserve without speculative scaffolding]

DEFERRED DECISIONS:
  - [Decision]: [blocking or non-blocking], owner [name], trigger [date/event].
    Current implementation must not assume [X].

ACCEPTANCE EXCLUSIONS:
  - Verify [endpoint/field/UI/job/event] does not exist or is not emitted.
  - Verify [out-of-scope behavior] has not changed.
```

## Scope Boundary Decision Tree

```text
Is the proposed item required for functional correctness, authorization,
data integrity, compliance, reliability, accessibility, compatibility, or
an existing customer/platform commitment?
  YES -> Not a non-goal. Move into scope or block release.
  NO  -> Continue.

Can the current implementation be correct without deciding it now?
  NO  -> Blocking unknown. Hand off to requirement-clarification.
  YES -> Continue.

Would deferring it make the future version require a breaking API/schema/UI
change or irreversible migration?
  YES -> Escalate future compatibility and migration cost before accepting.
  NO  -> Continue.

Does current work need a placeholder endpoint, field, role, flag, job, event,
or UI element to prepare for it?
  YES -> Reject as speculative surface or formally re-scope it.
  NO  -> Accept as non-goal with not-present checks.
```

## Forbidden Artifact Matrix

| Artifact type | Why it is risky | Safer treatment |
| --- | --- | --- |
| `501 coming soon` endpoint | Creates attack surface and consumer expectation. | Do not define route until feature is in scope. |
| Nullable future column | Adds permanent ambiguous data semantics. | Add migration only when future feature is approved. |
| Reserved enum/status value | Consumers may branch on unimplemented state. | Keep enum limited to released states. |
| Hidden/no-op UI control | Users or tests can discover dead behavior. | Omit UI until behavior exists. |
| Future feature flag | Implies deployable behavior and adds config debt. | Create flag with the actual scoped implementation. |
| Permission bit for future action | Confuses role policy and audit review. | Add permission when action exists. |
| Unused job/event/topic | Adds operational and contract surface. | Add producer/consumer contract when needed. |
| Placeholder docs | Publicly promises unsupported behavior. | Document only released or explicitly planned roadmap items. |

## Acceptance Exclusion Matrix

| Exclusion | Example evidence | Strong check |
| --- | --- | --- |
| Endpoint not present | Route table, OpenAPI diff, integration 404. | Contract test or generated spec diff. |
| Field not present | Response schema, DTO test, generated client diff. | Contract test against v1 response. |
| UI action not rendered | Component/route test, screenshot, manual review. | Accessibility query confirms no action by name/role. |
| DB artifact not added | Migration diff, schema dump. | Migration validator and schema snapshot. |
| Permission not introduced | Role/policy diff, permission registry. | Policy test or permission matrix review. |
| Job/event not emitted | Job registry, topic list, event contract. | Integration test or contract schema check. |
| Docs do not promise behavior | Public docs diff, help text review. | Release-note and docs validation. |

## Graph, Memory, And Trajectory Coupling

| Input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current routes, schemas, migrations, UI actions, permission policies, jobs, events, docs, and tests were inspected. | Graph proximity is treated as proof that a surface is in or out of scope. |
| Project memory | Memory names unchanged version boundary, owners, date, and affected surfaces. | Memory predates route/schema/role/customer/SLA changes or lacks freshness evidence. |
| Execution trajectory | Validation ran after the final scope-related edit and covers excluded artifacts. | Evidence predates final edits or only validates in-scope happy paths. |
| Stakeholder record | Owner, date, and authority are clear. | A chat summary or vague roadmap note is used as binding scope. |
| Existing tests | Tests assert both included behavior and excluded behavior where relevant. | Tests cover only success paths and cannot detect scope creep. |

Strong outputs state which graph or memory evidence was accepted, rejected, or left unknown.

## Review Questions

1. What exact behavior, actors, surfaces, and data are in scope for this release?
2. What exact behavior, endpoints, fields, UI, jobs, events, roles, migrations, docs, and metrics are excluded?
3. Which excluded items could be confused with required security, compliance, reliability, accessibility, or compatibility work?
4. Which deferred decisions are blocking, non-blocking, or owned follow-ups?
5. What must the current implementation not assume about future versions?
6. Does v1 keep a clean path to v2 without adding speculative surface area?
7. Which acceptance checks prove excluded behavior is not present?
8. Which source paths, registry entries, docs, tests, graph facts, memory facts, and execution results were inspected?
9. Which old assumptions or nearby patterns were rejected as stale?
10. Which specialist gate owns any residual risk?

## Anti-Patterns To Reject

| Anti-pattern | Why it fails | Required correction |
| --- | --- | --- |
| "Admin features are out of scope." | Vague category cannot be verified. | Name excluded endpoints, actions, roles, and UI. |
| "Security is a non-goal for v1." | Baseline safety cannot be removed from in-scope behavior. | Move required controls into scope or block. |
| Nullable v2 fields in v1 response. | Creates consumer contract and ambiguous semantics. | Remove field until v2 contract exists. |
| Hidden "coming soon" tab. | Exposes unimplemented behavior and creates support burden. | Omit tab; document roadmap separately if approved. |
| No exclusion checks. | QA cannot detect scope creep. | Add not-present acceptance and review checks. |
| Stale project memory copied into scope. | Old assumptions outlive current contracts. | Confirm against current source, owner, and validation. |
| Deferred decision has no owner. | Non-goal becomes permanent accidental product decision. | Assign owner, trigger, and escalation rule. |
| Future compatibility ignored. | v1 blocks v2 or requires breaking migration. | Record compatibility judgment and accepted migration cost. |

## Handoff Boundaries

- Use `requirement-clarification` when the boundary depends on an unanswered authority decision.
- Use `requirement-structuring` when confirmed facts need a full change brief.
- Use `scenario-decomposition` when non-goals constrain scenario space.
- Use `acceptance-standard-definition` when exclusion checks need falsifiable done standards.
- Use `quality-test-gate` when not-present checks require runnable validation.
- Use `data-api-contract-changer` for API, schema, event, version, DTO, and migration compatibility.
- Use `security-privacy-gate` when a proposed non-goal touches authorization, privacy, secrets, or security controls.
- Use `reliability-observability-gate` when an exclusion affects alerts, dashboards, rollback, incident response, SLOs, or operations.
- Use `delivery-release-gate` when deferred scope affects rollout, release notes, migration rollout, or rollback.
- Use `task-dag-planner` after boundaries are accepted and sequencing can begin.
