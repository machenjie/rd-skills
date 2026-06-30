# Engineering Stage Model

ChangeForge launches professional capability by engineering stage, product surface,
language surface, and risk surface. `src/registry/stage-model.yaml` is the canonical
machine-readable matrix. This document is the human-readable projection used to explain
which capabilities launch now, which to skip, and where to hand off next. The
`engineering-stage-professionalism` capability body carries the compact launch rules and
output contract, and validators keep both views aligned with the registry source.

The goal is precision, not coverage. A stage launches the smallest sufficient capability set.
Heavy cross-stage loading is a defect: it bloats context and hides the next action.

## 1. Stage Launch Matrix

Each stage declares purpose, launch capabilities (launched by default for that stage),
do-not-launch-by-default (skip unless a trigger forces them), required evidence, required
quality gates, and the allowed handoff target stage.

### requirement-intake
- Purpose: understand requirement, clarify scope, name non-goals, define acceptance.
- Launch: `requirement-clarification`, `requirement-structuring`, `non-goal-boundary-definition`, `acceptance-standard-definition`, `scenario-decomposition`.
- Do not launch by default: coding, language, testing, refactoring, release capabilities.
- Required evidence: clarified scope, explicit non-goals, testable acceptance signal, clarification status before action, PDD acceptance criteria, business semantic intent, vocabulary, and open questions when business terms are present.
- Required quality gates: requirement gate, PDD gate.
- Handoff: architecture-design or implementation-planning.

### architecture-design
- Purpose: module boundaries, layering, dependency direction, data ownership, service boundaries, extensibility, reversibility.
- Launch: `architecture-style-selection`, `module-boundary-design`, `layered-architecture-design`, `architecture-tradeoff-analysis`, `extensibility-design`, `solution-optimality-evaluation`.
- Conditional launch: `architecture-enforcement-tooling`, `consumer-impact-analysis`, `dependency-wiring-lifecycle`, and `minimal-correct-implementation` when extensibility, stack complexity, or future-proofing is proposed; `business-semantic-control-plane` when business objects, rule authority, or workflow states affect architecture.
- Do not launch by default: language idiom checks, coding, test authoring.
- Required evidence: boundary owners, dependency direction, rejected alternatives, simplicity ladder result when extensibility or stack complexity is proposed, reversibility classification, DDD domain invariants, business object ownership, rule authority, and workflow boundary when business semantics affect architecture.
- Required quality gates: architecture gate, DDD gate.
- Handoff: implementation-planning.

### implementation-planning
- Purpose: code placement, reuse decision, object/function/class/file/directory design, naming, readable main flow, public/private/internal boundaries.
- Launch: `repository-context-map`, `implementation-structure-design`, `module-boundary-design`, `code-clarity-maintainability`, `language-idiom-enforcement` (naming only); add `minimal-correct-implementation` when new structure, dependency, file, class, config, or abstraction is proposed.
- Conditional launch: `code-element-professionalism` when variable, expression, statement, default, cleanup, fallthrough, boolean-trap, side-effect-getter, or event-order hazards shape the plan; `repository-graph-analysis` when repo graph, context pack, generated artifact graph, affected-test graph, or source-of-truth uncertainty is part of the plan; `business-semantic-control-plane` when business rules or workflows need source-backed semantic mapping.
- Do not launch by default: full architecture review, release gate, deep performance profiling.
- Required evidence: SDD public API and module placement, SDD design decision points for material choices, user choice status for material design choices, safe assumption rationale when proceeding without user choice, target boundaries inspected before plan, repository context map with owning surface and caller/callee evidence, reuse candidates, simplicity ladder result, deleted or rejected complexity, placement rationale, visibility decisions, test placement, TDD or validation signal, business-to-code mapping and forbidden placement rationale when rules or workflows are affected.
- Required quality gates: implementation gate, SDD gate.
- Handoff: coding.

