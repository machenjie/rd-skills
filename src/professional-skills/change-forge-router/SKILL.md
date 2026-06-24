---
name: change-forge-router
description: Central ChangeForge orchestration skill for classifying product and code changes, selecting the minimum sufficient professional skill path, routing foundation capabilities and domain extensions, choosing runtime profile awareness, and declaring quality gates without broad external asset-mapping assumptions.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---

# ChangeForge Router

## Mission
Route any product, code, delivery, documentation, review, or test-generation request through the smallest professional ChangeForge path that can safely resolve the change, expose risk, define acceptance, plan work, select foundation capabilities, apply domain extensions, and declare quality gates.

## When To Use
Use before implementation, investigation, review, release, or documentation work when the request does not already provide a complete skill path, risk level, impact model, capability set, execution mode, and quality gate plan.

Use the router especially when the request is broad, ambiguous, high risk, cross-module, domain-specific, production-facing, or likely to involve API, data, security, reliability, release, or documentation impact.

## Do Not Use When
Do not use when a specialist skill is explicitly requested, the scope is already narrow, the impacted surface is known, and no routing decision remains. This skips router reclassification only; it does not skip the runtime prompt execution protocol, evidence gates, independent review, repair/re-review, or evidence handoff owned by the invoked skill path.

Do not use the router to invoke every skill, invent a product program around a local edit, assume a new system is being built, or introduce out-of-scope asset mapping. Runtime work must be based on the request, available project context, and ChangeForge-authored skills, not undeclared external libraries or knowledge stores.

## Non-Negotiable Rules
- **Direct use still runs the runtime prompt flow.** When `change-forge-router` is invoked directly and router reclassification is skipped, target-project engineering work must still clarify requirements before action, inspect relevant code/tests/config/docs before planning, name a TDD or validation signal before implementation, map each action to an owner skill and a different review skill, repair and re-review findings, and hand off with validation evidence, residual risk, and route/stage manifests when routed.
- Classify the request before prescribing work.
- Choose the minimum sufficient professional path; add skills only when the classification, impact, risk, or missing information requires them.
- Treat bug fixes, refactors, API changes, data changes, migrations, review, tests, docs, reliability, security, and deployment as first-class changes.
- Preserve missing information as blocking questions, non-blocking questions, or explicit assumptions.
- For engineering prompts in a target project, run the runtime prompt execution protocol before any implementation path: clarify requirement, inspect relevant target-project evidence before planning, create a TDD-oriented plan, split action-specific skill ownership, require independent review, repair findings, re-review, and hand off with evidence. Pure explanation, translation, or question-answering with no engineering action may skip the full protocol only after stating that no engineering action is being taken.
- Do not plan engineering work before inspecting the relevant target-project code, tests, configs, docs, existing implementation, and likely call chain. A plan based only on the user prompt is invalid unless the prompt is explicitly asking for non-executing advice and no target-project action will follow.
- Do not route a single generalized skill to own every action. Each action must have the most specific owner professional skill or selected capability, and each completed action must have a review skill or capability that is different from the owner.
- If review finds a defect, missing evidence, wrong boundary, or untested acceptance path, route repair back to the owner skill or the appropriate specialist, then repeat review before closure.
- Escalate risk when auth, authorization, object-level permission, payment, subscription, billing, wallet, private key, Web3 asset, user data, PII, file upload, AI prompt, RAG, external integration, webhook, database migration, production deployment, production incident, cloud IAM, public exposure, regulated workload, compliance evidence, cost anomaly, secret/config change, security-sensitive dependency upgrade, or irreversible data operation is plausible.
- Route domain extensions only when domain signals are present; do not attach them because they are available.
- Route foundation capabilities as targeted support for selected professional skills; do not list all capabilities unless the user asks for a catalog.
- Include skipped or deferred areas implicitly through the impact matrix and quality gates instead of padding the professional path.
- Treat the machine-readable `changeforge_route` manifest as mandatory routing output and closure evidence: emit it when routing and restate it, with `changeforge_stage_route` for non-trivial engineering work, in the final handoff of a routed change instead of dropping it after the first turn. A manifest counts as closure evidence only when it carries non-empty `selected_skills`, `selected_capabilities`, `required_references`, and `required_quality_gates`; a bare `changeforge_route:` line or a manifest restated only on the first turn is not closure evidence.
- Never install source authoring directories as runtime content and never route to out-of-scope asset ingestion, scanning, indexing, summarization, mapping, packaging, or installation.

## Industry Benchmarks
Use change advisory practice, trunk-based delivery, risk-based testing, secure development lifecycle, architecture decision records, domain-driven design, API compatibility management, migration expand-contract delivery, operational readiness review, privacy-by-design, threat modeling, rollback planning, and evidence-based AI code review as benchmarks.

## Technical Selection Criteria
Classify the request across these dimensions:

- Change type: new feature, feature modification, bug fix, refactor, API change, data model change, database migration, frontend change, backend change, integration change, dependency upgrade, security fix, performance optimization, reliability improvement, observability change, deployment change, configuration change, documentation change, code review, or test generation.
- Complexity: L1 isolated local change, L2 single-module change, L3 multi-module product change, L4 product-grade high-risk change, or L5 regulated/financial/Web3/AI/migration/production-critical change.
- Risk level: low, medium, high, or critical.
- Execution mode: clarify, analyze, plan, implement, review, release, document, or blocked.
- Product area: user-facing workflow, admin workflow, platform workflow, operations workflow, internal developer workflow, or unknown.
- Code area: frontend, backend, API, data, middleware, integration, infrastructure, tests, docs, or unknown.
- Domain extension signals: Web3, AI, mobile, big data, IoT/embedded, payment/trading, low-level systems, or none.
- Runtime profile: recommended, full, or dev awareness.

Complexity routing: L1 uses only the relevant local builder/review/test path; L2 adds intake/acceptance/implementation/test and impact when blast radius is uncertain; L3 adds affected domain, architecture, data/API, security, docs, and test gates; L4 uses the full relevant product-grade path; L5 adds domain extension, security, reliability, delivery, rollback, documentation, evidence, and stop conditions.

Professional skill routing:

