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

The router is the orchestration brain. It decides what to use, what to skip, what to ask, what to defer, and what evidence is required before downstream work starts.

## When To Use
Use before implementation, investigation, review, release, or documentation work when the request does not already provide a complete skill path, risk level, impact model, capability set, execution mode, and quality gate plan.

Use the router especially when the request is broad, ambiguous, high risk, cross-module, domain-specific, production-facing, or likely to involve API, data, security, reliability, release, or documentation impact.

## Do Not Use When
Do not use when a specialist skill is explicitly requested and the scope is already narrow, the impacted surface is known, and no routing decision remains.

Do not use the router to invoke every skill, invent a product program around a local edit, assume a new system is being built, or introduce out-of-scope asset mapping. Runtime work must be based on the request, available project context, and ChangeForge-authored skills, not undeclared external libraries or knowledge stores.

## Non-Negotiable Rules
- Classify the request before prescribing work.
- Choose the minimum sufficient professional path; add skills only when the classification, impact, risk, or missing information requires them.
- Treat bug fixes, refactors, API changes, data changes, migrations, review, tests, docs, reliability, security, and deployment as first-class changes.
- Preserve missing information as blocking questions, non-blocking questions, or explicit assumptions.
- Escalate risk when auth, authorization, object-level permission, payment, subscription, billing, wallet, private key, Web3 asset, user data, PII, file upload, AI prompt, RAG, external integration, webhook, database migration, production deployment, secret/config change, security-sensitive dependency upgrade, or irreversible data operation is plausible.
- Route domain extensions only when domain signals are present; do not attach them because they are available.
- Route foundation capabilities as targeted support for selected professional skills; do not list all capabilities unless the user asks for a catalog.
- Include skipped or deferred areas implicitly through the impact matrix and quality gates instead of padding the professional path.
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

Complexity routing rules:

- L1 isolated local change: use only the relevant builder, review, or test skills. Add intake or acceptance only if the request is unclear or done state is untestable.
- L2 single-module change: include intake, impact when blast radius is uncertain, acceptance, implementation, and test.
- L3 multi-module product change: include intake, impact, domain or architecture if affected, data/API if affected, implementation, security when needed, tests, and docs.
- L4 product-grade high-risk change: include the full relevant path across intake, impact, acceptance, domain/experience/architecture/data/API, implementation, gates, delivery, docs, and AI code review where generated code quality is material.
- L5 regulated/financial/Web3/AI/migration/production-critical: include the matching domain extension, security, reliability, delivery, rollback, documentation, evidence requirements, and explicit stop conditions.

Professional skill routing:

- `change-intake-compiler`: unclear requirement, missing current or desired behavior, unclear constraints, unknown non-goals.
- `change-impact-analyzer`: unknown blast radius, cross-surface changes, uncertain product/code impact.
- `acceptance-criteria-builder`: untestable done state, weak success criteria, missing negative or regression cases.
- `task-dag-planner`: task too large, dependency ordering needed, rollback or parallelization needed.
- `experience-impact-modeler`: broken user flow, navigation, accessibility, interaction states, or UX regression risk.
- `domain-impact-modeler`: business behavior, domain rules, permissions, state machines, or event semantics are affected.
- `architecture-impact-reviewer`: architecture drift, module boundaries, layering, service boundaries, or scalability tradeoffs are affected.
- `data-api-contract-changer`: API contract, DTO, schema, compatibility, migration, or error model changes.
- `frontend-change-builder`: frontend implementation, routes, components, state, forms, API integration, or accessibility.
- `backend-change-builder`: backend implementation, validation, auth, transactions, services, jobs, repositories, or errors.
- `data-middleware-change-builder`: SQL, NoSQL, cache, queues, search, storage, consistency, indexing, or middleware.
- `integration-change-builder`: third-party APIs, webhooks, credentials, retries, reconciliation, or external failure modes.
- `quality-test-gate`: tests failed, test plan missing, evidence missing, regression risk exists, or release confidence is weak.
- `security-privacy-gate`: security, privacy, auth, secrets, upload, dependency, AI prompt, or Web3 risk exists.
- `reliability-observability-gate`: performance, reliability, concurrency, rate limits, fallback, observability, or operations risk exists.
- `delivery-release-gate`: deployment, config, migration rollout, CI/CD, feature flags, production release, or rollback risk exists.
- `ai-code-review-refactor`: AI-generated code, refactor quality, hallucinated APIs, hidden assumptions, duplication, or boundary drift risk exists.
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
- Engineering workflow: 76 `context-packaging`, 77 `task-dag-decomposition`, 78 `code-review`, 79 `refactoring`, 80 `documentation-generation`, 81 `failure-diagnosis`, 82 `solution-optimality-evaluation`.
- Technology selection: 83 `technology-stack-selection`, 84 `language-runtime-selection`, 85 `language-idiom-enforcement`, 86 `language-testing-strategy`, 87 `language-performance-safety`, 88 `package-dependency-management`.
- Language professional usage: 89 `go-professional-usage`, 90 `java-jvm-professional-usage`, 91 `typescript-professional-usage`, 92 `python-professional-usage`, 93 `rust-professional-usage`, 94 `cpp-professional-usage`, 95 `shell-cli-professional-usage`, 96 `sql-professional-usage`.
- Interface, storage, and global correctness: 97 `sdk-library-contract-design`, 98 `cli-daemon-interface-design`, 99 `file-storage-processing`, 100 `i18n-timezone-money-safety`.