### coding
- Purpose: implement code with language idiom, error handling, resource cleanup, input validation, concurrency, minimal implementation.
- Launch: matching language professional usage capability, `language-idiom-enforcement`, `input-validation`, `logging-error-handling`, relevant builder skill; add `minimal-correct-implementation` when the implementation risks unnecessary scope.
- Conditional launch: `code-element-professionalism` when implementation evidence includes variable, expression, statement, default, cleanup, fallthrough, boolean-trap, side-effect-getter, or event-order hazards.
- Do not launch by default: architecture deep review, release gate, full regression suite design.
- Required evidence: inspected implementation context, TDD or validation signal before code, PDD/DDD/SDD/TDD traceability, idiomatic implementation, validated inputs, released resources, minimal scope diff, deleted or rejected complexity when selected, tool permission and sandbox classification when risky tools or commands are used, business semantic claim-to-code mapping when implementation changes rules, objects, or workflow states.
- Required quality gates: implementation gate, TDD gate.
- Handoff: testing or code-review.

### debugging-diagnosis
- Purpose: reproduce, collect evidence, gather logs/metrics/traces, eliminate hypotheses, locate verified root cause.
- Launch: `failure-diagnosis`, `agent-execution-discipline`, `observability`, matching language professional usage capability.
- Do not launch by default: refactoring, release gate, new feature design. Launch refactoring only if root cause requires structural change.
- Required evidence: reproduction, symptom/root-cause/contributing-factor split, eliminated hypotheses, verified cause.
- Required quality gates: execution discipline gate.
- Handoff: bug-fix or implementation-planning.

### bug-fix
- Purpose: minimal fix, same-pattern scan, regression test, compatibility, upstream/downstream impact.
- Launch: relevant builder skill, `agent-execution-discipline`, `regression-testing`, `code-review`.
- Conditional launch: `minimal-correct-implementation` when minimal fix, delete/shrink, dependency, abstraction, wrapper-only delegation, shortcut, or overengineering review signal exists.
- Do not launch by default: architecture redesign, release gate unless the fix ships directly.
- Required evidence: minimal diff, deleted or rejected complexity when selected, same-pattern scan record, regression test, blast-radius note, plan versus actual changed-file consistency, business semantic same-pattern scan when the defect is rule, status, permission, or workflow related.
- Required quality gates: implementation gate, test gate.
- Handoff: testing, code-review, or release-delivery.

### code-review
- Purpose: correctness, structure, naming, reuse, readability, security, reliability, test evidence, hallucinated-API check.
- Launch: `code-review`, `plan-execution-consistency`, `implementation-structure-design`, `code-clarity-maintainability`, `language-idiom-enforcement`; add `ai-code-review-refactor` for generated code as a professional skill.
- Conditional launch: `code-element-professionalism` when review evidence includes variable, expression, statement, default, cleanup, fallthrough, boolean-trap, side-effect-getter, or event-order hazards; `minimal-correct-implementation` when minimal fix, delete/shrink, dependency, abstraction, wrapper-only delegation, shortcut, or overengineering review signal exists; add `execution-trajectory-analysis` or `project-memory-governance` when review must account for trajectory, repeated failure, fragile-file, or stale-context evidence.
- Do not launch by default: release gate, deployment, infrastructure capabilities.
- Required evidence: findings with severity, complexity-only delete/shrink findings when selected, evidence, impacted file, required fix, validation required, independent reviewer, repair and re-review result, final diff covered by review scope, semantic review result for changed, hidden, stale, rejected, or untested business behavior.
- Required quality gates: implementation gate.
- Handoff: refactoring, bug-fix, testing, or documentation-handoff.

### refactoring
- Purpose: behavior-preserving structure change — extract, move, inline, merge, split, cleanup, readability, dependency direction, rollback.
- Launch: `refactoring`, `implementation-structure-design`, `code-clarity-maintainability`, `code-review`, `regression-testing`; add `minimal-correct-implementation` for delete/shrink or speculative structure collapse.
- Conditional launch: `code-element-professionalism` when refactoring changes variable lifetime, expression semantics, statement ordering, cleanup, fallthrough, boolean parameters, getter behavior, or event timing.
- Do not launch by default: feature design, release gate. Add `architecture-impact-reviewer` only when boundaries shift.
- Required evidence: characterization tests, preserved behavior, selection rationale, deleted or rejected complexity, rollback path, business behavior preservation evidence when refactoring touches terms, rules, or workflows.
- Required quality gates: implementation gate, test gate.
- Handoff: testing, code-review, or documentation-handoff.