- `change-intake-compiler`: unclear requirement, missing current or desired behavior, unclear constraints, unknown non-goals.
- `change-impact-analyzer`: unknown blast radius, cross-surface changes, uncertain product/code impact.
- `acceptance-criteria-builder`: untestable done state, weak success criteria, missing negative or regression cases.
- `task-dag-planner`: task too large, dependency ordering needed, rollback or parallelization needed.
- `development-process-orchestrator`: PDD/DDD/SDD/TDD process orchestration, process trace evidence, cross-stage mapping, stage ownership, or requirement -> domain -> system design -> test closure needs validation.
- `experience-impact-modeler`: broken user flow, navigation, accessibility, interaction states, UX regression risk, A/B test, experiment, guardrail metric, SRM, or funnel analytics risk.
- `domain-impact-modeler`: business behavior, domain rules, permissions, state machines, or event semantics are affected.
- `architecture-impact-reviewer`: architecture drift, module boundaries, layering, service boundaries, scalability tradeoffs, monorepo graph, affected tests, build cache, or generated-file policy are affected.
- `data-api-contract-changer`: API contract, DTO, schema, compatibility, migration, or error model changes.
- `frontend-change-builder`: frontend implementation, routes, components, state, forms, API integration, accessibility, component placement, hook placement, or feature-local versus shared UI decisions.
- `backend-change-builder`: backend implementation, validation, auth, transactions, services, jobs, repositories, errors, service method placement, repository method placement, or helper placement.
- `data-middleware-change-builder`: SQL, NoSQL, cache, queues, search, storage, consistency, indexing, or middleware.
- `integration-change-builder`: third-party APIs, webhooks, credentials, retries, reconciliation, or external failure modes.
- `quality-test-gate`: tests failed, test plan missing, evidence missing, regression risk exists, test structure or fixture ownership is unclear, or release confidence is weak.
- `security-privacy-gate`: security, privacy, auth, secrets, upload, dependency, AI prompt, Web3, SOC 2, ISO 27001, audit evidence, compliance control, IAM, public bucket, or privilege escalation risk exists.
- `reliability-observability-gate`: performance, reliability, FinOps/cost, cloud bill, capacity, budget, incident response, outage, concurrency, rate limits, fallback, observability, or operations risk exists.
- `logging-design-gate`: log, logger, logging, audit log, diagnostic log, security log, access log, structured logging, error log, retry log, fallback log, degradation log, lifecycle log, log level, log field, trace_id, span_id, request_id, correlation_id, redaction, raw request body, raw query, authorization header, cookie, token, PII, log destination, high-cardinality control, or logging tests are affected.
- `delivery-release-gate`: deployment, config, migration rollout, CI/CD, Terraform/Pulumi/IaC, cloud governance, feature flags, production release, incident mitigation hotfix, compliance evidence, or rollback risk exists.
- `ai-code-review-refactor`: AI-generated code, refactor quality, hallucinated APIs, hidden assumptions, duplication, invented abstractions, weak implementation structure, unreadable flow, cleanup debt, or boundary drift risk exists.
- `change-documentation-gate`: user docs, API docs, migration notes, runbooks, ADRs, changelog, or operational notes need updates.
- `change-forge-router`: initial classification, rerouting, or route repair.

Foundation capability groups:

- Intake requirements: 01 `requirement-clarification`, 02 `requirement-structuring`, 03 `user-role-identification`, 04 `scenario-decomposition`, 05 `acceptance-standard-definition`, 06 `non-goal-boundary-definition`.
- Experience design: 07 `information-architecture`, 08 `user-flow-modeling`, 09 `prototype-description`, 10 `interaction-state-modeling`, 11 `design-system-rules`.
- Domain modeling: 12 `domain-object-identification`, 13 `business-rule-extraction`, 14 `state-machine-modeling`, 15 `use-case-modeling`, 16 `permission-boundary-modeling`, 17 `domain-event-modeling`.
- Architecture design: 18 `architecture-style-selection`, 19 `module-boundary-design`, 20 `layered-architecture-design`, 21 `microservice-splitting`, 22 `event-driven-architecture`, 23 `architecture-tradeoff-analysis`, 24 `extensibility-design`.
- Data and API contracts: 25 `data-model-design`, 26 `api-contract-design`, 27 `dto-schema-design`, 28 `error-code-design`, 29 `version-compatibility`, 30 `data-migration-design`.
- Frontend engineering: 31 `page-component-decomposition`, 32 `routing-navigation-design`, 33 `state-management-design`, 34 `form-validation-design`, 35 `frontend-api-integration`, 36 `frontend-testing`.
- Backend engineering: 37 `controller-api-implementation`, 38 `service-business-logic`, 39 `domain-logic-implementation`, 40 `repository-persistence`, 41 `authentication-authorization`, 42 `idempotency-retry-design`, 43 `async-job-design`, 44 `logging-error-handling`.
- Data middleware: 45 `relational-database`, 46 `nosql-database`, 47 `indexing-query-optimization`, 48 `transaction-consistency`, 49 `cache-design`, 50 `message-queue-design`, 51 `search-analytics-design`.
- Security privacy: 52 `threat-modeling`, 53 `input-validation`, 54 `web-security`, 55 `authentication-security`, 56 `secret-configuration-security`, 57 `dependency-vulnerability-scanning`.
- Quality testing: 58 `test-strategy`, 59 `unit-testing`, 60 `integration-testing`, 61 `contract-testing`, 62 `e2e-testing`, 63 `test-data-management`, 64 `regression-testing`.
- Reliability operations: 65 `performance-budgeting`, 66 `profiling`, 67 `concurrency-control`, 68 `degradation-circuit-breaking`, 69 `observability`, 70 `backup-recovery`.
- Delivery platform: 71 `project-initialization`, 72 `containerization`, 73 `ci-cd`, 74 `kubernetes-gateway`, 75 `release-rollback`.
- Engineering workflow: 76 `context-packaging`, 77 `task-dag-decomposition`, 78 `code-review`, 79 `refactoring`, 80 `documentation-generation`, 81 `failure-diagnosis`, 82 `solution-optimality-evaluation`, 101 `implementation-structure-design`, 102 `agent-execution-discipline`, 103 `skill-authoring-expert`, 104 `engineering-stage-professionalism`, 105 `code-clarity-maintainability`, 106 `design-pattern-selection`, 107 `testability-seam-design`, 108 `dependency-wiring-lifecycle`, 113 `data-side-effect-flow-tracing`, 116 `cleanup-deletion-governance`, 117 `minimal-correct-implementation`, 118 `repository-context-map`, 119 `agent-workflow-state-machine`, 120 `agent-tool-permission-sandbox`, 121 `skill-efficacy-benchmark`, 122 `plan-execution-consistency`, 127 `execution-trajectory-analysis`.
- Agent runtime governance: 123 `executor-adapter-protocol`.
- Repository intelligence: 124 `repository-graph-analysis`.
- Project memory: 125 `project-memory-governance`.
- Quality validation brokerage: 126 `validation-broker`.
- Targeted code correctness: 109 `algorithm-data-structure-selection`, 110 `failure-contract-design`, 111 `configuration-runtime-policy`, 112 `model-boundary-mapping`, 114 `architecture-enforcement-tooling`, 115 `consumer-impact-analysis`.
- Technology selection: 83 `technology-stack-selection`, 84 `language-runtime-selection`, 85 `language-idiom-enforcement`, 86 `language-testing-strategy`, 87 `language-performance-safety`, 88 `package-dependency-management`.
- Language professional usage: 89 `go-professional-usage`, 90 `java-jvm-professional-usage`, 91 `typescript-professional-usage`, 92 `python-professional-usage`, 93 `rust-professional-usage`, 94 `cpp-professional-usage`, 95 `shell-cli-professional-usage`, 96 `sql-professional-usage`.
- Interface, storage, and global correctness: 97 `sdk-library-contract-design`, 98 `cli-daemon-interface-design`, 99 `file-storage-processing`, 100 `i18n-timezone-money-safety`.

