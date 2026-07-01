---
name: requirement-structuring
description: Structures raw change input into a professional change brief covering behavior, trigger, actor, scope, non-goals, constraints, acceptance signals, and test traceability.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "02"
changeforge_version: 0.1.0
---

# Mission

**Transform confirmed requirement facts into a stable, implementation-neutral change brief** that describes current behavior, desired behavior, trigger, actor, scope, non-goals, constraints, acceptance signals, and test traceability — giving every downstream capability (design, planning, implementation, testing) a single authoritative source of truth that can be traced end-to-end from requirement to verified outcome.

# When To Use

Use this capability when: a request is unambiguous and clarified (all blocking unknowns are resolved — see `requirement-clarification`) but still needs professional structure before design or implementation begins; an incoming requirement is expressed as a code change ("change this function") rather than a behavior change ("users should be able to do X"); a new feature, bug fix, or behavior change needs a test traceability matrix before the implementation starts; or a change spans multiple surfaces (API, frontend, database, configuration) and a single structured brief is needed to coordinate all implementers.

Also use it when repository graph, project memory, or execution traces contain facts that must be accepted, rejected, or bounded before they become a downstream implementation plan, test plan, schema, API, migration, release, or review claim.

# Do Not Use When

Do not use this capability to: resolve unresolved authority questions (use `requirement-clarification` first); expand scope beyond the confirmed request ("while we're here, we could also…"); encode implementation tasks before behavior has been described; or produce implementation-specific designs (architecture, schema, API contract — those follow from the structured brief, they are not part of it).

# Stage Fit

- **Requirement intake stage:** turn confirmed facts into an implementation-neutral change brief after blocking unknowns are resolved.
- **Planning:** make scope, non-goals, constraints, dependencies, and verification paths stable before tasks are sequenced.
- **Review:** reject plans or diffs that cannot trace back to current behavior, desired behavior, non-goals, constraints, and acceptance signals.
- **Handoff:** pass explicit evidence limits, residual unknowns, and next capability owner instead of letting downstream skills infer intent.

# Non-Negotiable Rules

- **Describe current behavior as observable system behavior, not as speculation or source code description.** "The API returns 200 with an empty array" is an observable behavior. "The service calls `findAll()` and returns the result" is a code description — it says nothing about observable behavior. Rule: current behavior must be described as: what input → what output / side effect / state change, for which actor, under which precondition. If current behavior is unknown, that is a blocking unknown that must be resolved (via `requirement-clarification`) before structuring.
- **Describe desired behavior as the outcome the user or system needs, before naming implementation.** "Users should be able to cancel a pending order and receive a refund" is a desired behavior. "Add a DELETE /api/orders/:id endpoint" is an implementation choice. The implementation must follow from the behavior — not the other way around. Rule: desired behavior is written as: [Actor] can/must/must not [perform action / observe outcome] [when/given precondition]. Implementation choices belong in design, not in the requirement brief.
- **Non-goals must be explicit and specific.** Vague non-goals like "out of scope for this sprint" are not useful. Specific non-goals prevent scope creep: "Does NOT change the subscription billing cycle" is specific and prevents a developer from interpreting "cancel order" as implying subscription cancellation. Rule: every non-goal must be specific enough that an implementer cannot accidentally implement it while building the in-scope work.
- **Every meaningful requirement must trace to at least one verification artifact.** Verification artifact types: unit test (specific function/method behavior), integration test (cross-layer behavior), contract test (API consumer compatibility), E2E test (end-to-end user flow), migration test (data integrity after schema change), manual review artifact (accessibility audit, security review, compliance sign-off), observability signal (metric emitted, log entry, alert firing). A requirement with no verification path is not implementable — it has no done signal.
- **Constraints must be binding, not informative.** A constraint is not "we should try to keep response time reasonable." A constraint is "p99 response time must be ≤ 200ms under the production load baseline (measured in staging)." Constraints in the brief bind the implementation. If a constraint cannot be bound to a measurable criterion, it should not be listed as a constraint — it should be listed as a risk or noted as a quality concern for the quality gate.
- **Scope must include affected surfaces and explicit exclusions.** "In scope: the order cancellation API endpoint, the order status state machine, the refund initiation trigger. Out of scope: refund processing, subscription management, notification delivery." If a surface is not explicitly named in-scope or out-of-scope and an implementer touches it, the brief has failed to bound the change.
- Requirement facts must carry **repository evidence** (current source/docs/tests or explicit gap), **memory evidence** (prior decision accepted/rejected with freshness), **graph evidence** (affected surfaces and downstream consumers), and **execution evidence** (validation or review artifact that can prove the brief later).