### testing
- Purpose: unit, integration, contract, e2e, regression, fixtures, mocks, concurrency, language-specific tests.
- Launch: `test-strategy`, `plan-execution-consistency`, `language-testing-strategy`, the matching test capability (`unit-testing`, `integration-testing`, `contract-testing`, `e2e-testing`, `regression-testing`), `test-data-management`; add `minimal-correct-implementation` when lower-depth validation is proposed.
- Conditional launch: `validation-broker` and `repository-graph-analysis` when changed-path mapping, affected-test selection, stale validation, or generated artifact validation is in scope.
- Do not launch by default: architecture redesign, coding of new features.
- Required evidence: risk-based layer selection, deterministic data, observable-behavior assertions, evidence of gaps, minimal check rationale when lower-depth validation is selected, validation freshness after final material edits, validation commands mapped to PDD/DDD/SDD, business golden cases or explicit residual risk for material rule, reason-code, permission, and workflow claims.
- Required quality gates: test gate.
- Handoff: code-review, release-delivery, or documentation-handoff.

### release-delivery
- Purpose: CI/CD, configuration, migration, feature flag, canary, rollback, observability.
- Launch: `ci-cd`, `release-rollback`, `containerization`, `kubernetes-gateway`, `observability`, `backup-recovery`.
- Conditional launch: `minimal-correct-implementation` for new release machinery, shortcuts, stale flags, or config branches.
- Do not launch by default: language deep checks and coding unless code still changes.
- Required evidence: rollout sequence, rollback trigger, config compatibility, health checks, alert ownership, shortcut ceiling and upgrade trigger when shortcuts remain, tool permission and rollback classification for release commands.
- Required quality gates: delivery gate.
- Handoff: documentation-handoff or closed.

### documentation-handoff
- Purpose: change boundary, validation evidence, residual risk, runbook, API docs, changelog, next actions.
- Launch: `agent-workflow-state-machine`, `plan-execution-consistency`, `documentation-generation`, `agent-execution-discipline`; pair with `change-documentation-gate` as the professional owner.
- Conditional launch: `executor-adapter-protocol`, `validation-broker`, `execution-trajectory-analysis`, or `project-memory-governance` when closure depends on adapter support, validation freshness, trajectory review, or governed memory.
- Do not launch by default: coding capabilities unless docs contain API or code examples.
- Required evidence: validated boundary, validation freshness and plan-execution consistency, residual risk, updated docs list, handoff target, business semantic residual risk, owner handoff, and selected/skipped reference rationale when BSP was selected.
- Required quality gates: documentation gate.
- Handoff: closed or requirement-intake for a next change.

### skill-authoring
- Purpose: author, review, slim, split, or maintain ChangeForge skills, capabilities, references, registry, or routing rules.
- Launch: `repository-context-map`, `skill-authoring-expert`, `skill-efficacy-benchmark`, `documentation-generation`, `agent-execution-discipline`, `plan-execution-consistency`; add `minimal-correct-implementation` when skill source adds routing surface, references, benchmarks, shortcuts, or generated-review complexity; pair with `change-documentation-gate`, `ai-code-review-refactor`, or `quality-test-gate` when those professional owners are selected by risk.
- Conditional launch: `executor-adapter-protocol`, `repository-graph-analysis`, `project-memory-governance`, `validation-broker`, and `execution-trajectory-analysis` when authoring or evaluating those runtime-governance surfaces.
- Do not launch by default: product coding, language runtime, release capabilities.
- Required evidence: boundary, trigger precision, output contract, registry/routing/validation impact, skill-efficacy benchmark impact when behavior claims change, minimal scope diff, deleted or rejected complexity, shortcut ceiling and upgrade trigger when shortcuts remain, business semantic schema, fixture, routing, memory, graph, and validation impact when authoring BSP behavior.
- Required quality gates: documentation gate, test gate.
- Handoff: documentation-handoff or closed.

## 2. Product Surface Selector

