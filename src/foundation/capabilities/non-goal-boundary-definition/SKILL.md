---
name: non-goal-boundary-definition
description: Defines in-scope and out-of-scope boundaries, version limits, anti-scope-creep controls, and assumptions that must not leak into implementation.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "06"
changeforge_version: 0.1.0
---

# Mission

**Protect implementation focus by making non-goals, version boundaries, exclusions, and deferred decisions explicit, testable, and enforceable** so reviewers can identify unauthorized scope expansion, implementers know which adjacent work is out of scope, and no deferred decision leaks into current APIs, data schemas, permissions, UI, jobs, flags, observability, or user-visible states without a conscious contract.

# When To Use

Use this capability when a change request risks expanding into adjacent workflows, redesigns, migrations, platform changes, UX refreshes, policy changes, or "while we are here" work; defines a first version with assumptions about later versions; has multiple stakeholders with different scope expectations; needs explicit current-release versus deferred-release boundaries; or uses repository graph, project memory, prior plans, or execution history that could accidentally promote old assumptions into current scope.

# Do Not Use When

Do not use this capability to avoid required risk work by labeling it a non-goal, suppress legitimate technical dependencies, defer decisions that block correctness or safety, or decide unknown product/security/legal answers without authority. Use `requirement-clarification` when the unknown itself blocks coding, `requirement-structuring` when confirmed facts need a traceable brief, and `acceptance-standard-definition` when the in-scope done signal needs precision.

# Stage Fit

Use during requirement intake, implementation planning, coding, code-review, refactoring, debugging, testing, quality gate preparation, and release-readiness when scope pressure, version staging, deferred decisions, or boundary disputes could affect implementation. In planning, define exact inclusions, exclusions, forbidden artifacts, safe future compatibility constraints, and acceptance exclusions before task sequencing. In coding/review, reject speculative endpoints, nullable fields, reserved roles, hidden UI, feature flags, migrations, metrics, jobs, or adapters added for deferred work. In debugging or repair, distinguish the smallest required fix from adjacent cleanup, redesign, migration, and "while here" work. Hand off when the primary issue is unclear authority, scenario coverage, test-layer selection, architecture sequencing, release governance, or specialist security/reliability validation.

# Non-Negotiable Rules

- **Non-goals must be specific and testable as exclusions.** "We are not building a full admin portal" is not checkable. "User management CRUD (POST/PUT/DELETE /admin/users) is not in v1; these endpoints and UI actions must not exist" is checkable.
- **Version boundaries must state what the current release will and will not do.** A v1 boundary defines included behavior, excluded behavior, immutable contracts, compatibility assumptions, and forbidden future-preparation artifacts.
- **Deferred decisions must not create placeholder behavior.** A non-goal excludes scope. It does not permit empty endpoints, nullable columns, reserved enum values, permission stubs, no-op UI controls, future flags, unused jobs, or hidden API fields.
- **Required security, data integrity, reliability, accessibility, compliance, and compatibility work cannot be made a non-goal.** If the in-scope feature requires a control to be safe, that control is in scope or the feature is blocked.
- **Deferred scope must not contradict customer, legal, security, platform, SLA, or migration commitments.** Existing commitments outrank local scope preference.
- **Acceptance criteria must include "not present" checks for non-goals.** Every accepted non-goal produces at least one exclusion check in QA, review, contract validation, API schema validation, migration review, or UI inspection.
- **Future compatibility must be acknowledged without speculative surface area.** v1 should avoid closing the door on v2, but must not add artifacts whose only purpose is unapproved future scope.
- **Graph, memory, and trajectory evidence are advisory until source-confirmed.** Prior plans, nearby files, stale TODOs, old tickets, and previous execution results cannot expand current scope unless current source, registry, docs, tests, and stakeholder authority confirm them.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| V1 scope boundary | First release, MVP, phased delivery, or "not now" decisions. | Exact included/excluded behavior and forbidden artifacts. | Current scope source, excluded surfaces, version contract, acceptance exclusions. | `requirement-structuring`, `acceptance-standard-definition` | Future scaffolding. |
| Anti-scope-creep review | PR, plan, or task list adds adjacent work. | Detect unapproved endpoints, schema, UI, jobs, flags, roles, events, or docs. | Diff/path inventory, out-of-scope map, same-pattern search. | `change-impact-analyzer`, `plan-execution-consistency` | Opportunistic cleanup unless approved. |
| Deferred decision control | Unknown future behavior, product debate, dependency pending, or authority gap. | Separate deferrable choices from blockers and prevent hidden assumptions. | Decision owner, safe current constraint, forbidden assumption, follow-up trigger. | `requirement-clarification`, `user-role-identification` | Silent defaults for authority questions. |
| Contract and compatibility boundary | API/schema/event/version/data model may change later. | Keep current contract stable and future extension possible without placeholder fields. | API/schema surface, consumer impact, migration risk, compatibility note. | `version-compatibility`, `data-api-contract-changer` | Nullable future fields in current contract. |
| Risk-sensitive exclusion | Security, compliance, reliability, performance, accessibility, money, data loss, or auth is proposed as out of scope. | Decide whether exclusion is invalid, accepted with risk owner, or requires specialist gate. | Requirement risk, control owner, compensating control, written risk acceptance. | `security-privacy-gate`, `reliability-observability-gate`, `quality-test-gate` | Treating baseline controls as optional. |
| Evidence reuse boundary | Repository graph, project memory, old plan, or prior validation suggests scope. | Accept, reject, or downgrade reuse based on freshness and current source. | Inspected paths, accepted/rejected memory, final-edit validation freshness. | `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis` | Copying stale non-goals. |