# Industry Benchmarks

Anchor against ISO/IEC/IEEE 29148 and IEEE 830 for complete, consistent, unambiguous, verifiable, traceable, and feasible requirements; BDD/Gherkin for Given/When/Then acceptance language; ATDD for pre-implementation acceptance thinking; INVEST for small, testable requirement slicing; agile ready criteria for dependencies and authority; RFC 2119 for binding language; and ISO/IEC 25010 for quality constraints. Keep templates in `examples/example-output.md`, concrete review prompts in [references/checklist.md](references/checklist.md), deeper matrices in [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md), and closure proof rules in [references/evidence-patterns.md](references/evidence-patterns.md) so this body stays focused on routing, evidence, and gates.

# Mode Matrix

| Mode | Trigger signal | Minimum professional output | Evidence required | Handoff / skip by default |
| --- | --- | --- | --- | --- |
| Brief creation | Confirmed facts are known but not stable enough for coding, bug-fix planning, refactoring, or release review. | Current behavior, desired behavior, actor, trigger, scope, non-goals, constraints, dependencies, assumptions, and acceptance signals. | Source of current behavior, owner of desired behavior, and skipped boundary rationale. | Hand off to scenario, acceptance, or implementation planning; skip implementation design. |
| Traceability | Requirement, non-goal, constraint, or dependency lacks a test/review path. | Requirement-to-test/review map, verification type, evidence owner, and unresolved evidence gaps. | Planned test/review artifact, evidence owner, and what evidence does not prove. | Hand off to `quality-test-gate`; skip test implementation details. |
| Scope boundary | Confirmed facts span multiple surfaces or have ambiguous exclusions. | In-scope surfaces, excluded surfaces, adjacent capabilities, non-goal not-present checks, and authority owner. | Affected graph surfaces, forbidden artifacts, and owner for disputed scope. | Hand off to `non-goal-boundary-definition`; skip speculative future scaffolding. |
| Evidence freshness | Repository graph, project memory, stakeholder claim, old validation, or generated artifact is reused. | Accepted/rejected repository, graph, memory, stakeholder, and execution evidence with source and freshness limit. | Current-source check, memory status, execution freshness, and validation gap. | Hand off to graph, memory, or validation owner; skip treating memory as fact. |
| Handoff | Downstream plan, code-review, testing, or release gate needs an authoritative requirement anchor. | Next capability, residual unknowns, validation obligations, and what the brief does not authorize. | Brief-to-downstream map, residual-risk owner, and plan-vs-brief consistency check. | Hand off to the next selected capability; skip closure if traceability is missing. |

# Selection Rules

Selection boundary: use this capability to stabilize confirmed requirement facts into a behavior-first brief; do not use it to answer unresolved authority questions, define implementation design, or replace downstream acceptance/scenario planning.

Select this capability when **known requirement facts need professional structure before implementation begins**. Route elsewhere when: `requirement-clarification` is primary (open questions must be resolved before structuring); `acceptance-standard-definition` is primary (the behavior is known, but what "done" looks like needs precision); `use-case-modeling` is primary (a complex multi-actor workflow needs path-level decomposition — single actor + single flow briefs may be insufficient); `scenario-decomposition` is primary (a large brief needs to be decomposed into independently implementable scenarios for task planning).

Use **with** `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker` when the brief must prove source evidence, accepted/rejected memory, affected graph surfaces, and downstream validation obligations.

# Risk Escalation Rules

