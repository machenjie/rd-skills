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
- For engineering prompts in a target project, run the runtime prompt execution protocol before any implementation path: clarify requirement, inspect relevant target-project evidence before planning, produce senior programming judgment evidence for non-trivial behavior, create a TDD-oriented plan, split action-specific skill ownership, require independent review, repair findings, re-review, and hand off with evidence. Pure explanation, translation, or question-answering with no engineering action may skip the full protocol only after stating that no engineering action is being taken.
- Do not plan engineering work before inspecting the relevant target-project code, tests, configs, docs, existing implementation, and likely call chain. A plan based only on the user prompt is invalid unless the prompt is explicitly asking for non-executing advice and no target-project action will follow.
- Do not route a single generalized skill to own every action. Each action must have the most specific owner professional skill or selected capability, and each completed action must have a review skill or capability that is different from the owner.
- If review finds a defect, missing evidence, wrong boundary, or untested acceptance path, route repair back to the owner skill or the appropriate specialist, then repeat review before closure.
- Escalate risk when auth, authorization, object-level permission, payment, subscription, billing, wallet, private key, Web3 asset, user data, PII, file upload, AI prompt, RAG, external integration, webhook, database migration, production deployment, production incident, cloud IAM, public exposure, regulated workload, compliance evidence, cost anomaly, secret/config change, security-sensitive dependency upgrade, or irreversible data operation is plausible.
- Route domain extensions only when domain signals are present; do not attach them because they are available.
- Route foundation capabilities as targeted support for selected professional skills; do not list all capabilities unless the user asks for a catalog.
- Select `senior-programming-judgment-core` for non-trivial engineering, skill-authoring, hook-runtime, routing, registry, eval, or benchmark behavior changes unless an explicit trivial/no-semantic/no-engineering skip reason is recorded.
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

- Select only the foundation capabilities that support the chosen professional skills and route risk.
- Load references/routing-signals.md for the capability group map and detailed signal-to-skill/capability lookup.

Domain extension routing:

- `web3-product-extension`: wallet, signature, smart contract, blockchain transaction, token, on-chain/off-chain state, custody, private key, chain data, nonce, replay, reorg, or network mismatch.
- `ai-product-extension`: LLM, RAG, agent, embedding, vector database, prompt, model output, tool use, hallucination, evaluation, AI safety, generated content, permission-aware retrieval, MLOps, model registry, model drift, training-serving skew, feature store, or label leakage.
- `mobile-product-extension`: Android, iOS, mobile app, offline mode, push notification, app lifecycle, platform permission, deep link, app store release, background execution, or mobile compatibility.
- `bigdata-product-extension`: stream, batch job, warehouse, analytics, reporting, ETL/ELT, lineage, freshness, backfill, replay, schema drift, dashboard metric, product experiment, A/B test, guardrail metric, SRM, feature store, or partitioning.
- `iot-embedded-extension`: device, firmware, embedded, sensor, actuator, edge protocol, OTA, hardware resource limit, connectivity loss, physical safety, or field operations.
- `payment-trading-extension`: payment, subscription, billing, invoice, refund, chargeback, trading, ledger, balance, checkout, reconciliation, settlement, entitlement, or tax.
- `low-level-systems-extension`: OS, kernel, driver, native performance, C, C++, Rust systems, FFI, ABI, syscall, memory safety, atomics, descriptor, or platform runtime.

Runtime profile awareness: recommended has 21 professional skills; full has 21 professional skills plus 7 domain extensions; dev has 21 professional skills, 136 foundation capabilities, and 7 domain extensions. Foundation capabilities compile into professional references in every profile.