Domain extension routing:

- `web3-product-extension`: wallet, signature, smart contract, blockchain transaction, token, on-chain/off-chain state, custody, private key, chain data, nonce, replay, reorg, or network mismatch.
- `ai-product-extension`: LLM, RAG, agent, embedding, vector database, prompt, model output, tool use, hallucination, evaluation, AI safety, generated content, permission-aware retrieval, MLOps, model registry, model drift, training-serving skew, feature store, or label leakage.
- `mobile-product-extension`: Android, iOS, mobile app, offline mode, push notification, app lifecycle, platform permission, deep link, app store release, background execution, or mobile compatibility.
- `bigdata-product-extension`: stream, batch job, warehouse, analytics, reporting, ETL/ELT, lineage, freshness, backfill, replay, schema drift, dashboard metric, product experiment, A/B test, guardrail metric, SRM, feature store, or partitioning.
- `iot-embedded-extension`: device, firmware, embedded, sensor, actuator, edge protocol, OTA, hardware resource limit, connectivity loss, physical safety, or field operations.
- `payment-trading-extension`: payment, subscription, billing, invoice, refund, chargeback, trading, ledger, balance, checkout, reconciliation, settlement, entitlement, or tax.
- `low-level-systems-extension`: OS, kernel, driver, native performance, C, C++, Rust systems, FFI, ABI, syscall, memory safety, atomics, descriptor, or platform runtime.

Runtime profile awareness: recommended has 21 professional skills; full has 21 professional skills plus 7 domain extensions; dev has 21 professional skills, 127 foundation capabilities, and 7 domain extensions. Foundation capabilities compile into professional references in every profile.

## Mode Matrix
Select the routing mode before naming a professional path.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
|---|---|---|---|---|---|
| Initial classification | Request lacks complete stage, risk, skill, capability, and gate selection. | Choose the minimum sufficient route and preserve unknowns as questions or assumptions. | Change type, complexity, risk level, execution mode, selected skills/capabilities, skipped gates with reasons. | `engineering-stage-professionalism`, `context-packaging` | Listing every available skill or capability. |
| Route repair | Same path failed twice, diagnosis is weak, local fix lacks scan, or completion lacks evidence. | Change route based on new evidence instead of repeating the same action. | Failed command/output, route-repair reason, verified-cause gap, next diagnostic skill. | `agent-execution-discipline`, `failure-diagnosis` | Third same-path retry. |
| Hidden-risk escalation | Request hints at IDOR, queue duplicate, cache invalidation, webhook replay, migration rollback, accessibility, generated code, or shared utility pollution. | Upgrade only the risk-relevant path and record over-routing guard. | Trigger signal, hidden risk, routed skill/capability, evidence required, forbidden over-route. | `change-impact-analyzer`, `quality-test-gate` | Broad L4/L5 routing when a targeted L2/L3 route suffices. |
| Runtime profile selection | recommended/full/dev behavior, foundation reference loading, build/install, or skill authoring is in scope. | Keep runtime profile boundaries and source/dist separation correct. | Profile selected, source vs dist boundary, required references, validation commands. | `skill-authoring-expert`, `repository-context-map`, `skill-efficacy-benchmark`, `delivery-release-gate` | Installing source directories or runtime content from `src/`. |
| Handoff closure | Routing result is final or an agent hands off after routed work. | Preserve route manifest, stage state, plan consistency, evidence limits, residual risk, and next gate. | `changeforge_route`, optional `changeforge_stage_route`, plan-vs-diff/validation consistency, validation/not-verified disclosure, residual risk. | `agent-execution-discipline`, `agent-workflow-state-machine`, `plan-execution-consistency`, `change-documentation-gate` | Completion claims without closure evidence. |

## Proactive Professional Triggers
These triggers are hidden-risk escalators, not ordinary checklist items.