Escalate when: the structured brief reveals conflicting desired behaviors (two acceptance criteria contradict each other — requires product authority resolution before design begins); a constraint cannot be expressed as a measurable criterion (vague performance or compliance constraint — requires clarification from the constraint owner); the brief exposes a dependency on an external contract, partner API, or legal agreement that has not been confirmed (requires confirmation before the brief is approved); the scope boundary is disputed between teams (two teams claim ownership of the same surface — requires architecture or product resolution); or the change has backward-compatibility implications for existing API consumers that were not stated in the original request.

# Proactive Professional Triggers

- **Signal:** A request names an implementation, file, endpoint, schema, job, UI, or config change but not current behavior, desired behavior, actor, trigger, or acceptance signal. **Hidden risk:** downstream work satisfies the named mechanism while missing the required user/system outcome. **Required professional action:** rewrite into behavior-first current/desired behavior, actor, trigger, scope, non-goals, and acceptance signals before planning. **Route to:** `requirement-structuring`, `acceptance-standard-definition`. **Evidence required:** structured brief, implementation-choice deferral, and requirement-to-validation map.
- **Signal:** Confirmed facts span API, frontend, data, job, integration, config, release, docs, or support surfaces. **Hidden risk:** one implementer changes an unstated adjacent surface or omits a required dependency because the brief has no graph boundary. **Required professional action:** map in-scope and excluded surfaces, downstream owners, dependencies, and non-goal not-present checks. **Route to:** `requirement-structuring`, `repository-graph-analysis`, `non-goal-boundary-definition`. **Evidence required:** affected-surface graph, non-goal list, dependency owner, and skipped-surface rationale.
- **Signal:** Project memory, prior plan, ticket text, stakeholder claim, previous test output, or generated artifact is reused as requirement evidence. **Hidden risk:** stale or unverified memory becomes the source of truth and invalidates design, tests, or release decisions. **Required professional action:** accept, reject, or mark each evidence source stale against current source/docs/tests before it enters the brief. **Route to:** `requirement-structuring`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** evidence freshness table, accepted/rejected facts, and owner for unresolved claims.
- **Signal:** A constraint says fast, secure, compatible, reliable, compliant, scalable, simple, or safe without a measurable threshold or named standard. **Hidden risk:** downstream gates cannot prove the requirement and teams dispute completion after implementation. **Required professional action:** convert the constraint into a measurable criterion or hand it to acceptance/performance/security owners. **Route to:** `requirement-structuring`, `acceptance-standard-definition`, `quality-test-gate`. **Evidence required:** measurable constraint, evidence type, acceptance owner, and residual gap if not measurable.
- **Signal:** Requirements contain non-goals, deferred decisions, compatibility promises, rollback limits, or authority-sensitive behavior. **Hidden risk:** scope creep or hidden authority decisions appear in implementation despite the brief being treated as approved. **Required professional action:** name forbidden work, approval owner, downstream gate, validation/not-present check, and handoff boundary. **Route to:** `requirement-structuring`, `requirement-clarification`, `plan-execution-consistency`. **Evidence required:** non-goal not-present checks, authority owner, downstream gate, and residual-risk owner.
- **Signal:** A downstream plan, task DAG, or code diff cannot point back to a structured brief. **Hidden risk:** implementation and validation drift from the authorized requirement. **Required professional action:** stop closure and reconstruct the brief-to-downstream map before approving the plan or diff. **Route to:** `plan-execution-consistency`, `quality-test-gate`. **Evidence required:** changed plan/diff item, source requirement, validation artifact, and residual-risk owner.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 routing, selection rules, output contract, and quality gates. Load references only when their decision surface is active:

- **L1:** Read this `SKILL.md` only for routing, compact brief creation, or small review where the brief shape is obvious.
- **L2:** Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete structured brief, traceability matrix, or scope/non-goal checklist.
- **L3:** Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when benchmark anchors, requirement quality matrices, behavior-first conversion, compatibility, constraint classification, graph/memory/execution coupling, or anti-pattern review needs more depth.
- **Evidence closure:** Load [references/evidence-patterns.md](references/evidence-patterns.md) when repository evidence, project memory, repository graph, execution trajectory, validation freshness, forbidden-artifact checks, tool boundary, or proof limits decide whether a brief can hand off.
- **Shape example:** Use [examples/example-output.md](examples/example-output.md) only when the expected response shape is unclear or the user needs a filled compact brief format.
- **Adjacent skills:** Do not load adjacent skills by default. Load `requirement-clarification`, `acceptance-standard-definition`, `scenario-decomposition`, or `non-goal-boundary-definition` only when unresolved authority, done standards, scenario coverage, or exclusions are the primary gap.