Domain extension routing:

- `web3-product-extension`: wallet, signature, smart contract, blockchain transaction, token, on-chain/off-chain state, custody, private key, chain data, nonce, replay, reorg, or network mismatch.
- `ai-product-extension`: LLM, RAG, agent, embedding, vector database, prompt, model output, tool use, hallucination, evaluation, AI safety, generated content, or permission-aware retrieval.
- `mobile-product-extension`: Android, iOS, mobile app, offline mode, push notification, app lifecycle, platform permission, deep link, app store release, background execution, or mobile compatibility.
- `bigdata-product-extension`: stream, batch job, warehouse, analytics, reporting, ETL/ELT, lineage, freshness, backfill, replay, schema drift, dashboard metric, or partitioning.
- `iot-embedded-extension`: device, firmware, embedded, sensor, actuator, edge protocol, OTA, hardware resource limit, connectivity loss, physical safety, or field operations.
- `payment-trading-extension`: payment, subscription, billing, invoice, refund, chargeback, trading, ledger, balance, checkout, reconciliation, settlement, entitlement, or tax.
- `low-level-systems-extension`: OS, kernel, driver, native performance, C, C++, Rust systems, FFI, ABI, syscall, memory safety, atomics, descriptor, or platform runtime.

Runtime profile awareness:

- Recommended: 19 professional skills are top-level runtime skills; 100 foundation capabilities are compiled into relevant professional references; the router includes generated routing indexes.
- Full: 19 professional skills plus 7 domain extensions are top-level runtime skills; 100 foundation capabilities remain compiled professional references.
- Dev: 19 professional skills, 100 foundation capabilities, and 7 domain extensions are top-level runtime skills for ChangeForge development and debugging.

## Risk Escalation Rules
Escalate one level for any risk trigger that affects user data, money, permissions, external systems, production state, or irreversible operations. Escalate to high or critical when more than one high-impact trigger is present or when rollback is unclear.

Risk triggers include auth, authorization, object-level permission, payment, subscription, billing, wallet, private key, Web3 asset, user data, PII, file upload, AI prompt, RAG, external integration, webhook, database migration, production deployment, secret/config change, dependency upgrade with security impact, and irreversible data operation.

Escalate to L5 when regulated, financial, Web3, AI, migration, or production-critical behavior combines with security, data integrity, external dependency, or rollback risk.

## Critical Details
Read `references/checklist.md` for non-trivial routing. Use generated router references for the current skill registry, capability index, domain extension index, and routing rules when available.

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
- If data, cache, queue, search, or storage behavior is the change surface, route to `data-middleware-change-builder`.
- If external integration behavior is the change surface, route to `integration-change-builder`.
- If tests failed or verification is unclear, route to `quality-test-gate`.
- If security or privacy risk is present, route to `security-privacy-gate`.
- If reliability or performance risk is present, route to `reliability-observability-gate`.
- If deployment or release risk is present, route to `delivery-release-gate`.
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
Over-routing creates process drag and hides the next best action. Under-routing misses security, data, release, and user-impact risk. Treating every request as greenfield wastes time. Treating local fixes as risk-free can miss permissions, migrations, external integrations, and regression evidence. Listing every capability without selection rationale makes the route unusable.