- **Signal:** A local bug fix touches one permission, tenant, query, cache, retry, or validation path. **Hidden risk:** missing same-pattern repair leaves sibling defect paths unverified. **Required professional action:** route same-pattern scan and regression evidence before implementation closure. **Route to:** `change-impact-analyzer`, `agent-execution-discipline`, `regression-testing`. **Evidence required:** pattern scan output, searched scope, related occurrences, and local/broad fix rationale.
- **Signal:** Queue consumer, webhook, retry, cron, or background job is mentioned without idempotency, replay, DLQ, or terminal failure behavior. **Hidden risk:** duplicate side effects or lost work under at-least-once delivery. **Required professional action:** select idempotency/queue/integration/reliability route. **Route to:** `idempotency-retry-design`, `message-queue-design`, `integration-change-builder`, `reliability-observability-gate`. **Evidence required:** key scope, retry/DLQ, replay protection, duplicate-delivery test.
- **Signal:** Cache, Redis, CDN, or memoization is added for performance without TTL, invalidation, scope, or source-of-truth statement. **Hidden risk:** stale data, tenant leak, stampede, or cache-as-source-of-truth drift. **Required professional action:** route cache design and observability gate when production-facing. **Route to:** `cache-design`, `data-middleware-change-builder`, `observability`. **Evidence required:** key schema, TTL/invalidation, tenant/permission scope, cache-loss behavior.
- **Signal:** Migration, schema change, feature flag, rollout, or config change lacks rollback and old/new compatibility. **Hidden risk:** revert deploy cannot recover mutated state. **Required professional action:** route release/rollback and data contract checks. **Route to:** `delivery-release-gate`, `release-rollback`, `data-api-contract-changer`. **Evidence required:** expand/contract plan, rollback command, compatibility window, validation output.
- **Signal:** AI-generated code introduces helpers, abstractions, public exports, dependencies, or API calls without reuse search. **Hidden risk:** hallucinated API, duplicate logic, or shared utility pollution. **Required professional action:** route AI code review plus implementation structure and code review. **Route to:** `ai-code-review-refactor`, `implementation-structure-design`, `code-review`. **Evidence required:** symbol/dependency verification, reuse search, placement rationale, tests or not-verified disclosure.
- **Signal:** log, logger, logging, audit log, diagnostic log, security log, access log, structured logging, fallback log, retry log, degradation log, error log, lifecycle log, trace_id, span_id, request_id, correlation_id, or redaction is mentioned. **Hidden risk:** noisy or unsafe logs can hide failure modes, leak PII/secrets, mix audit and diagnostics, or lack testable evidence. **Required professional action:** route logging design and log/security validation. **Route to:** `logging-design-gate`, `logging-error-handling`, `quality-test-gate`; add `security-privacy-gate` for raw request body, raw query, authorization header, cookie, token, or PII. **Evidence required:** log type, level, fields, redaction, correlation, cardinality control, and logging/security tests or no-log rationale.

## Risk Escalation Rules
Escalate one level for any risk trigger that affects user data, money, permissions, external systems, production state, or irreversible operations. Escalate to high or critical when more than one high-impact trigger is present or when rollback is unclear.

Risk triggers include auth, authorization, object-level permission, payment, subscription, billing, wallet, private key, Web3 asset, user data, PII, file upload, AI prompt, RAG, external integration, webhook, database migration, production deployment, production incident, secret/config change, cloud IAM, public exposure, regulated workload, compliance evidence, cost anomaly, dependency upgrade with security impact, irreversible data operation, raw request body, raw query, authorization header, cookie, token, audit log, security log, access log, and structured logging that can expose sensitive data.

Escalate to L5 when regulated, financial, Web3, AI, migration, or production-critical behavior combines with security, data integrity, external dependency, or rollback risk.

## Action-Specific Owner And Review Routing
Select only rows that match the actual action; the owner and review skill must differ.

| Action type | Owner skill / capability | Typical review skill / capability |
| --- | --- | --- |
| Requirement clarification | `change-intake-compiler` with `requirement-clarification`, `requirement-structuring`, `non-goal-boundary-definition` | `acceptance-criteria-builder` or `quality-test-gate` |
| Acceptance / TDD | `acceptance-criteria-builder` with `acceptance-standard-definition`, `scenario-decomposition` | `quality-test-gate` |
| Impact analysis | `change-impact-analyzer` with `context-packaging` | `change-forge-router` or `quality-test-gate` |
| Planning | `task-dag-planner` with `task-dag-decomposition`, `engineering-stage-professionalism` | `change-impact-analyzer` or `quality-test-gate` |
| Frontend implementation | `frontend-change-builder` | `quality-test-gate` or `ai-code-review-refactor` |
| Backend implementation | `backend-change-builder` | `quality-test-gate` or `ai-code-review-refactor` |
| API/data contract | `data-api-contract-changer` | `quality-test-gate` or `architecture-impact-reviewer` |
| Data middleware | `data-middleware-change-builder` | `reliability-observability-gate` or `quality-test-gate` |
| External integration | `integration-change-builder` | `security-privacy-gate`, `reliability-observability-gate`, or `quality-test-gate` |
| Security-sensitive work | relevant implementation owner | `security-privacy-gate` |
| Reliability/performance | relevant implementation owner or `reliability-observability-gate` | `reliability-observability-gate` or `quality-test-gate` |
| Documentation | `change-documentation-gate` | `change-forge-router` or `quality-test-gate` |
| Final handoff | `agent-execution-discipline` | `quality-test-gate` |

## Critical Details
Read `references/checklist.md` for non-trivial routing. Use generated router references for the current skill registry, capability index, domain extension index, and routing rules when available.

### Runtime Prompt Execution Protocol
This protocol applies when a developer uses ChangeForge skills in any target project for feature work, bug fixing, refactoring, testing, review, debugging, release, documentation, API/data, security, reliability, or other engineering action. It is not limited to authoring this repository.

1. **Requirement clarification gate.** Before any engineering operation, clarify current behavior, desired behavior, non-goals, constraints, acceptance, and the TDD or validation signal. If a blocking unknown could change the data model, API contract, authorization boundary, rollout, rollback, or user-visible behavior, stop and ask the blocking question. If execution may proceed, record assumptions and risk.
2. **Repository context map gate.** Before planning or action, select `repository-context-map` for target-project engineering or skill-authoring work and inspect the owning surface, sibling conventions, likely caller/callee path, tests, configs, docs, generated artifacts, and rejected placement locations. A plan without repository-context evidence is invalid.
3. **Workflow state gate.** Select `agent-workflow-state-machine` for non-trivial engineering work so the current phase, allowed next phase, owner/reviewer split, validation freshness, repair loop, and closure state are explicit before and after each phase transition.
4. **TDD plan gate.** Before implementation, name the failing, new, or updated test, eval, validation command, acceptance check, or explicit not-verified residual risk that proves the intended behavior.
5. **Action-specific skill routing.** Break the work into actions. Each action has an owner professional skill or selected capability matched to the action type: intake, acceptance, impact, planning, frontend, backend, API/data, middleware, integration, security, reliability, docs, test, release, or final handoff.
6. **Tool permission/sandbox gate.** Before risky commands, destructive operations, network writes, MCP/connector calls, migrations, deploys, secret access, or filesystem-wide edits, select `agent-tool-permission-sandbox` and record the tool, permission state, sandbox boundary, dry-run/revert path, and secret/output redaction rule.
7. **Independent review gate.** Each action has a review skill or capability different from the owner. Review evidence must be concrete; self-review by the same owner skill is not enough.
8. **Repair/re-review loop.** Any review finding routes repair to the owner skill or appropriate specialist, then repeats independent review. Handoff is invalid while review findings remain unresolved or unreviewed after repair.
9. **Plan consistency gate.** Before final review or handoff, select `plan-execution-consistency` and compare the accepted plan, changed files, validation commands, skipped work, and residual risks. Any unplanned file or behavior change routes back to planning/review.
10. **Evidence handoff.** Final handoff carries clarification, repository context, TDD evidence, workflow state, action-to-skill map, tool permission/sandbox evidence when applicable, review results, repair/re-review record, plan-execution consistency, validation results, residual risk, next gate, and the `changeforge_route` / `changeforge_stage_route` manifests.