Each product surface lists the matching professional skill, matching foundation capabilities,
common risks, and gates likely needed. Launch only the matching set for the surface in play.

| Product surface | Professional skill | Foundation capabilities | Common risks | Gates likely needed |
| --- | --- | --- | --- | --- |
| frontend-product | `frontend-change-builder` | `page-component-decomposition`, `state-management-design`, `form-validation-design`, `frontend-api-integration` | broken flow, a11y, state leaks | impact, test |
| backend-product | `backend-change-builder` | `service-business-logic`, `authentication-authorization`, `idempotency-retry-design`, `logging-error-handling` | auth, transactions, concurrency | security, test |
| api-contract | `data-api-contract-changer` | `api-contract-design`, `dto-schema-design`, `error-code-design`, `version-compatibility`, `data-format-contract-usage` | breaking change, compatibility | API/data, test |
| data-model | `data-api-contract-changer` | `data-model-design`, `relational-database`, `indexing-query-optimization` | integrity, ownership | API/data, test |
| database-migration | `data-api-contract-changer` | `data-migration-design`, `transaction-consistency`, `release-rollback` | irreversible data, downtime | API/data, delivery, test |
| cache | `data-middleware-change-builder` | `cache-design`, `concurrency-control` | stampede, stale reads | reliability, test |
| message-queue | `data-middleware-change-builder` | `message-queue-design`, `idempotency-retry-design` | ordering, duplicate delivery | reliability, test |
| network-gateway | `reliability-observability-gate` | `network-protocol-gateway-usage`, `degradation-circuit-breaking`, `observability` | timeout chain, spoofed headers, retry amplification | reliability, security |
| search-analytics | `data-middleware-change-builder` | `search-analytics-design`, `indexing-query-optimization` | freshness, relevance | reliability, test |
| external-integration | `integration-change-builder` | `degradation-circuit-breaking`, `idempotency-retry-design` | timeout, retry storms | security, reliability |
| webhook | `integration-change-builder` | `authentication-security`, `idempotency-retry-design` | signature, replay | security, reliability |
| infrastructure-deployment | `delivery-release-gate` | `containerization`, `release-rollback`, `ci-cd` | rollout, rollback | delivery, reliability |
| kubernetes-helm | `delivery-release-gate` | `kubernetes-gateway`, `ci-cd`, `secret-configuration-security` | exposure, RBAC | delivery, security |
| ci-cd | `delivery-release-gate` | `ci-cd`, `package-dependency-management`, `build-tool-professional-usage` | unverified release, supply chain | delivery, security |
| ai-rag-agent | `ai-product-extension` | `threat-modeling`, `observability`, `test-strategy` | prompt injection, hallucination | security, AI review |
| web3 | `web3-product-extension` | `authentication-security`, `threat-modeling` | key custody, replay | security, test |
| payment-trading | `payment-trading-extension` | `idempotency-retry-design`, `transaction-consistency` | double-charge, ledger drift | security, test, delivery |
| low-level-systems | `low-level-systems-extension` | `concurrency-control`, `language-performance-safety` | memory safety, ABI | reliability, test |
| linux-systems | `reliability-observability-gate` | `linux-systems-professional-usage`, `observability` | service lifecycle, cgroup limits, permissions | reliability, security |
| sdk-library | `data-api-contract-changer` | `sdk-library-contract-design`, `version-compatibility`, `package-dependency-management` | API break, provenance | API/data, test |
| cli-daemon | `backend-change-builder` | `cli-daemon-interface-design`, `logging-error-handling` | exit-code/IO contract | test |
| documentation-only | `change-documentation-gate` | `documentation-generation` | stale or wrong docs | documentation |
| git-workflow | `development-process-orchestrator` | `git-professional-usage`, `repository-context-map`, `validation-broker`, `plan-execution-consistency` | overwritten worktree, generated conflict, history rewrite | implementation, test |
| skill-authoring | `change-forge-router` | `repository-context-map`, `skill-authoring-expert`, `engineering-stage-professionalism`, `skill-efficacy-benchmark`, `plan-execution-consistency`, `context-control-plane`, `minimal-correct-implementation` | over/under routing, context bloat | documentation, test |
| agent-runtime-governance | `change-forge-router` | `executor-adapter-protocol`, `agent-tool-permission-sandbox`, `agent-workflow-state-machine`, `context-control-plane` | unsupported runtime event, overclaimed closure | security, execution discipline |
| repository-intelligence | `change-impact-analyzer` | `repository-graph-analysis`, `repository-context-map`, `context-packaging`, `context-control-plane` | stale graph, source-of-truth drift | impact, test |
| project-memory | `change-forge-router` | `project-memory-governance`, `agent-execution-discipline`, `plan-execution-consistency`, `context-control-plane` | unsafe auto-learning, stale context | execution discipline |
| business-semantics | `change-forge-router` | `business-semantic-control-plane`, `domain-object-identification`, `business-rule-extraction`, `state-machine-modeling`, `context-control-plane`, `project-memory-governance`, `repository-graph-analysis`, `validation-broker` | stale or overclaimed business context | requirement, domain, test, AI review |
| validation-broker | `quality-test-gate` | `validation-broker`, `repository-graph-analysis`, `plan-execution-consistency`, `context-control-plane` | stale validation, wrong validator depth | test |
| execution-trajectory | `ai-code-review-refactor` | `execution-trajectory-analysis`, `agent-workflow-state-machine`, `validation-broker`, `context-control-plane` | edit-before-read, repair without re-review | AI review, test |