# Industry Benchmarks

Anchor against INVEST testability and small-scope discipline, IETF RFC "out of scope" practice, Shape Up appetite and rabbit-hole control, IEEE/ISO requirements traceability, TOGAF scope inclusions/exclusions, Google design-doc non-goals, OKR focus discipline, and product backlog slicing. Keep the body focused on routing, evidence, output, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for classification matrices, version-boundary templates, decision trees, graph/memory/trajectory coupling, anti-pattern review, and benchmark anchors.

# Selection Rules

Select this capability when the primary need is **containing scope and making exclusions explicit, testable, and enforceable**. Route elsewhere when the problem is unresolved authority (`requirement-clarification`), confirmed requirement structure (`requirement-structuring`), scenario coverage (`scenario-decomposition`), in-scope done standards (`acceptance-standard-definition`), sequencing (`task-dag-planner`), or specialist control design (`security-privacy-gate`, `reliability-observability-gate`, `data-api-contract-changer`, `delivery-release-gate`).

# Proactive Professional Triggers

- **Signal:** A plan says "later", "future-proof", "while here", "coming soon", "v2", "for now", or "placeholder".
  **Hidden risk:** hidden placeholder endpoints, fields, jobs, or flags create contract pollution and missing validation.
  **Required professional action:** require a forbidden-artifact scan and document acceptance exclusions.
  **Route to:** `non-goal-boundary-definition`, `acceptance-standard-definition`.
  **Evidence required:** route scan, schema diff, UI/job/flag review, and not-present validation checks.
- **Signal:** A proposed non-goal touches auth, security, privacy, compliance, money, data loss, reliability, accessibility, or compatibility.
  **Hidden risk:** hidden auth, privacy, reliability, accessibility, or compatibility control gap reaches release.
  **Required professional action:** reject the non-goal, move the control into scope, or require explicit risk acceptance and specialist gate.
  **Route to:** `security-privacy-gate`, `reliability-observability-gate`, `quality-test-gate`.
  **Evidence required:** control decision, owner, compensating control, residual risk.