Route by evidence in the request:

- If requirements are unclear, route first to `change-intake-compiler`.
- If blast radius is unknown, route to `change-impact-analyzer`.
- If done state is not testable, route to `acceptance-criteria-builder`.
- If the task is too large, route to `task-dag-planner`.
- If user flow is broken, route to `experience-impact-modeler`.
- If business behavior is wrong, route to `domain-impact-modeler`.
- If architecture drift is likely, route to `architecture-impact-reviewer`.
- If contract or schema mismatch is present, route to `data-api-contract-changer`.
- If frontend behavior is the change surface, route to `frontend-change-builder`.
- If backend behavior is the change surface, route to `backend-change-builder`.
- If code is added, moved, extracted, or reorganized, select `implementation-structure-design` with the relevant builder so the plan names reuse candidates, placement rationale, private/public decisions, file ownership, dependency direction, and test placement before implementation.
- If code is added or changed in a way that makes the main flow, control flow, function purpose, signature, comments, fallback, compatibility branch, or deletion path hard to read, select `code-clarity-maintainability` with the relevant builder, review, refactoring, or test gate.
- If the request asks where to put a function, class, component, hook, service, repository method, helper, utility, file, or directory, select `implementation-structure-design`; add `module-boundary-design` and `architecture-impact-reviewer` when the decision could alter module boundaries or dependency direction.
- If the request asks how to name a variable, function, method, class, file, directory, package, module, component, hook, service, repository, adapter, utility, helper, public API, or shared/common code, select `implementation-structure-design`; add `language-idiom-enforcement` when casing, visibility, export, package, namespace, or public API naming is language-specific.
- If the request uses broad buckets such as business, component, module, tool, helper, common, shared, public, feature, service, repository, adapter, or utility, require `implementation-structure-design` to classify ownership and reject dumping-ground placement.
- If target-project code, tests, configs, docs, ownership, caller/callee flow, generated artifacts, or local conventions have not been inspected before planning, select `repository-context-map`; do not substitute a generic plan for repository evidence.
- If the work crosses read/plan/edit/test/review/repair/release/handoff phases, select `agent-workflow-state-machine` so the current state, allowed transition, validation freshness, and repair/re-review obligation are explicit.
- If the work may run shell commands, destructive filesystem operations, migrations, deploys, network writes, connector/MCP actions, credential-bearing calls, or untrusted tool output handling, select `agent-tool-permission-sandbox`.
- If the change edits skills, capabilities, routing rules, stage architecture, hook runtime behavior, evals, benchmark fixtures, or professional evidence requirements, select `skill-efficacy-benchmark` to define the before/after behavior case and overhead evidence.
- If the final diff, validation, or handoff may drift from the accepted plan, select `plan-execution-consistency`; review cannot close until planned actions, changed files, validation results, skipped work, and residual risks reconcile.
- If the request mentions executor adapter, runtime adapter, adapter capabilities, normalized event, closure contract, or unsupported runtime event, select `executor-adapter-protocol` and keep the adapter as runtime protocol, not a router or LLM.
- If the request mentions repo graph, symbol/import/call/reference/test graph, context pack, source of truth unknown, generated artifact graph, or graph freshness, select `repository-graph-analysis` with `repository-context-map`.
- If the request mentions project memory, repeat failure, fragile file, stale context, previous fix failed, or latest commit review follow-up, select `project-memory-governance`; memory is experience input and needs current-source confirmation.
- If the request mentions validation command selection, stale validation, validation without outcome, affected tests, or changed path validation, select `validation-broker` with `quality-test-gate`.
- If the request mentions trajectory, edit before read, repair without re-review, stop without residual risk, or skipped engineering stage, select `execution-trajectory-analysis` with `agent-workflow-state-machine`.
- If AI-generated implementation adds any function, class, file, directory, component, hook, service, repository, adapter, utility, abstraction, branch-heavy flow, or dependency, select `ai-code-review-refactor`, `implementation-structure-design`, `code-clarity-maintainability`, and `code-review`.
- If refactoring extracts, moves, splits, collapses, cleans up dead code, removes feature flags, removes deprecated APIs, or retires compatibility branches, select `refactoring`, `implementation-structure-design`, `code-clarity-maintainability`, and `code-review`.
- If the request mentions or implies file naming mismatch, inconsistent file naming, wrong filename format, duplicate code, poor reuse, failure to reuse existing functions, reuse existing function/class/module, extension reuse, extending existing logic without changing old behavior, extracting classes, object modeling, inheritance, reflection, advanced refactor, oversized file/class/function, unreadable main flow, deep nesting, boolean trap, weakly typed parameter bag, side-effect pollution, missing comments, doc comments, test comments, exported API comments, public API comments, useless comments, excessive comments, stale comments, or comment quality, select `implementation-structure-design`, `code-clarity-maintainability`, `agent-execution-discipline`, and `language-idiom-enforcement`; add `ai-code-review-refactor` when reviewing AI-generated code; add `refactoring` when behavior-preserving movement is required; add `quality-test-gate` when tests, fixtures, helpers, or test comments are affected; add `architecture-impact-reviewer` when module boundaries or dependency direction may change.
- If test helpers, fixtures, factories, mocks, or golden files are placed in shared/common test utilities, or tests call private helpers instead of public behavior, select `quality-test-gate`, `code-clarity-maintainability`, and `implementation-structure-design`.
- If the change is being executed by an AI or agent and has any non-trivial diagnosis, code-mutation, deployment, or handoff component, select `agent-execution-discipline` alongside the substantive skills so the execution carries evidence inventory, verified-cause statement, route-repair ledger (after repeated failure), same-pattern scan record, reuse-and-placement rationale, and a proactive closure package.
- If an agent has retried the same approach twice without success, force a route change via `agent-execution-discipline` and route the substantive diagnosis to `failure-diagnosis`; do not permit a third same-path retry.
- If an agent proposes a local fix for a bug or defect, require `agent-execution-discipline` with a same-pattern scan record and route to `change-impact-analyzer` when the scan reveals occurrences in other modules.
- If an agent claims a change is complete or ready for handoff, require the `agent-execution-discipline` proactive closure package (boundary, validation results, residual risk, handoff target) regardless of which professional skills handled the substantive work.
- If the request is a non-trivial engineering task spanning design, implementation planning, coding, debugging, bug fix, code review, refactoring, testing, or release, select `engineering-stage-professionalism` to name the current engineering stage, launch only that stage's minimum capabilities, record skipped heavy capabilities with a reason, set a context budget, and name the next-stage handoff; do not launch every stage's capabilities at once, do not launch architecture deep review during coding, and do not launch the release gate during code review.
- If the task edits a SKILL.md body, a foundation capability, a professional skill, a domain extension, a `references` file, the skill registry, or routing rules, select `skill-authoring-expert` so the change keeps a clear boundary, precise triggers, a testable output contract, synchronized registry impact, and a disciplined context budget.
- When selecting `skill-authoring-expert` for routing or behavior changes, also select `repository-context-map`, `skill-efficacy-benchmark`, and `plan-execution-consistency` unless the edit is a trivial typo with no behavior or registry impact.
- If the user says "simplest", "minimal", "smallest correct", "YAGNI", "do less", "avoid overengineering", "what can we delete", "avoid new dependency", "use stdlib/native", or asks for a smallest correct path, select `minimal-correct-implementation`.
- If a request asks for a dependency, abstraction, factory, interface, strategy, generic manager/processor/helper, wrapper, config option, mode switch, or future-proof structure, select `minimal-correct-implementation` with the relevant structure, dependency, or design capability.
- If review is requested for bloat or overengineering, route a complexity-only pass with `minimal-correct-implementation`; keep normal `code-review`, `quality-test-gate`, `security-privacy-gate`, or `reliability-observability-gate` for substantive correctness and risk.
- If data, cache, queue, search, or storage behavior is the change surface, route to `data-middleware-change-builder`.
- If the request touches Redis, ElastiCache, Memorystore, Memcached, cache stampede, hot keys, eviction, maxmemory, RDB/AOF, Redis Cluster, Sentinel, or cache invalidation, select `cache-design`, `data-middleware-change-builder`, and `reliability-observability-gate` when production behavior is affected.
- If the request touches Kafka, Kafka topics, partitions, consumer groups, offset commits, schema registry, topic retention, compaction, consumer lag, DLQ, poison messages, replay, or transactional producers, select `message-queue-design`, `data-middleware-change-builder`, and `bigdata-product-extension` when streaming analytics or data pipelines are involved.
- If the request touches k8s, Kubernetes Deployment, StatefulSet, DaemonSet, Job, CronJob, Service, Ingress, Gateway API, HPA, KEDA, PDB, NetworkPolicy, ServiceAccount, RBAC, ConfigMap, Secret, namespace, probes, or topology spread, select `kubernetes-gateway`, `delivery-release-gate`, and `reliability-observability-gate`; add `security-privacy-gate` for public exposure, RBAC, secrets, or network policy.
- If the request touches Helm, Helm chart, Chart.yaml, values.yaml, values.schema.json, helm template, helm lint, helm upgrade, helm rollback, helm diff, Chart.lock, CRDs, hooks, or OCI charts, select `kubernetes-gateway`, `ci-cd`, `delivery-release-gate`, and `secret-configuration-security` when values or secrets are involved.
- If the request touches Spark, PySpark, Spark SQL, Structured Streaming, Flink, Beam, Databricks, EMR, Glue, Delta Lake, Iceberg, Hudi, dbt, Great Expectations, shuffle skew, partitions, compaction, or distributed data jobs, select `bigdata-product-extension`, `data-middleware-change-builder`, `quality-test-gate`, and `reliability-observability-gate`.
- If external integration behavior is the change surface, route to `integration-change-builder`.
- If tests failed or verification is unclear, route to `quality-test-gate`.
- If security or privacy risk is present, route to `security-privacy-gate`.
- If reliability or performance risk is present, route to `reliability-observability-gate`.
- If deployment or release risk is present, route to `delivery-release-gate`.
- If cost, capacity, FinOps, cloud bill, budget guardrail, autoscaling spend, egress, storage lifecycle, capacity forecast, or cost anomaly risk is present, select `reliability-observability-gate` and `performance-budgeting`.
- If SEV0, SEV1, SEV2, production incident, outage, incident command, mitigation, customer impact, status page, customer communication, or postmortem work is present, select `reliability-observability-gate`, `failure-diagnosis`, and `change-documentation-gate`.
- If Terraform, Pulumi, IaC, cloud IAM, public bucket, DNS, CDN, WAF, KMS, policy as code, or cloud account/project governance is present, select `ci-cd`, `delivery-release-gate`, and `security-privacy-gate`.
- If SOC 2, ISO 27001, audit evidence, compliance control, IAM privilege escalation, or public bucket exposure is present, select `security-privacy-gate`, `delivery-release-gate`, and `change-documentation-gate` when evidence artifacts are required.
- If an A/B test, exposure event, funnel, cohort, primary metric, guardrail metric, SRM/sample ratio mismatch, or experiment decision is present, select `experience-impact-modeler`, `acceptance-criteria-builder`, `quality-test-gate`, and `bigdata-product-extension`.
- If MLOps, ML model rollout, model registry, feature store, training-serving skew, model drift, label leakage, shadow/canary, fairness, or rollback model is present, select `ai-product-extension`, `bigdata-product-extension`, `reliability-observability-gate`, and `quality-test-gate`.
- If monorepo, affected tests, incremental build, Bazel, Pants, Nx, Turborepo, generated files, devcontainer, or build cache correctness is present, select `architecture-impact-reviewer`, `ci-cd`, `package-dependency-management`, and `quality-test-gate`.
- If AI code quality risk is present, route to `ai-code-review-refactor`.
- If docs are stale or behavior changed, route to `change-documentation-gate`.
- If the user asks which language or stack to use, select `technology-stack-selection` and `language-runtime-selection`.
- If a language is already chosen, select `language-idiom-enforcement`, `language-testing-strategy`, and `language-performance-safety` when implementation, review, testing, or runtime behavior is in scope.
- If the request touches Go, Java/JVM, TypeScript, Python, Rust, C/C++, Shell/CLI, or SQL specifically, select the matching language professional usage capability.
- If package manager, dependency, lockfile, upgrade, license, provenance, or supply-chain behavior is involved, select `package-dependency-management`.
- If the request touches an SDK, generated client, reusable library, public API client, or published package contract, select `sdk-library-contract-design`.
- If the request touches a CLI, TUI, daemon, scriptable command, config precedence, stdout/stderr contract, exit code, signal behavior, dry run, or background process interface, select `cli-daemon-interface-design`.
- If the request touches upload, download, object storage, large file handling, media/image processing, MIME detection, virus scanning, signed URLs, retention, or cleanup, select `file-storage-processing`.
- If the request touches internationalization, localization, timezone, date/time, currency, money precision, number formatting, collation, pluralization, or locale fallback, select `i18n-timezone-money-safety`.
- If high-risk code generation occurs in any language, select `solution-optimality-evaluation` and the matching language professional usage capability.