Business semantics use the canonical trigger family: business context missing,
business vocabulary ambiguous, business object ownership unclear, business rule
authority unknown, business workflow state unclear, business invariant changed,
business rule hidden in SQL/controller/UI/test, DTO used as business object,
business memory affects decision, business golden case missing, technical
refactor may change business semantics, business semantic review required, graph
used as business fact, and memory used as business fact. Legacy trigger aliases
remain accepted for compatibility. BSP reference selection must use structured
reason/evidence-limit rationale, and graph or memory cannot be promoted to
`FACT` without current source, owner review, user source, or validation evidence.

## 3. Language Surface Selector

Each language lists its capability, the stages where it launches, and its main professional
concerns. The full per-stage checklist lives in the language capability body, not here.

| Language | Capability | Launch stages | Main professional concerns |
| --- | --- | --- | --- |
| Go | `go-professional-usage` | implementation-planning, coding, bug-fix, code-review, refactoring, testing | context propagation, goroutine lifecycle, error wrapping, small interfaces, package boundaries, table-driven tests, race detector |
| Java/JVM | `java-jvm-professional-usage` | implementation-planning, coding, bug-fix, code-review, refactoring, testing | null safety, immutability, exception model, thread/executor lifecycle, equals/hashCode, JVM memory, dependency hygiene |
| TypeScript | `typescript-professional-usage` | implementation-planning, coding, bug-fix, code-review, refactoring, testing | strict types, `unknown` over `any`, runtime validation, async error handling, state modeling, bundle impact |
| Python | `python-professional-usage` | implementation-planning, coding, bug-fix, code-review, refactoring, testing | type hints, runtime validation, packaging, async/sync boundary, context managers, mutable defaults |
| Rust | `rust-professional-usage` | implementation-planning, coding, bug-fix, code-review, refactoring, testing | ownership/borrowing, error model, `unsafe` boundary, trait design, async runtime, lifetime correctness |
| C/C++ | `cpp-professional-usage` | implementation-planning, coding, bug-fix, code-review, refactoring, testing | memory ownership, RAII, UB, bounds, concurrency, ABI, resource cleanup |
| Shell | `shell-cli-professional-usage` | implementation-planning, coding, bug-fix, code-review, refactoring, testing | quoting, `set -euo pipefail`, injection, portability, exit codes, idempotency |
| SQL | `sql-professional-usage` | implementation-planning, coding, bug-fix, code-review, refactoring, testing | parameterization, index usage, transaction isolation, migration safety, set-based logic |

## 4. Launch Discipline