- **Signal:** Repository graph or project memory suggests an old boundary.
  **Hidden risk:** stale scope, renamed routes, changed consumers, or retired assumptions become current requirements.
  **Required professional action:** inspect current source/registry/tests/docs before reuse and mark stale evidence.
  **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`.
  **Evidence required:** source path scan, docs/tests review, accepted/rejected reuse judgment, and freshness report.
- **Signal:** Implementation adds nullable columns, reserved enum values, no-op endpoints, permission bits, hidden tabs, event topics, or feature flags for future work.
  **Hidden risk:** current contract is polluted by unapproved future behavior.
  **Required professional action:** scan the diff, require removal of speculative surface, or route formal re-scope.
  **Route to:** `data-api-contract-changer`, `architecture-impact-reviewer`.
  **Evidence required:** diff search, removed/preserved artifact decision, compatibility note.
- **Signal:** A non-goal has no QA/review exclusion check.
  **Hidden risk:** missing validation evidence lets hidden scope creep pass while only in-scope success is tested.
  **Required professional action:** require not-present acceptance checks and changed-scope-to-validation mapping.
  **Route to:** `acceptance-standard-definition`, `quality-test-gate`.
  **Evidence required:** not-present validator, review checklist, validation command or manual report, and residual risk.
- **Signal:** Final validation proves only in-scope happy paths after scope-related edits.
  **Hidden risk:** unverified out-of-scope artifacts ship because validation evidence is stale or incomplete.
  **Required professional action:** verify exclusion checks after the final scope edit and record what the evidence does not prove.
  **Route to:** `validation-broker`, `plan-execution-consistency`.
  **Evidence required:** command/report path, exit code or manual review result, changed scope, freshness, and residual risk.

# Risk Escalation Rules

Escalate when a proposed non-goal would leave unsafe partial behavior, violate backward compatibility, defer required migration or data integrity work, create a user-visible dead state, contradict a customer/legal/security/platform/SLA commitment, remove an operational recovery path, or make v2 impossible without breaking the v1 API or schema. Escalate to the owning gate when a deferred item affects authorization, privacy, payments, accessibility, reliability, compliance, external integrations, migrations, or irreversible side effects.

# Critical Details

- **"Not now" still needs future compatibility judgment.** A non-goal means excluded from the current release, not permanently impossible. Record whether v1 keeps a clean path to v2 without speculative artifacts.
- **Security and correctness exclusions require named ownership.** "Rate limiting is not in scope" is acceptable only when the endpoint exposure, compensating controls, and accepting owner are explicit. Otherwise it is a blocker.
- **Placeholder artifacts are scope violations.** A `501 coming soon` endpoint, nullable future field, reserved enum, hidden button, unused role, or future flag creates contract and attack surface. Remove it unless the feature is actually in scope.
- **Non-goals interact with API versioning and consumer expectations.** Do not include v2 fields as nulls in v1 responses. Do not add schema fields, events, flags, or docs that imply support before the capability is accepted.
- **Reviewers need a mechanical check.** Each non-goal should translate to a diff search, schema review, OpenAPI/contract check, UI route check, migration review, or explicit manual inspection.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 selection, stage fit, routing, evidence, output, and gates. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete scope boundary, non-goal list, anti-scope-creep review, or acceptance exclusions. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when detailed benchmark anchors, classification matrices, version-boundary templates, graph/memory/trajectory coupling, review questions, or anti-pattern analysis is needed. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load references for pure routing or trivial wording changes where the inline output contract and quality gate are enough.

# Failure Modes

- **Vague exclusion:** "no admin features" lets user-management endpoints appear because no excluded surfaces were named.
- **Invalid risk deferral:** GDPR, auth, rate limiting, or data retention is deferred as a non-goal even though the in-scope feature processes protected data.
- **Speculative contract surface:** nullable future fields, reserved roles, or hidden UI are added for v2 and become permanent ambiguous contract surface.
- **Missing exclusion evidence:** non-goals have no acceptance exclusions, so QA verifies only the included behavior and misses deployed out-of-scope endpoints.
- **Stale memory expansion:** project memory from an old plan is reused after routes, roles, schema, or customer commitments changed.
- **Unbounded volume assumption:** "No pagination in v1" is accepted without volume assumption, and the current release times out under realistic data growth.
- **Hidden release promise:** placeholder docs, roadmap copy, or help text promises an excluded capability and support treats it as committed behavior.
- **Stale validation closure:** final evidence predates a route, schema, UI, job, flag, or docs edit, so the handoff overclaims scope containment.

# Output Contract

Return a scope boundary record with:

- `mode_selected` (v1 scope boundary / anti-scope-creep review / deferred decision control / contract and compatibility boundary / risk-sensitive exclusion / evidence reuse boundary)
- `scope_boundary` (current version, authority owner, release boundary, in-scope behavior, out-of-scope behavior, and excluded surfaces)
- `source_evidence` (request/ticket, current docs, registry, source paths, API/schema specs, tests, repository graph, project memory, execution trajectory, stakeholder commitments, and freshness limits)
- `graph_memory_trajectory_judgment` (accepted, rejected, or not verified for each reused scope boundary, non-goal, prior plan, route, schema, test, or validation result)
- `in_scope` (specific behaviors, actors, contexts, endpoints, jobs, UI elements, data entities, permissions, events, and observability that are included)
- `out_of_scope` (specific non-goals with excluded behavior, deferred-to version/backlog item, reason, owner, and forbidden placeholder artifacts)
- `version_boundary` (current contract for API shape, DB schema, permissions, UI, jobs, flags, events, docs, and what is immutable once released)
- `deferred_decisions` (decision, owner, deadline or trigger, why it is non-blocking or blocking, and current implementation constraint)
- `forbidden_assumptions` (columns, endpoints, enum values, roles, UI elements, flags, jobs, events, docs, metrics, or behavior that must not exist now)
- `future_compatibility_judgment` (whether v1 keeps a clean path to v2, known migration cost, and rejected speculative scaffolding)
- `acceptance_exclusions` (not-present checks for each non-goal: API/schema/UI/route/migration/permission/job/event/metric/doc/review evidence)
- `anti_scope_creep_checklist` (PR review checks for out-of-scope endpoints, fields, migrations, permissions, flags, UI, events, jobs, tests, and docs)
- `risk_acknowledgement` (for deferred security/compliance/reliability/accessibility/money/data work: owner, date, compensating control, and why it is acceptable or blocked)
- `validation_commands` (command or review procedure, validator/tool, artifact/report path, output/exit code or manual result, changed scope, and freshness after the final scope-related edit)
- `changed_scope_to_validation_map` (each included behavior, excluded surface, forbidden artifact, compatibility constraint, deferred decision, and risk acknowledgement mapped to a test, validator, review check, or residual risk)
- `handoff_boundaries` (what belongs to clarification, structuring, scenarios, acceptance, quality tests, security, reliability, data/API contracts, release, or task planning)
- `evidence_limits` (what was not inspected or validated: live system, production data, customer contracts, current permissions, generated specs, UI routes, migrations, docs, tests, or final validation freshness)

# Evidence Contract

Close a scope-boundary output only when it names the selected mode, current scope boundary, source evidence, graph/memory/trajectory reuse judgment, boundaries inspected, exact inclusions, exact exclusions, version contract, deferred decisions, forbidden assumptions/artifacts, future compatibility judgment, acceptance exclusions, changed-scope-to-validation map, handoff boundaries, residual risk, and evidence limits. A non-goal list without "not present" checks, source evidence, and forbidden artifacts is not sufficient evidence.

Validation evidence must name command or review procedure, validator, artifact/report path, output and exit code or manual result, changed scope, and freshness after the final scope-related edit. State what evidence proves, what evidence does not prove, reuse and placement rationale for graph/memory/trajectory claims, behavior preservation for existing in-scope contracts, and next gate or handoff owner.

# Benchmark Coverage

Improved outputs reject weak patterns: vague category non-goals, "future-proof" scaffolding, placeholder endpoints, nullable v2 fields, hidden no-op UI, baseline security as optional, unowned deferred decisions, missing exclusion tests, stale project-memory scope, and scope boundaries that make v2 impossible. Detailed benchmark anchors, templates, decision trees, review questions, graph/memory/trajectory coupling, and anti-pattern matrices belong in references so the body remains efficient.

# Routing Coverage

Route here when scope containment, non-goals, version limits, excluded surfaces, deferred decisions, forbidden artifacts, future compatibility, or anti-scope-creep review is primary. Hand off when the primary concern is unresolved authority (`requirement-clarification`), confirmed behavior brief (`requirement-structuring`), scenario path coverage (`scenario-decomposition`), falsifiable done standards (`acceptance-standard-definition`), test-layer strategy (`quality-test-gate`), security/privacy control design (`security-privacy-gate`), reliability/ops readiness (`reliability-observability-gate`), API/schema compatibility (`data-api-contract-changer`), or task ordering (`task-dag-planner`).

# Quality Gate

The scope boundary is complete only when:

1. Selected mode, scope boundary, source evidence, and graph/memory/trajectory reuse judgment are explicit.
2. Every non-goal is specific enough to be checked by test, schema/API validation, UI inspection, diff review, or PR review.
3. Acceptance criteria include explicit exclusion checks for every non-goal.
4. Forbidden placeholder artifacts are listed and checked.
5. Deferred security, compliance, reliability, accessibility, money, data integrity, or compatibility work is justified with explicit risk acknowledgement or moved into scope.
6. The current API, schema, permissions, UI, jobs, flags, events, and docs avoid speculative future surface while preserving stated future compatibility where required.
7. Every deferred decision has an owner, trigger or deadline, blocking/non-blocking classification, and "must not assume" constraint.
8. Non-goals are reviewed against customer, legal, security, platform, SLA, release, and migration commitments.
9. Changed-scope-to-validation mapping covers every included behavior, excluded surface, forbidden artifact, deferred decision, compatibility constraint, and risk acknowledgement.
10. Validation commands or review procedures, validators, artifacts/reports, output/exit code or manual result, changed scope, and freshness are recorded for every exclusion, forbidden artifact, and accepted residual risk.
11. Handoff boundaries and evidence limits are explicit so non-goal definition is not over-claimed as clarification, acceptance, test execution, security sign-off, reliability sign-off, or release approval.

# Used By

- change-intake-compiler
- acceptance-criteria-builder
- task-dag-planner

# Handoff

Hand off to `requirement-clarification` when an exclusion may actually be a blocking decision; `requirement-structuring` when confirmed facts need a traceable brief; `scenario-decomposition` when excluded paths affect scenario boundaries; `acceptance-standard-definition` when exclusion checks need falsifiable done standards; `quality-test-gate` when not-present checks require executable validation; `data-api-contract-changer` for API/schema/version compatibility; `security-privacy-gate` or `reliability-observability-gate` when a proposed exclusion touches baseline controls; and `task-dag-planner` for sequencing approved in-scope work.

# Completion Criteria

The capability is complete when **every non-goal is a specific, testable exclusion with forbidden artifacts, acceptance exclusions, source evidence, future compatibility judgment, changed-scope-to-validation mapping, explicit handoff boundaries, and evidence limits; no deferred security or compliance work is silently excluded; and the current implementation path is protected from speculative future scope**.