## Failure Modes
- **Over-routing** creates process drag and hides the next best action.
- **Under-routing** misses security, data, release, and user-impact risk.
- **Treating every request as greenfield** wastes time and ignores existing module ownership.
- **Treating local fixes as risk-free** can miss permissions, migrations, external integrations, same-pattern defects, and regression evidence.
- **Listing every capability without selection rationale** makes the route unusable.
- **Dropping route manifests at handoff** loses selected stage, evidence obligations, residual risk, and next gate.
- **Ignoring runtime profile boundaries** can install source authoring directories or assume undeclared runtime content.
- **Confusing hidden-risk triggers with checklists** inflates routes without improving professional evidence.

## Reference Loading Policy
Do not load every reference by default. Treat references as targeted support selected by the router and the task risk. `required_references` is an allow-list, not a convenience list.

- L1 changes: read only router self-use references needed to classify the route plus selected capability references. Do not read unrelated professional skill, domain extension, language, or checklist references.
- L2 changes: read the selected owner and reviewer skill bodies, `references/capabilities/index.md` when needed to locate compiled capability files, the necessary mode reference for the current route, and only capability files explicitly selected by `change-forge-router`.
- L3 changes: read all selected capability references and the relevant impact/API/security/test/release checklist sections when those surfaces are selected; list adjacent skipped references with a reason.
- L4/L5 changes: read the full relevant selected path, including selected owner/reviewer skill references, selected capability references, selected domain extension references, and `references/checklist.md` when present. Still do not read unrelated language or domain references.
- Runtime profile boundary: `recommended` loads selected professional skills with compiled selected capability references; `full` may additionally load selected domain extensions; `dev` may inspect source registries and generated references for authoring validation, but only for selected route surfaces.
- `required_references` must contain only router self-use references, selected capability references, selected owner/reviewer mode references, selected domain extension references, and selected checklist references required by the route.
- `skipped_references` or the skipped rationale must explain why nearby capabilities, language references, domain extensions, professional skills, and quality gates were not loaded.
- Final handoff must restate selected references, skipped references or skipped rationale, validation evidence, residual risk, and any reference loading limit that remains.
- Selected capability reference path format: `references/capabilities/<capability-id>-<capability-name>.md`.