- Decide the stage first, then launch capabilities.
- Every launched capability must map to the current stage, product surface, language surface, or a risk trigger.
- Every skipped heavy capability must state a skip reason.
- A cross-stage task is split into stages; it does not load every capability at once.
- L1 changes launch only the current stage's minimum set. L3/L4/L5 may plan across stages but still execute stage by stage.
- When both apply, select `engineering-stage-professionalism` before `agent-execution-discipline`: pick the stage first (routing priority 89), then apply execution discipline (priority 88) within that stage.
- The matrices above are referenced, not copied into individual skills.

Action ownership and review ownership are deliberately split. The active stage
selects the owner skill or capability for the action being performed; closure
then requires a different reviewer skill or capability when review evidence is
needed. Empty compaction or reinjection context must not overwrite the active
stage or owner/reviewer split. Repairs return to the action owner and then back
to the reviewer before the stage can close.

## 5. Stage Resolution

When stage signals conflict, resolve the active stage in this order:
explicit user stage, active action verb, evidence state, artifact type, then risk trigger.
The action being performed outranks the artifact being touched.

Conflict examples:

| Signals | Current stage | Reason |
| --- | --- | --- |
| review + implementation plan | implementation-planning | reviewing a plan before code is planning, not code-review |
| root cause unknown + fix | debugging-diagnosis | no verified cause exists yet |
| behavior preserving + extract/move/split | refactoring | structure movement without behavior change is refactoring |
| debug + release failure + migration | debugging-diagnosis | diagnose the failure before release rerouting |
| test + generated code review | code-review | generated implementation risk is reviewed before test expansion |
| docs + validation evidence + residual risk | documentation-handoff | closure evidence and reader obligations are documentation handoff |
| skill + registry + routing rule | skill-authoring | ChangeForge source artifacts use the skill-authoring stage |
| acceptance criteria + unclear scope | requirement-intake | clarify the requirement before design or implementation |
| module boundary + dependency direction | architecture-design | boundary ownership is architecture work |
| code placement + reuse decision | implementation-planning | placement and reuse decisions precede coding |
| implementation plan + target-project not inspected | requirement-intake | read-before-plan evidence is required before implementation-planning |
| coding + TDD signal missing | implementation-planning | coding waits for TDD or validation signal |
| review finding + re-review result missing | code-review | review findings keep the stage in code-review until repair and re-review evidence exists |
| write implementation + selected design | coding | active action is implementation |
| rollout + rollback + config | release-delivery | rollout mechanics belong to release delivery |

## 6. Cross-Stage and Planning Professional Skills

Some professional skills are not owned by a single stage: they compile intake, plan work
across stages, model cross-cutting impact, or gate risk at any stage. The router selects
them when their signal appears and hands the result to the owning stage. Each still
launches the minimum sufficient capability set; none is loaded by default in every stage.

| Professional skill | Primary stage(s) | Role |
| --- | --- | --- |
| `change-intake-compiler` | requirement-intake | Compile a raw request into a structured change request: current vs desired behavior, non-goals, constraints, assumptions, and missing information. |
| `acceptance-criteria-builder` | requirement-intake, testing | Turn the change request into verifiable acceptance criteria and link them to required test evidence. |
| `change-impact-analyzer` | architecture-design, cross-stage planning | Map blast radius across product, domain, API, data, frontend, backend, integration, security, and operations before implementation. |
| `task-dag-planner` | implementation-planning, multi-stage planning | Decompose a multi-stage change into ordered, reviewable, rollback-aware tasks with explicit dependencies and validation points. |
| `experience-impact-modeler` | requirement-intake, frontend-product flow | Model user and page flows, interaction states, and usability risk for product-facing change. |
| `domain-impact-modeler` | architecture-design, domain behavior | Model entities, invariants, state machines, and domain events, and protect consistency boundaries. |
| `security-privacy-gate` | risk escalation across all stages | Review auth, object authorization, input/output, injection, secrets, dependencies, and privacy whenever a security or privacy signal appears. |
| `reliability-observability-gate` | debugging-diagnosis, release-delivery | Set SLI/SLO, performance and capacity, logging/metrics/traces/alerts, and recovery expectations for production-risk change. |

These skills are listed here so no top-level professional skill is invisible to the stage
model. They are launched by router signal, not by default in every stage.
