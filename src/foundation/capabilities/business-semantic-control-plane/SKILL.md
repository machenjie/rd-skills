---
name: business-semantic-control-plane
description: Coordinates task-scoped Business Semantic Pack evidence across intent, vocabulary, objects, rules, workflows, memory, graph, golden cases, validation, and review without becoming a business-expert skill or runtime corpus.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "135"
changeforge_version: 0.1.0
---

# Mission

Coordinate Business Semantic Pack (BSP) evidence so AI-assisted engineering can understand business intent, vocabulary, objects, rules, workflows, source mappings, memory signals, graph selectors, golden cases, validation, and review boundaries without inventing business authority or installing a separate business-skill corpus.

# When To Use

Use this capability when a task changes or reviews business meaning: business context missing, business vocabulary ambiguous, business object ownership unclear, business rule authority unknown, business workflow state unclear, business invariant changed, business rule hidden in SQL/controller/UI/test, DTO used as business object, business memory affects decision, business golden case missing, technical refactor may change business semantics, business semantic review required, graph used as business fact, memory used as business fact, or broad requests to make AI understand business context. Legacy aliases such as ambiguous business term, rule authority unclear, hidden SQL rule, hidden controller rule, and stale business memory remain compatible.

Use it for ChangeForge skill-authoring work that adds business semantic routing, stage evidence, eval fixtures, schemas, graph/memory semantics, validation scripts, or hook-runtime advisory reminders.

# Do Not Use When

Do not use this capability as a standalone business-expert skill, strategy consultant, market researcher, personal knowledge-base loader, document-ingestion surface, or project-wide business corpus. Do not use it for small local technical edits with no business term, rule, workflow, data-signal, or source-of-truth ambiguity.

# Stage Fit

Use during requirement intake, DDD, implementation planning, coding, testing, code review, documentation handoff, and skill-authoring when business semantics affect evidence. It adds evidence slots to the current engineering stage; it does not create a new stage or override the professional owner skill.

# Non-Negotiable Rules

- BSP is task-scoped and source-bounded; it is never a project-wide business archive.
- The capability coordinates semantic evidence; it is not the authority for business decisions.
- `FACT` requires current source, user-provided source material, owner review, or validation evidence.
- Repository graph and project memory are selectors only. They may suggest where to inspect but cannot prove a `FACT` by themselves.
- Every rule record names `rule_id`, owner, enforcement layer, reason codes, entry points, effective dating, tests or residual risk, and evidence.
- Every workflow record names allowed and forbidden transitions, guard rules, actors, and validation mapping.
- Business golden cases map business claims to executable tests, review evidence, owner review, or residual risk.
- Selected and skipped references must use structured `referenceDecision` rationale under `context-control-plane`: reference, reason, evidence limit, optional budget mode, and residual risk.
- Do not add personal asset ingestion, private archive maps, or runtime assumptions about private corpora.

# Industry Benchmarks

Anchor on domain-driven design ubiquitous language, business rule cataloging, decision tables, state-transition testing, golden-case regression suites, traceability matrices, source-of-truth review, memory governance, and graph-as-selector retrieval discipline.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Intent clarification | Outcome, non-goal, success signal, or failure signal is ambiguous. | Convert business intent into verifiable claims. | Business outcome, affected objects/rules/workflows, non-goals, open questions. | `requirement-clarification`, `acceptance-standard-definition` | Coding from vague terms. |
| Vocabulary/object alignment | Term, object, owner, entity, aggregate, DTO, table, or resource meaning is unclear. | Separate business vocabulary from persistence/API/UI artifacts. | Term map, object inventory, owner, rejected ambiguous meanings. | `domain-object-identification`, `model-boundary-mapping` | Treating DTO/table as domain object. |
| Rule authority mapping | Rule, invariant, policy, calculation, permission, reason code, or SQL/controller condition changes. | Create a rule catalog and single enforcement authority. | Rule record, owner, layer, entry points, reason codes, tests/residual risk. | `business-rule-extraction`, `permission-boundary-modeling` | Hidden rule in controller, mapper, SQL, or tests. |
| Workflow/state mapping | Status, transition, lifecycle, cancellation, approval, recovery, or forbidden path changes. | Model allowed/forbidden transitions and validation. | Transition table, guard rules, actor authority, invalid-transition tests. | `state-machine-modeling`, `regression-testing` | Enum-only state changes. |
| Business-to-code placement | Semantic claim must map to files, modules, commands, schemas, or generated artifacts. | Preserve business-to-code trace and forbidden placements. | Object-to-file, rule-to-layer, workflow-to-state-machine, residual placement risk. | `implementation-structure-design`, `repository-context-map` | Shared utils or mappers as rule owners. |
| Memory reconciliation | Prior memory mentions business term, rule, owner, stale context, or golden case. | Classify memory as accepted, rejected, stale, or not verified. | Memory event verdict, current-source confirmation, residual risk. | `project-memory-governance`, `repository-graph-analysis` | Memory as direct fact. |
| Golden case mapping | Business behavior needs durable validation. | Map claims to business golden cases and test/review targets. | Golden case, positive/negative case, validation command or owner review. | `quality-test-gate`, `validation-broker` | Green technical checks without business cases. |
| Semantic review | Diff, refactor, or generated code may alter business meaning. | Detect changed semantics, hidden rules, stale memory, missing golden coverage. | BSP diff consistency, new/changed/rejected rule/workflow findings, validation map. | `ai-code-review-refactor`, `code-review` | Approval from clean code shape alone. |