## Mode Matrix
Select the routing mode before naming a professional path.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
|---|---|---|---|---|---|
| Initial classification | Request lacks complete stage, risk, skill, capability, and gate selection. | Choose the minimum sufficient route and preserve unknowns as questions or assumptions. | Change type, complexity, risk level, execution mode, selected skills/capabilities, skipped gates with reasons. | `engineering-stage-professionalism`, `context-packaging` | Listing every available skill or capability. |
| Route repair | Same path failed twice, diagnosis is weak, local fix lacks scan, or completion lacks evidence. | Change route based on new evidence instead of repeating the same action. | Failed command/output, route-repair reason, verified-cause gap, next diagnostic skill. | `agent-execution-discipline`, `failure-diagnosis` | Third same-path retry. |
| Hidden-risk escalation | Request hints at IDOR, queue duplicate, cache invalidation, webhook replay, migration rollback, accessibility, generated code, or shared utility pollution. | Upgrade only the risk-relevant path and record over-routing guard. | Trigger signal, hidden risk, routed skill/capability, evidence required, forbidden over-route. | `change-impact-analyzer`, `quality-test-gate` | Broad L4/L5 routing when a targeted L2/L3 route suffices. |
| Runtime profile selection | recommended/full/dev behavior, foundation reference loading, build/install, or skill authoring is in scope. | Keep runtime profile boundaries and source/dist separation correct. | Profile selected, source vs dist boundary, required references, validation commands. | `skill-authoring-expert`, `repository-context-map`, `skill-efficacy-benchmark`, `delivery-release-gate` | Installing source directories or runtime content from `src/`. |
| Context control | Context budget, reference bloat, selected/skipped references, JIT retrieval, tool-output boundary, compaction snapshot, branch repair summary, or overhead evidence is in scope. | Keep route context high-signal, privacy-safe, and auditable without dropping required evidence. | `context_control` record with budget mode, selected/skipped references, JIT plan, output boundary, snapshot/repair needs, overhead evidence, residual risk. | `context-control-plane`, `validation-broker`, `execution-trajectory-analysis` | Generic context-engineering route or loading every related reference. |
| Senior programming judgment | Non-trivial engineering behavior, object relationships, states, rules, invariants, boundaries, failure contract, side effects, validation map, observability, or residual risk are in scope. | Require source-backed senior judgment evidence without turning it into a persona or replacing specialist capabilities. | `senior_programming_judgment` record or explicit trivial/no-semantic/no-engineering skip reason. | `senior-programming-judgment-core`, `implementation-structure-design`, `quality-test-gate`, `agent-execution-discipline` | Treating BSP, clean code shape, or local tests as complete senior judgment. |
| Business semantic control | Business intent, vocabulary, object ownership, rule authority, workflow state, stale business memory, graph-as-selector, golden cases, or semantic review is in scope. | Produce a task-scoped Business Semantic Pack decision without becoming a business-expert corpus. | BSP trigger decision, source-backed facts, memory/graph selector limits, validation map, selected/skipped references, residual semantic risk. | `business-semantic-control-plane`, `domain-object-identification`, `business-rule-extraction`, `state-machine-modeling`, `context-control-plane` | Treating memory or repository graph as business fact. |
| Handoff closure | Routing result is final or an agent hands off after routed work. | Preserve route manifest, stage state, plan consistency, evidence limits, residual risk, and next gate. | `changeforge_route`, optional `changeforge_stage_route`, plan-vs-diff/validation consistency, validation/not-verified disclosure, residual risk. | `agent-execution-discipline`, `agent-workflow-state-machine`, `plan-execution-consistency`, `change-documentation-gate` | Completion claims without closure evidence. |

## Proactive Professional Triggers
These triggers are hidden-risk escalators, not ordinary checklist items.