# Critical Details

- **The brief is the traceability anchor, not a specification document.** It does not describe implementation. It describes what must be true after implementation. Every subsequent artifact (API design, database schema, test cases, release plan) should be traceable to the brief. If a test cannot be traced to a requirement in the brief, the test is either testing internal implementation (acceptable but not traced) or testing something out of scope (requires brief amendment).
- **Current behavior description prevents regression.** If current behavior is not documented, future implementers cannot distinguish "this changed intentionally" from "this regressed accidentally." The current behavior description serves as the baseline for regression test design.
- **Test traceability matrix is written before implementation, not after.** Writing the traceability matrix after implementation means it maps to what was built, not to what was required. Writing it before ensures all requirements have a verification path and that any unverifiable requirement is identified before anyone builds it.
- **"Done" is defined by the acceptance signals, not by the implementation task list.** A change is done when the acceptance signals are verifiably met, not when the implementation tasks are checked off. A developer who completes all tasks but the acceptance signals are not met has not delivered the requirement.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| Current behavior: "The function currently calls findById" | Describes code, not observable behavior; useless for regression detection | "The API returns 404 when the order ID does not exist" |
| Desired behavior: "Add a DELETE /api/orders/:id endpoint" | Describes implementation, not outcome; forces implementation choice before design | "A customer should be able to cancel a pending order and receive a confirmation" |
| Non-goal: "Out of scope for this sprint" | Time-bound, not behavior-bound; next sprint can add anything without brief amendment | "Does NOT change notification delivery" (behavior-specific exclusion) |
| Constraint: "Response should be fast" | Not measurable; cannot be a done criterion; rubber-stamped | "p99 ≤ 200ms at production load baseline (measured in staging with k6)" |
| Acceptance signal: "It works correctly" | Not verifiable; depends on subjective judgment | Specific Given/When/Then scenario with observable outcome |
| No test traceability column | Requirement exists but no verification path; "done" is undefined | Traceability matrix: requirement → verification type → test ID |

# Failure Modes

- **Mechanism over behavior:** brief says "add the endpoint"; team implements the endpoint but misses the state transition, so the observable requirement is still false.
- **No current-behavior baseline:** refactor changes behavior and no regression boundary exists; the defect is discovered after release.
- **Vague non-goals:** developer adds notification delivery "while in there"; the notification service is not ready and release is delayed.
- **Unmeasurable constraint:** 800 ms response time ships under a "fast" requirement; no agreed p95/p99 baseline exists.
- **Late traceability:** traceability is written after implementation and maps to what was built, not what was required.
- **Compatibility omission:** field removed from an API response because backward compatibility was not named; existing consumer breaks and rollback is required.
- **Stale memory accepted as truth:** an old plan or generated artifact describes a retired route; downstream design and tests target a path that no longer exists.
- **Graph boundary gap:** an omitted job, config, doc, support flow, or migration surface changes implicitly because the structured brief did not name excluded surfaces.
- **Authority decision hidden:** product, security, legal, or reliability decision is treated as an assumption, then implementation encodes it without owner approval.

# Output Contract

Return a `structured_change_brief` with:

- `mode_selected` (brief creation, traceability, scope boundary, evidence freshness, or handoff)
- `summary` (one sentence: what changes and why)
- `current_behavior` (observable: actor → precondition → output/state, per affected surface)
- `desired_behavior` (outcome-first: [actor] can/must [achieve outcome] [when precondition])
- `trigger` (what initiates the behavior)
- `actor` (who initiates: role, authentication state)
- `in_scope_work` (explicit surface list with named components)
- `non_goals` (specific exclusions, behavior-bound)
- `constraints` (binding, measurable criteria per constraint)
- `assumptions` (safe engineering + explicit stakeholder, sourced)
- `dependencies` (external services, contracts, feature flags)
- `acceptance_signals` (verifiable Given/When/Then scenarios)
- `requirement_test_traceability` (per requirement: verification type, test ID/description)
- `graph_memory_execution_validation` (source files/docs/tests inspected, accepted/rejected memory, affected graph surfaces, validation artifacts or gaps)
- `brief_to_downstream_map` (each requirement/non-goal/constraint/dependency mapped to next capability, evidence type, and owner)
- `evidence_limits` (what remains unverified, stale, unavailable, authority-owned, or intentionally out of scope)
- `residual_risks` and `owner`