## Reference Loading Policy
Do not load every reference by default. Treat references as targeted support selected by the router and the task risk.

- L1 changes: do not read references unless the task touches security, data, auth, external integration, performance, release, or irreversible behavior.
- L2 changes: read `references/capabilities/index.md` and only capability files explicitly selected by `change-forge-router`.
- L3 changes: read all selected capability references and `references/checklist.md` when present.
- L4/L5 changes: read all selected capability references, `references/checklist.md` when present, and domain extension references when selected.
- Selected capability reference path format: `references/capabilities/<capability-id>-<capability-name>.md`.

Examples:
- `42 idempotency-retry-design` -> `references/capabilities/42-idempotency-retry-design.md`
- `82 solution-optimality-evaluation` -> `references/capabilities/82-solution-optimality-evaluation.md`

## Output Contract
Return this exact structure:

```markdown
# ChangeForge Routing Result

## 1. Request Classification
- Change type:
- Complexity:
- Risk level:
- Execution mode:
- Product area:
- Code area:
- Domain extension signals:

## 2. Interpreted Change
- Current behavior:
- Desired behavior:
- User value:
- Constraints:
- Non-goals:

## 3. Missing Information
- Blocking:
- Non-blocking:
- Assumptions:

## 4. Impact Areas
- Product behavior:
- UX:
- Domain:
- API:
- Data:
- Frontend:
- Backend:
- Integration:
- Security:
- Testing:
- Reliability:
- Delivery:
- Documentation:

## 5. Professional Skill Path
| Order | Skill | Why | Input | Output |
| --- | --- | --- | --- | --- |

## 6. Foundation Capabilities
| Capability ID | Capability | Why | Used By | Expected Output |
| --- | --- | --- | --- | --- |

## 7. Domain Extensions
| Extension | Why | Risks | Required Outputs |
| --- | --- | --- | --- |

## 8. Required References
| Skill | Reference | Why | Required/Optional |
| --- | --- | --- | --- |

## 9. Task DAG
Each task:
- id
- name
- skill
- capabilities
- depends_on
- files_or_artifacts
- acceptance
- rollback_note

## 10. Quality Gates
- requirement gate
- impact gate
- domain gate
- architecture gate
- API/data gate
- implementation gate
- security gate
- test gate
- reliability gate
- delivery gate
- documentation gate
- AI review gate

## 11. Next Actions
- next skill calls
- blocked/unblocked status
- recommended execution mode
```

Use `None` when a domain extension is not selected. Use `Skipped: reason` for quality gates that are not needed. Use concrete assumptions rather than silent gaps.

Populate Required References for router self-use and for every selected support reference:

- Always include router self-use references: `references/routing-rules.md`, `references/skill-registry.md`, `references/capability-index.md`, and `references/domain-extension-index.md`.
- Whenever foundation capabilities are selected, list selected capability files under `references/capabilities/` for each selected professional skill.
- For L3 and higher changes, include `references/checklist.md` when present.
- For L4/L5 changes with a selected domain extension, include the selected domain extension `SKILL.md` and any selected domain extension reference.

## Quality Gate
The route passes only when:

- Every selected professional skill has a clear reason, input, and expected output.
- Every selected foundation capability is tied to a selected professional skill.
- Every selected domain extension has a domain signal, risk, and required output.
- Required References lists router self-use references and every selected capability, checklist, or domain extension reference required by the route.
- Every impacted area has a selected skill, a quality gate, a non-blocking assumption, or an explicit skip reason.
- Complexity and risk match the escalation triggers.
- The task DAG is acyclic, reviewable, acceptance-linked, and rollback-aware.
- The route does not rely on undeclared asset ingestion, external knowledge stores, or undeclared runtime content.

## Handoff
Hand off to the first unblocked skill in the professional path. Preserve request classification, interpreted change, missing information, impact areas, selected capabilities, domain extension requirements, required references, task DAG, quality gates, and recommended execution mode.

If blocked, hand off only to the skill that can remove the block. If unblocked, hand off to the next implementation, gate, or documentation skill according to the minimum sufficient path.

## Completion Criteria
The routing result is complete when an implementing agent can start the next skill with clear scope, risk, dependencies, selected capabilities, required references, quality gates, validation expectations, and rollback notes without guessing which ChangeForge path applies or which references to read.
