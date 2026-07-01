---
name: senior-programming-judgment-core
description: Coordinates senior programming judgment for non-trivial engineering work by requiring purpose, source-backed facts, object relationships, state/behavior/rule constraints, invariants, boundaries, failure contract, side effects, reuse and placement, minimality, validation, observability, and residual-risk evidence before implementation or closure.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "136"
changeforge_version: 0.1.0
---

# Mission

Make senior programming judgment explicit for non-trivial engineering work. Before implementation or closure, require a compact evidence record that explains why the change exists, which facts are source-backed, which objects and relationships carry behavior, which states/rules/invariants must hold, which boundaries and side effects are touched, how failure is handled, why placement and minimality are correct, how validation proves behavior, what observability is needed or intentionally absent, and what residual risk remains.

This capability coordinates judgment across existing ChangeForge capabilities. It does not replace `implementation-structure-design`, `business-semantic-control-plane`, `agent-execution-discipline`, `code-clarity-maintainability`, `failure-contract-design`, `data-side-effect-flow-tracing`, or `validation-broker`.

# When To Use

Use for non-trivial engineering, skill-authoring, hook-runtime, routing, registry, eval, refactoring, bug-fix, API/data, reliability, security, or release work when the change could alter behavior, object ownership, state transitions, public/private boundaries, hidden rules, failure behavior, side effects, validation coverage, observability, or long-term maintainability.

Use before edits when a structural gate, route, or stage plan indicates new files, helpers, shared/common placement, public API, status/lifecycle changes, hidden controller/SQL/UI/test rules, state-machine behavior, generated code review, hook/runtime behavior, or skill/eval behavior changes.

# Do Not Use When

- Do not use as a persona, title, generic senior-developer article, motivational text, or top-level professional skill.
- Do not use for trivial typo, formatting, copy-only, or docs-only edits with no semantic or engineering behavior impact; record an allowed skip reason instead.
- Do not use to load personal archives, private corpora, private mapping artifacts, project-wide business documents, or user-specific technical content.
- Do not use to make `business-semantic-control-plane` own every programming judgment; BSP remains limited to task-scoped business meaning.
- Do not duplicate detailed placement, business, validation, failure, or side-effect rules already owned by specialist capabilities; select those capabilities when their risk is primary.

# Stage Fit

This capability adds evidence obligations to the active engineering stage. It does not create a new stage and does not launch every stage at once.

| Stage mode | Trigger signals | Professional focus | Required evidence | Companion capabilities / gates | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| Implementation planning | New file, helper, shared/common placement, public API, object/module ownership, or reuse uncertainty | Confirm purpose, facts, object ownership, boundaries, placement, and minimality before coding | `senior_programming_judgment` plus implementation preflight, reuse ladder, rejected locations, validation map | `implementation-structure-design`, `repository-context-map`, `quality-test-gate` | Skip for pure copy edits with no structural or semantic impact |
| Coding / bug-fix | Behavior, state, rule, invariant, failure path, or side effect changes | Keep implementation tied to facts, invariants, failure contract, side-effect map, and tests | changed behavior, old behavior preservation, state/rule/invariant mapping, rollback path | `agent-execution-discipline`, `failure-contract-design`, `data-side-effect-flow-tracing`, `regression-testing` | Skip only with explicit no-semantic-change reason |
| Review / refactoring | Generated code, moved behavior, file split/merge, hidden side effect, or over-abstraction | Review whether object relationships, boundaries, invariants, and validation still match reality | before/after behavior, object graph, side effects, validation proof, residual risk | `ai-code-review-refactor`, `code-review`, `code-clarity-maintainability`, `refactoring` | Do not approve from clean shape alone |
| Skill authoring / hook runtime | Skill, capability, routing, stage, hook, eval, benchmark, or closure behavior changes | Treat skill/runtime behavior as engineered behavior with evidence and regression fixtures | source/dist boundary, schema/state contract, behavior fixture, validation freshness, rollback note | `skill-authoring-expert`, `skill-efficacy-benchmark`, `validation-broker` | Do not hand-edit generated runtime artifacts |
| Documentation handoff | Final handoff for non-trivial engineering work | Close evidence, proof limits, observability/no-log rationale, and residual risk | validation result, what it proves/does not prove, next gate, rollback note | `agent-execution-discipline`, `plan-execution-consistency`, `change-documentation-gate` | Read/review-only turns may close with inspected limits instead |