# Evidence Contract

An acceptable answer names:

- **Boundaries inspected:** request source, current behavior source, docs, tests, generated contracts, schemas, APIs, screens, jobs, configs, reports, graph, memory, and skipped boundaries with reason.
- **Repository evidence:** current behavior source, docs, tests, generated contracts, schemas, APIs, screens, jobs, configs, reports, or explicit evidence gap.
- **Memory evidence:** prior decisions, project conventions, stakeholder claims, old plans, old validations, or known constraints accepted, rejected, or marked stale.
- **Graph evidence:** affected surfaces, downstream consumers, dependencies, excluded surfaces, ownership boundaries, and non-goal not-present checks.
- **Execution evidence:** validation artifact, review check, test plan, acceptance owner, or command/report that can later prove each meaningful requirement.
- **What evidence proves:** which requirement, non-goal, constraint, dependency, or handoff is supported for the named actor, surface, source, and freshness window.
- **What evidence does not prove:** uninspected surfaces, stale memory, authority-owned decisions, production-only behavior, specialist risk, or implementation choices not authorized by the brief.
- **Handoff evidence:** next capability, residual unknowns, authority owner, residual risk, and evidence limits so downstream skills know what the brief does and does not authorize.

# Benchmark Coverage

- **Requirement quality:** complete, consistent, unambiguous, verifiable, traceable, feasible, and implementation-neutral.
- **Behavior structure:** current behavior, desired behavior, actor, trigger, precondition, outcome, scope, non-goals, constraints, dependencies, and assumptions.
- **Traceability:** requirement-to-acceptance, requirement-to-test/review, requirement-to-owner, and requirement-to-downstream-skill mapping.
- **Execution coupling:** graph/memory freshness, validation obligations, evidence limits, and residual-risk owner.

# Routing Coverage

This capability should route from prompts involving confirmed facts, change brief, current behavior, desired behavior, actor, trigger, scope, non-goals, constraints, dependencies, assumptions, acceptance signals, requirement traceability, and implementation-neutral structuring. Route away when blocking unknowns remain, acceptance standards need precision, scenario coverage is primary, or implementation design has already begun without a stable brief.

# Quality Gate

The structured brief is complete only when:

1. Current behavior is described as observable behavior, not code description.
2. Desired behavior is described as outcome, not implementation choice.
3. Every non-goal is specific enough to prevent unintentional scope expansion.
4. Every constraint is measurable and bound to a criterion.
5. Acceptance signals are written as verifiable scenarios (Given/When/Then).
6. Every meaningful requirement has at least one verification path.
7. In-scope work explicitly names all affected surfaces.
8. Non-goals explicitly exclude adjacent surfaces that could be ambiguous.
9. No blocking unknown remains unresolved.
10. The brief is approved by the requirement authority before design begins.
11. Repository, memory, graph, and execution evidence are accepted, rejected, or marked as evidence gaps with freshness limits.
12. Every requirement, non-goal, constraint, and dependency maps to a downstream owner, validation/review evidence, or residual-risk owner.
13. The brief states what it does not authorize: implementation choices, scope expansion, unresolved authority decisions, and unverified assumptions.

# Used By

- change-intake-compiler

# Handoff

Hand off to `scenario-decomposition` to break the brief into independently implementable tasks; `acceptance-standard-definition` to sharpen the done criteria; `task-dag-planner` for task sequencing and dependency planning; or the relevant domain professional skill (backend-change-builder, frontend-change-builder, etc.) when the brief is ready for implementation planning.

# Completion Criteria

The capability is complete when **the raw request is transformed into a bounded, traceable change brief where every requirement has a verification path, every non-goal is behavior-specific, every constraint is measurable, and the brief is approved before design or implementation begins**.