- **Signal:** A local bug fix touches one permission, tenant, query, cache, retry, or validation path. **Hidden risk:** missing same-pattern repair leaves sibling defect paths unverified. **Required professional action:** route same-pattern scan and regression evidence before implementation closure. **Route to:** `change-impact-analyzer`, `agent-execution-discipline`, `regression-testing`. **Evidence required:** pattern scan output, searched scope, related occurrences, and local/broad fix rationale.
- **Signal:** Queue consumer, webhook, retry, cron, or background job is mentioned without idempotency, replay, DLQ, or terminal failure behavior. **Hidden risk:** duplicate side effects or lost work under at-least-once delivery. **Required professional action:** select idempotency/queue/integration/reliability route. **Route to:** `idempotency-retry-design`, `message-queue-design`, `integration-change-builder`, `reliability-observability-gate`. **Evidence required:** key scope, retry/DLQ, replay protection, duplicate-delivery test.
- **Signal:** Cache, Redis, CDN, or memoization is added for performance without TTL, invalidation, scope, or source-of-truth statement. **Hidden risk:** stale data, tenant leak, stampede, or cache-as-source-of-truth drift. **Required professional action:** route cache design and observability gate when production-facing. **Route to:** `cache-design`, `data-middleware-change-builder`, `observability`. **Evidence required:** key schema, TTL/invalidation, tenant/permission scope, cache-loss behavior.
- **Signal:** Migration, schema change, feature flag, rollout, or config change lacks rollback and old/new compatibility. **Hidden risk:** revert deploy cannot recover mutated state. **Required professional action:** route release/rollback and data contract checks. **Route to:** `delivery-release-gate`, `release-rollback`, `data-api-contract-changer`. **Evidence required:** expand/contract plan, rollback command, compatibility window, validation output.
- **Signal:** AI-generated code introduces helpers, abstractions, public exports, dependencies, or API calls without reuse search. **Hidden risk:** hallucinated API, duplicate logic, or shared utility pollution. **Required professional action:** route AI code review plus implementation structure and code review. **Route to:** `ai-code-review-refactor`, `implementation-structure-design`, `code-review`. **Evidence required:** symbol/dependency verification, reuse search, placement rationale, tests or not-verified disclosure.
- **Signal:** log, logger, logging, audit log, diagnostic log, security log, access log, structured logging, fallback log, retry log, degradation log, error log, lifecycle log, trace_id, span_id, request_id, correlation_id, or redaction is mentioned. **Hidden risk:** noisy or unsafe logs can hide failure modes, leak PII/secrets, mix audit and diagnostics, or lack testable evidence. **Required professional action:** route logging design and log/security validation. **Route to:** `logging-design-gate`, `logging-error-handling`, `quality-test-gate`; add `security-privacy-gate` for raw request body, raw query, authorization header, cookie, token, or PII. **Evidence required:** log type, level, fields, redaction, correlation, cardinality control, and logging/security tests or no-log rationale.
- **Signal:** context budget, token overhead, reference bloat, selected references, skipped references, JIT retrieval, graph-as-selector, tool-output boundary, compaction snapshot, branch summary, route repair summary, output truncation, or benchmark overhead is mentioned. **Hidden risk:** missing validation evidence, stale route state, or bloated context makes decisive routing rules easy to miss. **Required professional action:** route to `context-control-plane`, require selected/skipped reference rationale, and preserve bounded output evidence. **Route to:** `context-control-plane`, `validation-broker`, `execution-trajectory-analysis`. **Evidence required:** budget mode, selected/skipped reference rationale, JIT retrieval plan, output boundary, snapshot/repair needs, validation command status, overhead evidence or `not_collected`, and residual context risk.
- **Signal:** Non-trivial engineering, requirement intake, diagnosis, architecture, hook/runtime, routing, registry, schema, eval, benchmark, or closure behavior is described without purpose, source-backed facts, object/state/rule/invariant map, boundary, failure contract, validation proof limits, and residual-risk ownership. **Hidden risk:** the route can appear professional while missing the judgment that connects code or skill behavior to real constraints and proof. **Required professional action:** route senior programming judgment as evidence attached to the current action owner, not as a persona or catch-all route. **Route to:** `senior-programming-judgment-core`, current action owner, `quality-test-gate`, `agent-execution-discipline`. **Evidence required:** `senior_programming_judgment` or allowed skip reason, validation proof/does-not-prove fields, residual risk owner, and next gate.
- **Signal:** business context missing, business vocabulary ambiguous, business object ownership unclear, business rule authority unknown, business workflow state unclear, business invariant changed, business rule hidden in SQL/controller/UI/test, DTO used as business object, business memory affects decision, business golden case missing, technical refactor may change business semantics, business semantic review required, graph used as business fact, or memory used as business fact. **Hidden risk:** AI treats unverified memory, graph proximity, DTO/table names, controller/SQL/UI/test conditions, or old fixtures as business authority. **Required professional action:** route to `business-semantic-control-plane`, classify evidence, and require source-backed facts plus validation mapping. **Route to:** `business-semantic-control-plane`, `domain-impact-modeler`, `quality-test-gate`, `ai-code-review-refactor`. **Evidence required:** task-scoped BSP trigger decision, rule owner/enforcement layer, memory/graph selector limits, selected/skipped structured reference decisions, golden case or residual risk.

## Risk Escalation Rules
Escalate one level for any risk trigger that affects user data, money, permissions, external systems, production state, or irreversible operations. Escalate to high or critical when more than one high-impact trigger is present or when rollback is unclear.

Risk triggers include auth, authorization, object-level permission, payment, subscription, billing, wallet, private key, Web3 asset, user data, PII, file upload, AI prompt, RAG, external integration, webhook, database migration, production deployment, production incident, secret/config change, cloud IAM, public exposure, regulated workload, compliance evidence, cost anomaly, dependency upgrade with security impact, irreversible data operation, raw request body, raw query, authorization header, cookie, token, audit log, security log, access log, structured logging that can expose sensitive data, context budget exceeded, reference bloat, selected references missing rationale, skipped references missing rationale, tool output too large, compaction snapshot, branch route repair summary, context control plane, business semantic pack, business context missing, business vocabulary ambiguous, business object ownership unclear, business rule authority unknown, business workflow state unclear, business invariant changed, business rule hidden in SQL/controller/UI/test, DTO used as business object, business memory affects decision, business golden case missing, technical refactor may change business semantics, business semantic review required, graph used as business fact, memory used as business fact.