# Non-Negotiable Rules

- **Evidence before confidence:** non-trivial implementation or closure must name purpose, source-backed facts, object relationships, state/rule/invariant constraints, boundaries, side effects, validation, observability, and residual risk.
- **Specialist ownership remains intact:** route structure, business semantics, failure contracts, side effects, validation, security, reliability, and release risks to their owning capabilities; this capability only coordinates the judgment record.
- **No persona or corpus drift:** do not turn senior judgment into a top-level professional skill, personal-content loader, generic article, or business-semantic-control-plane substitute.
- **Source/generated boundary is explicit:** source files, generated outputs, reports, dist artifacts, and installation artifacts have separate owners and validation evidence.
- **Skip is evidence:** trivial/no-semantic/no-engineering skips must explain why behavior, state, rule, boundary, side effect, validation, and observability evidence is unnecessary.

# Industry Benchmarks

Senior engineering review practices, DDD aggregate and invariant modeling, Clean Architecture boundaries, OWASP security review discipline, SRE failure-mode analysis, and DORA release evidence all require the same minimum: facts before claims, ownership before placement, failure and side-effect contracts before rollout, validation evidence before closure, and residual-risk ownership when proof is incomplete.

# Selection Rules

Select this capability when any of these are true:

- The task is non-trivial engineering and no explicit senior judgment evidence exists.
- A change adds, moves, extracts, merges, splits, or renames code where ownership, object relationship, or placement could drift.
- A rule, invariant, state transition, side effect, failure path, permission, status, lifecycle, or public contract is changed or reviewed.
- A shortcut, abstraction, dependency, helper, strategy, adapter, manager, or shared/common module is proposed.
- Hook runtime, stage routing, eval fixtures, capability registries, or closure requirements change agent behavior.
- Validation could pass while the real behavior, invariant, side effect, or boundary remains unproven.

Skip with an explicit `skip_reason` only for trivial, no-semantic, no-engineering, formatting, or docs-only changes. The skip reason must state why no behavior, state, rule, boundary, side effect, validation, or observability evidence is needed.

# Proactive Professional Triggers

- **Signal:** Implementation begins with code shape but no purpose, facts, object/state/rule map, validation map, or residual risk.
  **Hidden risk:** plausible code expresses no verified reality and can pass local tests while violating invariants.
  **Required professional action:** require `senior_programming_judgment` before edit or closure.
  **Route to:** `implementation-structure-design`, `agent-execution-discipline`, `quality-test-gate`.
  **Evidence required:** purpose, source-backed facts, objects, states, behaviors, rules, invariants, boundaries, validation map, residual risk.
- **Signal:** A helper, shared/common module, public API, or adapter is introduced from convenience.
  **Hidden risk:** business rules, IO, failure behavior, or ownership leaks into generic code and becomes hard to validate.
  **Required professional action:** record reuse/placement and object-boundary evidence, then select specialist structure review.
  **Route to:** `implementation-structure-design`, `module-boundary-design`, `code-clarity-maintainability`.
  **Evidence required:** existing candidates, selected location, rejected locations, dependency direction, side effects, tests.
- **Signal:** A status, lifecycle, guard, invariant, permission, failure mode, retry, or side effect changes.
  **Hidden risk:** the change mutates state or external reality without transition, compensation, observability, or rollback evidence.
  **Required professional action:** map allowed/forbidden states, behavior owner, rule authority, failure contract, and validation.
  **Route to:** `state-machine-modeling`, `failure-contract-design`, `data-side-effect-flow-tracing`, `validation-broker`.
  **Evidence required:** transition or invariant map, side-effect ordering, expected failures, rollback/compensation, validation command.