## Output Contract
Return the Markdown Routing Result using `references/route-result-template.md` as the exact section template. It owns the runtime prompt execution gates plus the route sections: Request Classification, Interpreted Change, Missing Information, Requirement Clarification Gate, Read-Before-Plan Gate, TDD Plan Gate, Impact Areas, Professional Skill Path, Foundation Capabilities, Domain Extensions, Required References, Task DAG, Action Skill Map, Review And Repair Loop, Quality Gates, Next Actions, and Stage Professionalism.

Use `None` when a domain extension is not selected. Use `Skipped: reason` for quality gates that are not needed. Use concrete assumptions rather than silent gaps.

The routing result must also state:
- **Mode selected**: routing mode and trigger signal that selected it.
- **Boundaries inspected**: request scope, product/code/data/security/release/docs surfaces, source-vs-dist boundary when authoring skills, and skipped surfaces with reasons.
- **Clarification status**: blocked, clarified, or clarified-with-assumptions, including current behavior, desired behavior, non-goals, constraints, acceptance/TDD signal, blocking questions, assumptions, and risk.
- **Repository context map**: owning surface, related files, caller/callee flow, local conventions, tests, configs, docs, generated artifacts, rejected locations, and not-inspected boundaries before plan.
- **Workflow state summary**: current stage, allowed next transition, owner/reviewer split, validation freshness, review/repair state, and closure readiness.
- **TDD plan evidence**: failing/new/updated test, eval, validation command, acceptance check, or not-verified fallback before implementation starts.
- **Tool permission/sandbox record**: tool, command/action class, permission state, sandbox boundary, dry-run/revert path, secret/output redaction rule, and escalation owner when risky tools are used.
- **Action ownership and review map**: every action names owner skill, selected capabilities, input, output, independent review skill, review evidence, and repair route if review fails.
- **Skill efficacy benchmark plan**: for skill/routing/eval changes, the baseline behavior case, expected treatment behavior, token/turn overhead signal, regression fixture, and validator command.
- **Minimal Correctness Decision**: when `minimal-correct-implementation` is selected, record the existence challenge, simplicity ladder result, delete/shrink findings, dependency/abstraction/file/config decisions, shortcut ledger entries, validation evidence, residual risk, and next gate.
- **Repair/re-review record**: review findings, repair owner, re-review result, remaining risk, and the point at which closure is allowed.
- **Plan-execution consistency check**: accepted plan, actual changed files, validation commands, skipped work, unplanned behavior changes, stale evidence, and residual-risk reconciliation.
- **Professional judgment**: why the route is minimum sufficient, which hidden risks were escalated or ruled out, and why skipped gates are safe.
- **Reuse and placement rationale**: existing professional skill, capability, reference, or registry path reused instead of inventing a new path.
- **Behavior preservation statement**: existing runtime profile, skill registry, source/dist separation, and routed behavior preserved or intentionally changed.
- **Validation evidence**: eval, validator, build, or not-verified disclosure expected before closure.
- **Evidence limits**: what routing evidence proves and does not prove about code correctness, production behavior, or downstream consumer adoption.
- **Residual risk and next gate**: unresolved assumption, owner, handoff target, and next skill/gate.