Legacy aliases such as business term ambiguous, rule authority unclear, hidden business rule, hidden sql rule, hidden controller rule, and stale business memory remain accepted in registry and hook routing for compatibility.

Escalate to L5 when regulated, financial, Web3, AI, migration, or production-critical behavior combines with security, data integrity, external dependency, or rollback risk.

## Action-Specific Owner And Review Routing
Select only rows that match the actual action; the owner and review skill must differ.

Keep the main body on the invariant: every action has a specific owner, selected capabilities, an output, a different reviewer, review evidence, and a repair route. Load [references/routing-signals.md](references/routing-signals.md#action-specific-owner-and-review-routing) for the detailed owner/reviewer lookup table when building a non-trivial action map.

## Critical Details
Read `references/checklist.md` for non-trivial routing. Read `references/routing-signals.md` when the request has broad, hidden-risk, skill-authoring, runtime, language, or domain-specific route signals. Use generated router references for the current skill registry, capability index, domain extension index, and routing rules when available.

### Runtime Prompt Execution Protocol
This protocol applies when a developer uses ChangeForge skills in any target project for feature work, bug fixing, refactoring, testing, review, debugging, release, documentation, API/data, security, reliability, or other engineering action. It is not limited to authoring this repository.

1. **Requirement clarification gate.** Before any engineering operation, clarify current behavior, desired behavior, non-goals, constraints, acceptance, and the TDD or validation signal. If a blocking unknown could change the data model, API contract, authorization boundary, rollout, rollback, or user-visible behavior, stop and ask the blocking question. If execution may proceed, record assumptions and risk.
2. **Repository context map gate.** Before planning or action, select `repository-context-map` for target-project engineering or skill-authoring work and inspect the owning surface, sibling conventions, likely caller/callee path, tests, configs, docs, generated artifacts, and rejected placement locations. A plan without repository-context evidence is invalid.
3. **Senior programming judgment gate.** Select `senior-programming-judgment-core` for non-trivial engineering, skill-authoring, hook-runtime, routing, registry, eval, or benchmark behavior changes. Emit `senior_programming_judgment` with purpose, source-backed facts, objects, states, behaviors, rules, invariants, boundaries, failure contract, side effects, reuse/placement, minimality, validation map, observability map, and residual risk, or record an explicit trivial/no-semantic/no-engineering skip reason.
4. **Workflow state gate.** Select `agent-workflow-state-machine` for non-trivial engineering work so the current phase, allowed next phase, owner/reviewer split, validation freshness, repair loop, and closure state are explicit before and after each phase transition.
5. **TDD plan gate.** Before implementation, name the failing, new, or updated test, eval, validation command, acceptance check, or explicit not-verified residual risk that proves the intended behavior.
6. **Action-specific skill routing.** Break the work into actions. Each action has an owner professional skill or selected capability matched to the action type: intake, acceptance, impact, planning, frontend, backend, API/data, middleware, integration, security, reliability, docs, test, release, or final handoff.
7. **Tool permission/sandbox gate.** Before risky commands, destructive operations, network writes, MCP/connector calls, migrations, deploys, secret access, or filesystem-wide edits, select `agent-tool-permission-sandbox` and record the tool, permission state, sandbox boundary, dry-run/revert path, and secret/output redaction rule.
8. **Independent review gate.** Each action has a review skill or capability different from the owner. Review evidence must be concrete; self-review by the same owner skill is not enough.
9. **Repair/re-review loop.** Any review finding routes repair to the owner skill or appropriate specialist, then repeats independent review. Handoff is invalid while review findings remain unresolved or unreviewed after repair.
10. **Plan consistency gate.** Before final review or handoff, select `plan-execution-consistency` and compare the accepted plan, changed files, validation commands, skipped work, and residual risks. Any unplanned file or behavior change routes back to planning/review.
11. **Evidence handoff.** Final handoff carries clarification, repository context, senior programming judgment evidence or skip reason, TDD evidence, workflow state, action-to-skill map, tool permission/sandbox evidence when applicable, review results, repair/re-review record, plan-execution consistency, validation results, residual risk, next gate, and the `changeforge_route` / `changeforge_stage_route` manifests.

Route by evidence in the request. Keep the main body focused on the invariant: select the minimum sufficient owner/reviewer path, add hidden-risk gates only when trigger evidence exists, and preserve source/dist runtime profile boundaries. Load `references/routing-signals.md` for the detailed signal-to-skill and signal-to-capability map.

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
Return the Markdown Routing Result using `references/route-result-template.md` as the exact section template. It owns the runtime prompt execution gates plus the route sections: Request Classification, Interpreted Change, Missing Information, Requirement Clarification Gate, Read-Before-Plan Gate, Senior Programming Judgment Gate, TDD Plan Gate, Impact Areas, Professional Skill Path, Foundation Capabilities, Domain Extensions, Required References, Task DAG, Action Skill Map, Review And Repair Loop, Quality Gates, Next Actions, and Stage Professionalism.

Use `None` when a domain extension is not selected. Use `Skipped: reason` for quality gates that are not needed. Use concrete assumptions rather than silent gaps.

The routing result must also state:
- **Mode selected:** routing mode and trigger signal.
- **Boundaries inspected:** request scope, product/code/data/security/release/docs surfaces, source-vs-dist boundary, and skipped surfaces with reasons.
- **Clarification and repository context:** current/desired behavior, non-goals, constraints, acceptance/TDD signal, assumptions, owning surface, callers/callees, conventions, tests, configs, docs, generated artifacts, rejected locations, and not-inspected boundaries.
- **Workflow and TDD state:** current stage, allowed next transition, owner/reviewer split, validation freshness, review/repair state, closure readiness, and failing/new/updated test, eval, validation command, acceptance check, or not-verified fallback.
- **Tool permission/sandbox record:** tool/action class, permission state, sandbox boundary, dry-run/revert path, redaction rule, and escalation owner when risky tools are used.
- **Action ownership and review map:** owner skill, selected capabilities, input, output, independent review skill, review evidence, and repair route for each action.
- **Special decision records:** skill efficacy benchmark plan for skill/routing/eval changes and Minimal Correctness Decision when `minimal-correct-implementation` is selected.
- **Repair, consistency, and judgment:** repair/re-review result, plan-execution consistency, minimum-sufficient rationale, hidden risks escalated or ruled out, skipped-gate rationale, reuse and placement rationale, behavior preservation, validation evidence, evidence limits, residual risk, and next gate.

Populate Required References for router self-use and every selected support reference: always include `references/routing-rules.md`, `references/skill-registry.md`, `references/capability-index.md`, and `references/domain-extension-index.md`; list selected `references/capabilities/` files; include selected checklists for L3+; include selected domain extension skill/reference files for L4/L5 domain routes.

### Machine-Readable Route Manifests
After the Markdown Routing Result, also emit two fenced YAML blocks that hooks, doctor, telemetry review, and the routing/agent-behavior eval tools parse. They never replace the human-readable sections and never authorize any tool to mutate skills, routing rules, or capabilities.

- `changeforge_route`: the route projection — `route_id`, `complexity`, `risk_level`, `execution_mode`, `selected_skills`, `selected_capabilities`, `selected_domain_extensions`, `required_references`, `required_quality_gates`, `skipped_quality_gates` (each with a `reason`), `blocking_questions`, `assumptions`, `context_control` when selected or context risk exists, BSP route fields when selected (`business_semantic_pack_required`, `business_semantic_scope`, `business_semantic_triggers`, `business_semantic_evidence_required`, `business_semantic_residual_risk`), `runtime_prompt_flow`, and `handoff_target`. `context_control` carries budget mode, selected/skipped reference counts and rationale, JIT retrieval plan, tool-output boundary, compaction snapshot requirement, branch route-repair summary requirement, overhead evidence status, and residual context risk. BSP route fields carry the task-scoped semantic decision, source-backed FACT obligations, memory/graph selector limits, validation map expectation, selected/skipped reference rationale, and residual semantic risk. `runtime_prompt_flow` carries closure mode, clarification status, inspected boundaries, `senior_programming_judgment` or an allowed skip reason, TDD signal, action owner/review/repair mapping, validation evidence, and residual risk so direct specialist-skill invocation can skip reclassification without skipping the execution protocol; `plan` may keep review/validation pending, while `action-handoff` and `final-handoff` require completed, blocked-with-risk, or explicitly not-verified closure evidence. Every ordinary `selected_capabilities` entry must map to a `selected_skills` entry via the capability `used_by` relationship; route-level capabilities marked in the registry are allowed at manifest level. `required_references` must list the four router self-use references plus the deterministic `references/capabilities/<capability-id>-<capability-name>.md` path for each selected capability.
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
- For non-trivial engineering tasks, `runtime_prompt_flow.senior_programming_judgment` is present or has an allowed skip reason.
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