- **Signal:** A skill, routing, hook, eval, or benchmark behavior change is claimed complete from prose or partial tests.
  **Hidden risk:** runtime agent behavior, source/dist boundaries, state schemas, or reports drift while local prose looks correct.
  **Required professional action:** require behavior fixture, schema/state evidence, source/generated boundary, validation freshness, and residual risk.
  **Route to:** `skill-authoring-expert`, `skill-efficacy-benchmark`, `plan-execution-consistency`.
  **Evidence required:** fixture, changed source, generated-artifact policy, validator result, what evidence does not prove.

# Risk Escalation Rules

- Escalate to `implementation-structure-design` when placement, ownership, helper extraction, shared/common modules, public/private/internal boundaries, or dependency direction are uncertain.
- Escalate to `business-semantic-control-plane` only when task-scoped business vocabulary, rule authority, workflow state, or business-object ownership is actually involved.
- Escalate to `failure-contract-design` and `data-side-effect-flow-tracing` when failure, retry, rollback, persistence, cache, event, external IO, telemetry, or ordering is material.
- Escalate to `security-privacy-gate` or `reliability-observability-gate` when trust boundaries, permissions, sensitive data, availability, performance, logs, metrics, traces, or operational evidence are affected.
- Escalate to `validation-broker` and `quality-test-gate` when validation evidence is stale, too narrow, syntax-only, or not mapped to the changed invariant, state, failure path, or public contract.

# Critical Details

- Treat repository graph, memory, prior summaries, and generated reports as selectors until current source verifies the fact.
- A fact is source-backed only when it names current code, config, docs, user-provided material, owner review, or fresh validation evidence.
- Object evidence names ownership and relationships; it is not a list of classes only.
- State evidence names allowed and forbidden transitions, guards, and terminal or rollback states when applicable.
- Rule evidence names authority, enforcement layer, reason codes, entry points, tests, and residual risk.
- Side effects include persistence, cache, events, file IO, network IO, external calls, telemetry, state cache, generated output, and user-visible output.
- Observability is explicit even when the decision is "no new log": state the no-log rationale and any metric/trace/test evidence instead.
- Minimality requires a selected simplest correct path, rejected abstractions, shortcut ceiling, and upgrade trigger when a shortcut remains.

# Failure Modes

- **Persona drift:** the capability becomes generic senior-developer prose instead of executable evidence.
- **BSP overreach:** business-semantic-control-plane is selected to cover all engineering judgment.
- **Shape-only review:** object/file shape is clean while rules, states, side effects, or validation are unproven.
- **Shared utility pollution:** generic helpers absorb domain behavior, IO, or failure handling.
- **State-free status change:** enum/status edits skip allowed/forbidden transition evidence.
- **Side-effect blindness:** persistence, cache, event, telemetry, or generated output changes without ordering and rollback evidence.
- **Validation mismatch:** tests prove syntax or local success but not the invariant, public contract, or failure path.
- **No observability decision:** logs/metrics/traces are added without redaction/cardinality rationale or omitted without a no-log rationale.
- **Evidence closure gap:** final handoff claims completion without validation result, proof limits, residual risk, and rollback note.

# Reference Loading Policy

This body carries the full decision contract. Load adjacent specialist capability references only when their risk is selected: structure and placement through `implementation-structure-design`, business semantics through `business-semantic-control-plane`, side effects through `data-side-effect-flow-tracing`, failure through `failure-contract-design`, validation through `validation-broker` and `test-strategy`, and skill authoring through `skill-authoring-expert`. Do not load unrelated language or domain references by default.

# Output Contract

Return `senior_programming_judgment`:

- `schema_version`
- `required`
- `skip_reason` when not required
- `stage_fit`
- `purpose`
- `facts`
- `objects`
- `states`
- `behaviors`
- `rules`
- `invariants`
- `boundaries`
- `failure_contract`
- `side_effects`
- `reuse_and_placement`
- `minimality_decision`
- `validation_map`
- `observability_map`
- `residual_risk`

Use compact, source-backed entries. Do not include raw prompts, secrets, environment variables, full command output, full diffs, personal archives, or project-wide corpora.

# Evidence Contract

Closure requires concrete answers for:

- **Purpose:** why the change exists, current behavior, desired behavior, success signal, failure signal, and non-goals.
- **Facts:** source-backed facts, assumptions, open questions, and evidence limits.
- **Objects and relationships:** artifact type, owner, lifecycle, relationships, rejected meanings, and ownership boundary.
- **States, behaviors, rules, and invariants:** allowed/forbidden transitions, behavior owner, rule authority, enforcement layer, side effects, protected invariants, tests, and residual risk.
- **Boundaries:** module, public/private/internal, dependency direction, trust/permission, generated/source, runtime profile, and external IO boundaries.
- **Failure and side effects:** expected failures, retryability, rollback/compensation, degradation behavior, persistence/cache/event/external effects, ordering, and idempotency.
- **Reuse, placement, and minimality:** existing candidates, selected location, rejected locations, simplest correct path, rejected abstractions, shortcut ceiling, and upgrade trigger.
- **Validation and observability:** acceptance-to-test map, invariant/state/failure tests, commands or not-run status, what evidence proves and does not prove, logs/metrics/traces or no-log rationale.
- **Boundaries inspected:** files, generated artifacts, schemas, runtime hooks, public contracts, caller/callee paths, tests, configs, and docs inspected before the decision, plus boundaries intentionally not inspected.
- **Validation evidence:** fresh command output or explicit not-run disclosure mapped to purpose, facts, objects, states, behaviors, rules, invariants, failure contract, side effects, and observability.
- **Reuse / placement rationale:** direct reuse, extension reuse, rejected locations, selected owner, dependency direction, and why no broader abstraction is being introduced.
- **Behavior preservation:** compatibility, old and new behavior comparison, migration or fallback path, and proof limits for behavior that must not change.
- **Residual risk:** owner, next gate, and handoff target for every remaining risk.

# Quality Gate

1. Non-trivial engineering work has either a complete `senior_programming_judgment` or an allowed skip reason.
2. Every fact is source-backed or classified as assumption/open question.
3. Objects, states, behaviors, rules, invariants, boundaries, failures, side effects, validation, observability, and residual risk are all represented when behavior changes.
4. Specialist capabilities remain owners of detailed structure, business semantics, side-effect, failure, test, security, reliability, and release rules.
5. Validation evidence is fresh after the final material edit or disclosed as not run with residual risk.
6. No personal corpus, private mapping artifact, direct source install, raw prompt, secret, environment value, or full command output is introduced.

# Used By

- change-forge-router
- development-process-orchestrator
- architecture-impact-reviewer
- backend-change-builder
- frontend-change-builder
- data-api-contract-changer
- data-middleware-change-builder
- integration-change-builder
- security-privacy-gate
- reliability-observability-gate
- quality-test-gate
- ai-code-review-refactor
- change-documentation-gate
- skill-authoring-expert

# Handoff

Hand off placement to `implementation-structure-design`, business meaning to `business-semantic-control-plane`, failures to `failure-contract-design`, side effects to `data-side-effect-flow-tracing`, validation to `quality-test-gate` and `validation-broker`, runtime/hook behavior to `skill-authoring-expert` and `skill-efficacy-benchmark`, and closure evidence to `agent-execution-discipline`.

# Completion Criteria

Complete when the change has a bounded senior judgment record, selected specialist capabilities for the real risks, fresh validation or an explicit not-run disclosure, a rollback note, proof limits, and residual risk owners without adding a persona, top-level skill, private corpus, or duplicate specialist rules.
