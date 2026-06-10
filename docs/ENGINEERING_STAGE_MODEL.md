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
- Required evidence: clarified scope, explicit non-goals, testable acceptance signal.
- Required quality gates: requirement gate.
- Handoff: architecture-design or implementation-planning.

### architecture-design
- Purpose: module boundaries, layering, dependency direction, data ownership, service boundaries, extensibility, reversibility.
- Launch: `architecture-style-selection`, `module-boundary-design`, `layered-architecture-design`, `architecture-tradeoff-analysis`, `extensibility-design`, `solution-optimality-evaluation`.
- Do not launch by default: language idiom checks, coding, test authoring.
- Required evidence: boundary owners, dependency direction, rejected alternatives, reversibility classification.
- Required quality gates: architecture gate.
- Handoff: implementation-planning.

### implementation-planning
- Purpose: code placement, reuse decision, object/function/class/file/directory design, naming, readable main flow, public/private/internal boundaries.
- Launch: `implementation-structure-design`, `module-boundary-design`, `code-clarity-maintainability`, `language-idiom-enforcement` (naming only).
- Do not launch by default: full architecture review, release gate, deep performance profiling.
- Required evidence: reuse candidates, placement rationale, visibility decisions, test placement.
- Required quality gates: implementation gate.
- Handoff: coding.

### coding
- Purpose: implement code with language idiom, error handling, resource cleanup, input validation, concurrency, minimal implementation.
- Launch: matching language professional usage capability, `language-idiom-enforcement`, `input-validation`, `logging-error-handling`, relevant builder skill.
- Do not launch by default: architecture deep review, release gate, full regression suite design.
- Required evidence: idiomatic implementation, validated inputs, released resources, minimal scope diff.
- Required quality gates: implementation gate.
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
- Do not launch by default: architecture redesign, release gate unless the fix ships directly.
- Required evidence: minimal diff, same-pattern scan record, regression test, blast-radius note.
- Required quality gates: implementation gate, test gate.
- Handoff: testing, code-review, or release-delivery.

### code-review
- Purpose: correctness, structure, naming, reuse, readability, security, reliability, test evidence, hallucinated-API check.
- Launch: `code-review`, `implementation-structure-design`, `code-clarity-maintainability`, `language-idiom-enforcement`; add `ai-code-review-refactor` for generated code as a professional skill.
- Do not launch by default: release gate, deployment, infrastructure capabilities.
- Required evidence: findings with severity, evidence, impacted file, required fix, validation required.
- Required quality gates: implementation gate.
- Handoff: refactoring, bug-fix, testing, or documentation-handoff.

### refactoring
- Purpose: behavior-preserving structure change — extract, move, inline, merge, split, cleanup, readability, dependency direction, rollback.
- Launch: `refactoring`, `implementation-structure-design`, `code-clarity-maintainability`, `code-review`, `regression-testing`.
- Do not launch by default: feature design, release gate. Add `architecture-impact-reviewer` only when boundaries shift.
- Required evidence: characterization tests, preserved behavior, selection rationale, rollback path.
- Required quality gates: implementation gate, test gate.
- Handoff: testing, code-review, or documentation-handoff.

### testing
- Purpose: unit, integration, contract, e2e, regression, fixtures, mocks, concurrency, language-specific tests.
- Launch: `test-strategy`, `language-testing-strategy`, the matching test capability (`unit-testing`, `integration-testing`, `contract-testing`, `e2e-testing`, `regression-testing`), `test-data-management`.
- Do not launch by default: architecture redesign, coding of new features.
- Required evidence: risk-based layer selection, deterministic data, observable-behavior assertions, evidence of gaps.
- Required quality gates: test gate.
- Handoff: code-review, release-delivery, or documentation-handoff.

### release-delivery
- Purpose: CI/CD, configuration, migration, feature flag, canary, rollback, observability.
- Launch: `ci-cd`, `release-rollback`, `containerization`, `kubernetes-gateway`, `observability`, `backup-recovery`.
- Do not launch by default: language deep checks and coding unless code still changes.
- Required evidence: rollout sequence, rollback trigger, config compatibility, health checks, alert ownership.
- Required quality gates: delivery gate.
- Handoff: documentation-handoff or closed.

### documentation-handoff
- Purpose: change boundary, validation evidence, residual risk, runbook, API docs, changelog, next actions.
- Launch: `documentation-generation`, `agent-execution-discipline`; pair with `change-documentation-gate` as the professional owner.
- Do not launch by default: coding capabilities unless docs contain API or code examples.
- Required evidence: validated boundary, residual risk, updated docs list, handoff target.
- Required quality gates: documentation gate.
- Handoff: closed or requirement-intake for a next change.

### skill-authoring
- Purpose: author, review, slim, split, or maintain ChangeForge skills, capabilities, references, registry, or routing rules.
- Launch: `skill-authoring-expert`, `documentation-generation`, `agent-execution-discipline`; pair with `change-documentation-gate`, `ai-code-review-refactor`, or `quality-test-gate` when those professional owners are selected by risk.
- Do not launch by default: product coding, language runtime, release capabilities.
- Required evidence: boundary, trigger precision, output contract, registry/routing/validation impact.
- Required quality gates: documentation gate, test gate.
- Handoff: documentation-handoff or closed.

## 2. Product Surface Selector

Each product surface lists the matching professional skill, matching foundation capabilities,
common risks, and gates likely needed. Launch only the matching set for the surface in play.