Populate Required References for router self-use and for every selected support reference:

- Always include router self-use references: `references/routing-rules.md`, `references/skill-registry.md`, `references/capability-index.md`, and `references/domain-extension-index.md`.
- Whenever foundation capabilities are selected, list selected capability files under `references/capabilities/` for each selected professional skill.
- For L3 and higher changes, include `references/checklist.md` when present.
- For L4/L5 changes with a selected domain extension, include the selected domain extension `SKILL.md` and any selected domain extension reference.

### Machine-Readable Route Manifests
After the Markdown Routing Result, also emit two fenced YAML blocks that hooks, doctor, telemetry review, and the routing/agent-behavior eval tools parse. They never replace the human-readable sections and never authorize any tool to mutate skills, routing rules, or capabilities.

- `changeforge_route`: the route projection — `route_id`, `complexity`, `risk_level`, `execution_mode`, `selected_skills`, `selected_capabilities`, `selected_domain_extensions`, `required_references`, `required_quality_gates`, `skipped_quality_gates` (each with a `reason`), `blocking_questions`, `assumptions`, `runtime_prompt_flow`, and `handoff_target`. `runtime_prompt_flow` carries closure mode, clarification status, inspected boundaries, TDD signal, action owner/review/repair mapping, validation evidence, and residual risk so direct specialist-skill invocation can skip reclassification without skipping the execution protocol; `plan` may keep review/validation pending, while `action-handoff` and `final-handoff` require completed, blocked-with-risk, or explicitly not-verified closure evidence. Every ordinary `selected_capabilities` entry must map to a `selected_skills` entry via the capability `used_by` relationship; route-level capabilities marked in the registry are allowed at manifest level. `required_references` must list the four router self-use references plus the deterministic `references/capabilities/<capability-id>-<capability-name>.md` path for each selected capability.
- `changeforge_stage_route`: the stage projection of `## 12. Stage Professionalism` — `schema_version`, `current_stage`, `next_stage`, legacy `product_surface` / `language_surface`, `primary_product_surface`, `primary_language_surface`, `product_surfaces`, `language_surfaces`, the `selected_*` lists, `skipped_capabilities` (foundation capability names only, each with a `reason`), `skipped_skills`, `skipped_routes`, `context_budget_mode` (`minimal` for L1, `single-stage` for L2, `staged-plan` for L3+), `context_budget_rationale`, `required_evidence`, `required_quality_gates`, and `handoff_target`. Emit it only for non-trivial engineering tasks, name exactly one `current_stage`, and keep it consistent with `changeforge_route`.

Full manifest schemas, field templates, and rules: `references/route-manifest.md`.

## Evidence Contract
Close routing only when all canonical evidence answers are concrete (answer schema: `agent-execution-discipline`):
- **Basis**: selected routing mode, request classification, risk triggers, and runtime profile awareness.
- **Files and boundaries inspected**: request text, repository context map, registry/routing rules, source-vs-dist boundary, product/code/data/security/release/docs surfaces, caller/callee flow, and skipped gates with reasons.
- **Placement rationale**: why each selected professional skill and capability is the owner, why omitted skills are not needed, and why no new runtime structure is introduced.
- **Validation commands**: routing eval, agent-behavior eval, skill-efficacy benchmark validator when applicable, skill validator, build/install validator, or not-verified disclosure required for the route.
- **Routing judgment and evidence limits**: minimum sufficient path, workflow state, plan-execution consistency, behavior preservation, what evidence proves, what it does not prove, residual risk, and next gate.

## Quality Gate
The route passes only when:

- Every selected professional skill has a clear reason, input, and expected output.
- Every ordinary selected foundation capability is tied to a selected professional skill; route-level capabilities are explicitly marked in the registry.
- Every selected domain extension has a domain signal, risk, and required output.
- Required References lists router self-use references and every selected capability, checklist, or domain extension reference required by the route.
- Every impacted area has a selected skill, a quality gate, a non-blocking assumption, or an explicit skip reason.
- Complexity and risk match the escalation triggers.
- The task DAG is acyclic, reviewable, acceptance-linked, rollback-aware, and each task has `owner_skill`, a different `review_skill`, review evidence, and repair/re-review instructions.
- The requirement clarification, repository-context-map, workflow-state, and TDD plan gates are complete or explicitly blocked before implementation begins.
- Risky tool, connector, deployment, migration, network-write, destructive filesystem, and secret-bearing operations have a tool permission/sandbox record before execution.
- Skill, routing, stage, hook, eval, and benchmark changes carry a skill-efficacy benchmark plan or an explicit not-applicable rationale.
- Final review and handoff include plan-execution consistency: accepted plan vs. changed files, validation commands, skipped work, residual risk, and stale evidence.
- Each action has an action-specific owner skill and independent review skill; the same skill cannot close its own action review.
- Any review finding has a repair owner and a completed re-review before handoff, or the handoff is blocked with residual risk.
- The `changeforge_route` manifest is present, lists the router self-use references and selected capability references, maps each selected capability to a selected skill, and records every skipped gate with a reason.
- For non-trivial engineering tasks, the `changeforge_stage_route` manifest is present, names one `current_stage`, records plural product/language surfaces, records `skipped_capabilities`, `skipped_skills`, and `skipped_routes` with reasons, and matches the `## Stage Professionalism` section.
- The route does not rely on undeclared asset ingestion, external knowledge stores, or undeclared runtime content.

## Handoff
Hand off to the first unblocked skill in the professional path. Preserve request classification, interpreted change, missing information, impact areas, selected capabilities, domain extension requirements, required references, task DAG, quality gates, and recommended execution mode.

If blocked, hand off only to the skill that can remove the block. If unblocked, hand off to the next implementation, gate, or documentation skill according to the minimum sufficient path.

## Completion Criteria
The routing result is complete when an implementing agent can start the next skill with clear scope, risk, dependencies, selected capabilities, required references, quality gates, validation expectations, and rollback notes without guessing which ChangeForge path applies or which references to read.
