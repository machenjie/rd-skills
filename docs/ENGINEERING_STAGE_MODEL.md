# Engineering Stage Model

ChangeForge launches professional capability by engineering stage, product surface,
language surface, and risk surface. The router and the `engineering-stage-professionalism`
foundation capability use this model to decide which capabilities to launch now, which to
skip, and where to hand off next. This document is the canonical matrix; the capability body
carries the compact launch rules and the output contract.

The goal is precision, not coverage. A stage launches the smallest sufficient capability set.
Heavy cross-stage loading is a defect: it bloats context and hides the next action.

## 1. Stage Launch Matrix

Each stage declares purpose, launch capabilities (launched by default for that stage),
do-not-launch-by-default (skip unless a trigger forces them), required evidence, and the
handoff target stage.

### requirement-intake
- Purpose: understand requirement, clarify scope, name non-goals, define acceptance.
- Launch: `requirement-clarification`, `requirement-structuring`, `non-goal-boundary-definition`, `acceptance-standard-definition`, `scenario-decomposition`.
- Do not launch by default: coding, language, testing, refactoring, release capabilities.
- Required evidence: clarified scope, explicit non-goals, testable acceptance signal.
- Handoff: architecture-design or implementation-planning.

### architecture-design
- Purpose: module boundaries, layering, dependency direction, data ownership, service boundaries, extensibility, reversibility.
- Launch: `architecture-style-selection`, `module-boundary-design`, `layered-architecture-design`, `architecture-tradeoff-analysis`, `extensibility-design`, `solution-optimality-evaluation`.
- Do not launch by default: language idiom checks, coding, test authoring.
- Required evidence: boundary owners, dependency direction, rejected alternatives, reversibility classification.
- Handoff: implementation-planning.

### implementation-planning
- Purpose: code placement, reuse decision, object/function/class/file/directory design, naming, public/private/internal boundaries.
- Launch: `implementation-structure-design`, `module-boundary-design`, `language-idiom-enforcement` (naming only).
- Do not launch by default: full architecture review, release gate, deep performance profiling.
- Required evidence: reuse candidates, placement rationale, visibility decisions, test placement.
- Handoff: coding.

### coding
- Purpose: implement code with language idiom, error handling, resource cleanup, input validation, concurrency, minimal implementation.
- Launch: matching language professional usage capability, `language-idiom-enforcement`, `input-validation`, `logging-error-handling`, relevant builder skill.
- Do not launch by default: architecture deep review, release gate, full regression suite design.
- Required evidence: idiomatic implementation, validated inputs, released resources, minimal scope diff.
- Handoff: testing or code-review.

### debugging-diagnosis
- Purpose: reproduce, collect evidence, gather logs/metrics/traces, eliminate hypotheses, locate verified root cause.
- Launch: `failure-diagnosis`, `agent-execution-discipline`, `observability`, matching language professional usage capability.
- Do not launch by default: refactoring, release gate, new feature design. Launch refactoring only if root cause requires structural change.
- Required evidence: reproduction, symptom/root-cause/contributing-factor split, eliminated hypotheses, verified cause.
- Handoff: bug-fix.

### bug-fix
- Purpose: minimal fix, same-pattern scan, regression test, compatibility, upstream/downstream impact.
- Launch: relevant builder skill, `agent-execution-discipline`, `regression-testing`, `code-review`.
- Do not launch by default: architecture redesign, release gate unless the fix ships directly.
- Required evidence: minimal diff, same-pattern scan record, regression test, blast-radius note.
- Handoff: testing or code-review.

### code-review
- Purpose: correctness, structure, naming, reuse, security, reliability, test evidence, hallucinated-API check.
- Launch: `code-review`, `implementation-structure-design`, `language-idiom-enforcement`, `ai-code-review-refactor` (for generated code).
- Do not launch by default: release gate, deployment, infrastructure capabilities.
- Required evidence: findings with severity, evidence, impacted file, required fix, validation required.
- Handoff: refactoring, bug-fix, or testing.

### refactoring
- Purpose: behavior-preserving structure change — extract, move, inline, merge, split, dependency direction, rollback.
- Launch: `refactoring`, `implementation-structure-design`, `code-review`, `regression-testing`.
- Do not launch by default: feature design, release gate. Add `architecture-impact-reviewer` only when boundaries shift.
- Required evidence: characterization tests, preserved behavior, selection rationale, rollback path.
- Handoff: testing or code-review.

### testing
- Purpose: unit, integration, contract, e2e, regression, fixtures, mocks, concurrency, language-specific tests.
- Launch: `test-strategy`, `language-testing-strategy`, the matching test capability (`unit-testing`, `integration-testing`, `contract-testing`, `e2e-testing`, `regression-testing`), `test-data-management`.
- Do not launch by default: architecture redesign, coding of new features.
- Required evidence: risk-based layer selection, deterministic data, observable-behavior assertions, evidence of gaps.
- Handoff: code-review or release-delivery.

### release-delivery
- Purpose: CI/CD, configuration, migration, feature flag, canary, rollback, observability.
- Launch: `ci-cd`, `release-rollback`, `containerization`, `kubernetes-gateway`, `observability`, `backup-recovery`.
- Do not launch by default: language deep checks and coding unless code still changes.
- Required evidence: rollout sequence, rollback trigger, config compatibility, health checks, alert ownership.
- Handoff: documentation-handoff.

### documentation-handoff
- Purpose: change boundary, validation evidence, residual risk, runbook, API docs, changelog, next actions.
- Launch: `documentation-generation`, `change-documentation-gate`, `agent-execution-discipline`.
- Do not launch by default: coding capabilities unless docs contain API or code examples.
- Required evidence: validated boundary, residual risk, updated docs list, handoff target.
- Handoff: closed or next change.

### skill-authoring
- Purpose: author, review, slim, split, or maintain ChangeForge skills, capabilities, references, registry, or routing rules.
- Launch: `skill-authoring-expert`, `change-documentation-gate`, `ai-code-review-refactor`, `quality-test-gate`.
- Do not launch by default: product coding, language runtime, release capabilities.
- Required evidence: boundary, trigger precision, output contract, registry/routing/validation impact.
- Handoff: documentation-handoff.

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
- The matrices above are referenced, not copied into individual skills.