| Product surface | Professional skill | Foundation capabilities | Common risks | Gates likely needed |
| --- | --- | --- | --- | --- |
| frontend-product | `frontend-change-builder` | `page-component-decomposition`, `state-management-design`, `form-validation-design`, `frontend-api-integration` | broken flow, a11y, state leaks | impact, test |
| backend-product | `backend-change-builder` | `service-business-logic`, `authentication-authorization`, `idempotency-retry-design`, `logging-error-handling` | auth, transactions, concurrency | security, test |
| api-contract | `data-api-contract-changer` | `api-contract-design`, `dto-schema-design`, `error-code-design`, `version-compatibility` | breaking change, compatibility | API/data, test |
| data-model | `data-api-contract-changer` | `data-model-design`, `relational-database`, `indexing-query-optimization` | integrity, ownership | API/data, test |
| database-migration | `data-api-contract-changer` | `data-migration-design`, `transaction-consistency`, `release-rollback` | irreversible data, downtime | API/data, delivery, test |
| cache | `data-middleware-change-builder` | `cache-design`, `concurrency-control` | stampede, stale reads | reliability, test |
| message-queue | `data-middleware-change-builder` | `message-queue-design`, `idempotency-retry-design` | ordering, duplicate delivery | reliability, test |
| search-analytics | `data-middleware-change-builder` | `search-analytics-design`, `indexing-query-optimization` | freshness, relevance | reliability, test |
| external-integration | `integration-change-builder` | `degradation-circuit-breaking`, `idempotency-retry-design` | timeout, retry storms | security, reliability |
| webhook | `integration-change-builder` | `authentication-security`, `idempotency-retry-design` | signature, replay | security, reliability |
| infrastructure-deployment | `delivery-release-gate` | `containerization`, `release-rollback`, `ci-cd` | rollout, rollback | delivery, reliability |
| kubernetes-helm | `delivery-release-gate` | `kubernetes-gateway`, `ci-cd`, `secret-configuration-security` | exposure, RBAC | delivery, security |
| ci-cd | `delivery-release-gate` | `ci-cd`, `package-dependency-management` | unverified release, supply chain | delivery, security |
| ai-rag-agent | `ai-product-extension` | `threat-modeling`, `observability`, `test-strategy` | prompt injection, hallucination | security, AI review |
| web3 | `web3-product-extension` | `authentication-security`, `threat-modeling` | key custody, replay | security, test |
| payment-trading | `payment-trading-extension` | `idempotency-retry-design`, `transaction-consistency` | double-charge, ledger drift | security, test, delivery |
| low-level-systems | `low-level-systems-extension` | `concurrency-control`, `language-performance-safety` | memory safety, ABI | reliability, test |
| sdk-library | `data-api-contract-changer` | `sdk-library-contract-design`, `version-compatibility`, `package-dependency-management` | API break, provenance | API/data, test |
| cli-daemon | `backend-change-builder` | `cli-daemon-interface-design`, `logging-error-handling` | exit-code/IO contract | test |
| documentation-only | `change-documentation-gate` | `documentation-generation` | stale or wrong docs | documentation |
| skill-authoring | `change-forge-router` | `skill-authoring-expert`, `change-documentation-gate` | over/under routing, context bloat | documentation, test |

## 3. Language Surface Selector

Each language lists its capability, the stages where it launches, and its main professional
concerns. The full per-stage checklist lives in the language capability body, not here.

| Language | Capability | Launch stages | Main professional concerns |
| --- | --- | --- | --- |
| Go | `go-professional-usage` | coding, bug-fix, code-review, refactoring, testing | context propagation, goroutine lifecycle, error wrapping, small interfaces, package boundaries, table-driven tests, race detector |
| Java/JVM | `java-jvm-professional-usage` | coding, bug-fix, code-review, refactoring, testing | null safety, immutability, exception model, thread/executor lifecycle, equals/hashCode, JVM memory, dependency hygiene |
| TypeScript | `typescript-professional-usage` | coding, bug-fix, code-review, refactoring, testing | strict types, `unknown` over `any`, runtime validation, async error handling, state modeling, bundle impact |
| Python | `python-professional-usage` | coding, bug-fix, code-review, refactoring, testing | type hints, runtime validation, packaging, async/sync boundary, context managers, mutable defaults |
| Rust | `rust-professional-usage` | coding, bug-fix, code-review, refactoring, testing | ownership/borrowing, error model, `unsafe` boundary, trait design, async runtime, lifetime correctness |
| C/C++ | `cpp-professional-usage` | coding, bug-fix, code-review, refactoring, testing | memory ownership, RAII, UB, bounds, concurrency, ABI, resource cleanup |
| Shell | `shell-cli-professional-usage` | coding, bug-fix, code-review, refactoring, testing | quoting, `set -euo pipefail`, injection, portability, exit codes, idempotency |
| SQL | `sql-professional-usage` | coding, bug-fix, code-review, refactoring, testing | parameterization, index usage, transaction isolation, migration safety, set-based logic |

## 4. Launch Discipline

- Decide the stage first, then launch capabilities.
- Every launched capability must map to the current stage, product surface, language surface, or a risk trigger.
- Every skipped heavy capability must state a skip reason.
- A cross-stage task is split into stages; it does not load every capability at once.
- L1 changes launch only the current stage's minimum set. L3/L4/L5 may plan across stages but still execute stage by stage.
- When both apply, select `engineering-stage-professionalism` before `agent-execution-discipline`: pick the stage first (routing priority 89), then apply execution discipline (priority 88) within that stage.
- The matrices above are referenced, not copied into individual skills.

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