# Selection Rules

Select this capability when the canonical trigger family appears: business context missing, business vocabulary ambiguous, business object ownership unclear, business rule authority unknown, business workflow state unclear, business invariant changed, business rule hidden in SQL/controller/UI/test, DTO used as business object, business memory affects decision, business golden case missing, technical refactor may change business semantics, business semantic review required, graph used as business fact, or memory used as business fact. Select it with `domain-impact-modeler` for DDD evidence, with `quality-test-gate` for business golden cases, with `ai-code-review-refactor` for semantic review, and with `context-control-plane` when BSP references or evidence are selected/skipped.

Do not select it for every backend or frontend change. A simple local formatting, typo, dependency, or internal implementation edit should skip BSP unless it changes business meaning or hides a business rule.

# Risk Escalation Rules

Escalate when a business rule affects money, entitlement, tenant ownership, status/lifecycle, permission, audit, compliance, irreversible data, external contract, event semantics, or historical interpretation. Escalate when current source contradicts memory or graph suggestions, when a rule has no owner or tests, when a workflow has no forbidden transition coverage, or when a semantic change lacks owner review.

# Proactive Professional Triggers

- **Signal:** A task asks for business context, vocabulary, object meaning, or "understand the domain" without named source paths, owners, or current requirements. **Hidden risk:** project memory or broad prompt context becomes unverified business authority. **Required professional action:** classify each claim, inspect current source or owner material, and document open questions before implementation. **Route to:** `requirement-clarification`, `repository-context-map`. **Evidence required:** source path or owner review, claim class, accepted/rejected memory signal, open-question owner, and validation status.
- **Signal:** A rule, policy, entitlement, reason code, calculation, tenant constraint, or permission appears only in SQL, controller code, UI logic, mapper defaults, fixtures, or tests. **Hidden risk:** hidden rule authority moves without catalog, owner, entry-point, or negative-case evidence. **Required professional action:** extract the rule record and map enforcement layer, entry points, reason codes, tests, and residual risk. **Route to:** `business-rule-extraction`, `permission-boundary-modeling`. **Evidence required:** rule_id, source path, owner, enforcement layer, positive/negative case, validation command or owner review.
- **Signal:** Status, lifecycle, approval, cancellation, recovery, or enum changes are treated as simple data values. **Hidden risk:** forbidden transitions, actor authority, rollback, and historical state interpretation remain untested. **Required professional action:** model allowed and forbidden transitions and map each material transition to validation. **Route to:** `state-machine-modeling`, `quality-test-gate`. **Evidence required:** transition table, guard rule, actor, invalid-transition case, test or residual risk owner.
- **Signal:** Repository graph, generated summaries, old tickets, or project memory are used to prove a business rule, owner, workflow, or golden case. **Hidden risk:** stale selector evidence certifies false business meaning. **Required professional action:** treat graph and memory as selectors, reread current source, and mark stale claims rejected or not verified. **Route to:** `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** graph freshness, memory verdict, current-source confirmation, changed path, command/report, and evidence limit.
- **Signal:** A refactor, generated patch, mapper/schema change, fixture update, or test rewrite changes names, defaults, filters, reason codes, or workflows. **Hidden risk:** clean code review misses semantic drift and business golden cases stop proving the intended behavior. **Required professional action:** compare the diff to the BSP and require semantic review before approval. **Route to:** `ai-code-review-refactor`, `validation-broker`. **Evidence required:** BSP diff, changed claim, source path, golden case or validation command, owner review, and residual semantic risk.

# Critical Details

The BSP is a precision artifact. It should record only the business semantics needed for the task and the evidence that proves or limits those claims. It must preserve evidence classes: `FACT`, `INFERENCE`, `ASSUMPTION`, `OPEN_QUESTION`, and `MEMORY_SIGNAL`. A memory event that says a rule changed is a `MEMORY_SIGNAL` until current source or owner review confirms the rule.

The BSP schema sections are `task_business_intent`, `business_vocabulary`, `business_objects`, `business_rules`, `workflows`, `data_and_signal_semantics`, `code_mapping`, `memory_projection`, `validation_map`, and `context_control`. Missing sections must be explicit as open questions or residual risk, not silently omitted.

# Failure Modes

- **Business expert drift:** the capability invents business decisions instead of coordinating evidence and owners.
- **Memory-as-fact:** prior project memory is promoted to a `FACT` without current-source confirmation.
- **Graph-as-proof:** repository graph proximity is treated as semantic authority.
- **Hidden rule:** controller, mapper, SQL, UI, or test fixture owns a rule without a catalog record.
- **DTO-as-domain:** schema or table language becomes the business object by convenience.
- **Workflow bag:** statuses are added without allowed and forbidden transition mapping.
- **Golden gap:** technical tests pass while business behavior is untested.
- **Over-routing:** BSP is selected for a tiny local technical edit with no semantic signal.
- **Under-routing:** high-risk business semantics route through coding only.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 BSP routing, scope, mode, output, and gate rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete BSP decision. Load [references/business-semantic-pack-policy.md](references/business-semantic-pack-policy.md) when a task needs the full BSP schema, evidence-class policy, or graph/memory selector limits. Load [references/business-semantic-review-policy.md](references/business-semantic-review-policy.md) when reviewing a diff, refactor, generated patch, fixture, SQL/controller/UI change, or stale-memory claim for semantic drift. Load [references/business-golden-case-policy.md](references/business-golden-case-policy.md) when business claims must map to golden cases, negative paths, validation commands, owner review, or residual risk. Use [examples/example-output.md](examples/example-output.md) only when the output shape is unclear. Do not load references for project-wide business corpus construction, personal archive mapping, or local technical edits with no semantic signal.

# Output Contract

Return a `business_semantic_control_record` with:

- `mode_selected`
- `stage_fit`
- `triggers`
- `scope`
- `objects`
- `rules`
- `workflows`
- `memory`
- `graph`
- `golden_cases`
- `validation`
- `selected_references` as structured reference decisions
- `skipped_references` as structured reference decisions
- `evidence_limits`
- `residual_risk`
- `handoff`

When a BSP artifact is produced, use `business_semantic_pack` schema version 1 and map each business claim to evidence class, source, validation/review target, and residual risk.

# Evidence Contract

Close a BSP decision only when these answers are concrete: **boundaries inspected** across current requirements, source paths, owners, domain objects, rule authority, workflow states, graph selectors, project memory, golden cases, tests, and review surfaces; every business claim classified as `FACT`, `INFERENCE`, `ASSUMPTION`, `OPEN_QUESTION`, or `MEMORY_SIGNAL`; graph, memory, prior summary, and execution-trajectory claims accepted, rejected, stale, partial, or not verified before they influence trust; validation evidence names command, test, validator, report, artifact, owner review, exit code or not-run status, and freshness after the final material edit; what evidence proves and does not prove for uninspected entry points, historical data, external consumers, generated artifacts, stale memory, and business owner decisions; selected/skipped reference rationale, behavior preservation, rollback note, residual risk owner, and next gate.

# Quality Gate

1. BSP scope is task-bound and does not assume a runtime business corpus.
2. Every `FACT` has current source, user-provided source, owner review, or validation evidence.
3. Memory and graph are marked as selector/advisory evidence unless confirmed by current source.
4. Every business rule has unique `rule_id`, owner, enforcement layer, reason codes, entry points, effective dating, tests or residual risk.
5. Every workflow has allowed and forbidden transitions with guard/actor evidence.
6. Every business claim maps to validation, owner review, review finding, or residual risk.
7. Golden cases cover material business rules, workflows, permissions, reason codes, and negative paths.
8. Selected and skipped BSP references have structured context-control rationale with reason and evidence limit.
9. Review detects new, moved, hidden, rejected, stale, or untested business semantics.
10. Handoff states validation evidence, rollback note, residual risk, and next owner.

# Used By

- change-forge-router
- domain-impact-modeler
- quality-test-gate
- ai-code-review-refactor
- change-documentation-gate
- skill-authoring-expert

# Handoff

Hand off intent gaps to `change-intake-compiler`, object ownership to `domain-impact-modeler` and `domain-object-identification`, rule ownership to `business-rule-extraction`, workflow state to `state-machine-modeling`, source placement to `implementation-structure-design`, validation to `quality-test-gate` and `validation-broker`, semantic review to `ai-code-review-refactor`, and owner-facing documentation to `change-documentation-gate`.

# Completion Criteria

The capability is complete when business semantic evidence is scoped, classified, source-limited, mapped to code and validation, reconciled against memory/graph selectors, and handed off without claiming business authority beyond verified evidence.
