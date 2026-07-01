# Routing Signals

Load this reference when a route has broad, hidden-risk, skill-authoring, runtime, language, or domain-specific signals. Keep the main router body focused on classification, protocol, output, and quality gates.

## Contents

- Foundation Capability Groups
- Signal Routing
- Action-Specific Owner And Review Routing

## Foundation Capability Groups

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
- Engineering workflow: 76 `context-packaging`, 77 `task-dag-decomposition`, 78 `code-review`, 79 `refactoring`, 80 `documentation-generation`, 81 `failure-diagnosis`, 82 `solution-optimality-evaluation`, 101 `implementation-structure-design`, 102 `agent-execution-discipline`, 103 `skill-authoring-expert`, 104 `engineering-stage-professionalism`, 105 `code-clarity-maintainability`, 106 `design-pattern-selection`, 107 `testability-seam-design`, 108 `dependency-wiring-lifecycle`, 113 `data-side-effect-flow-tracing`, 116 `cleanup-deletion-governance`, 117 `minimal-correct-implementation`, 118 `repository-context-map`, 119 `agent-workflow-state-machine`, 120 `agent-tool-permission-sandbox`, 121 `skill-efficacy-benchmark`, 122 `plan-execution-consistency`, 127 `execution-trajectory-analysis`, 128 `context-control-plane`, 136 `senior-programming-judgment-core`.
- Agent runtime governance: 123 `executor-adapter-protocol`.
- Repository intelligence: 124 `repository-graph-analysis`.
- Project memory: 125 `project-memory-governance`.
- Quality validation brokerage: 126 `validation-broker`.
- Business intelligence: 135 `business-semantic-control-plane`.
- Targeted code correctness: 109 `algorithm-data-structure-selection`, 110 `failure-contract-design`, 111 `configuration-runtime-policy`, 112 `model-boundary-mapping`, 114 `architecture-enforcement-tooling`, 115 `consumer-impact-analysis`.
- Technology selection: 83 `technology-stack-selection`, 84 `language-runtime-selection`, 85 `language-idiom-enforcement`, 86 `language-testing-strategy`, 87 `language-performance-safety`, 88 `package-dependency-management`.
- Language professional usage: 89 `go-professional-usage`, 90 `java-jvm-professional-usage`, 91 `typescript-professional-usage`, 92 `python-professional-usage`, 93 `rust-professional-usage`, 94 `cpp-professional-usage`, 95 `shell-cli-professional-usage`, 96 `sql-professional-usage`.
- Interface, storage, and global correctness: 97 `sdk-library-contract-design`, 98 `cli-daemon-interface-design`, 99 `file-storage-processing`, 100 `i18n-timezone-money-safety`.

## Signal Routing

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
- If the request mentions context budget, token overhead, reference bloat, selected references, skipped references, JIT retrieval, graph-as-selector, tool-output boundary, artifact reference, compaction snapshot, branch summary, route repair summary, output truncation, live benchmark overhead, over-routing, or under-routing, select `context-control-plane` and emit a `context_control` record with budget and skipped-reference rationale.
- If the request mentions senior programming judgment, senior_programming_judgment, purpose/facts/objects/states/behaviors/rules/invariants/boundaries, failure contract, side effects, reuse and placement, minimality, validation map, observability map, residual risk, or a non-trivial engineering change with no explicit judgment evidence, select `senior-programming-judgment-core`. Keep it evidence-bound and pair it with specialist capabilities instead of using it as a persona, generic article, BSP replacement, or catch-all route.
- If the request mentions business semantic pack, business semantic control plane, business context missing, business vocabulary ambiguous, business object ownership unclear, business rule authority unknown, business workflow state unclear, business invariant changed, business rule hidden in SQL/controller/UI/test, DTO used as business object, business memory affects decision, business golden case missing, technical refactor may change business semantics, business semantic review required, graph used as business fact, or memory used as business fact, select `business-semantic-control-plane`; require source-backed `FACT` evidence, memory/graph selector limits, structured selected/skipped reference decisions, validation map or residual risk, and business semantic manifest fields. Keep legacy aliases such as business term ambiguous, rule authority unclear, hidden sql rule, hidden controller rule, and stale business memory for compatibility.
- If AI-generated implementation adds any function, class, file, directory, component, hook, service, repository, adapter, utility, abstraction, branch-heavy flow, or dependency, select `ai-code-review-refactor`, `implementation-structure-design`, `code-clarity-maintainability`, and `code-review`.
- If refactoring extracts, moves, splits, collapses, cleans up dead code, removes feature flags, removes deprecated APIs, or retires compatibility branches, select `refactoring`, `implementation-structure-design`, `code-clarity-maintainability`, and `code-review`.
- If the request mentions or implies file naming mismatch, inconsistent file naming, wrong filename format, duplicate code, poor reuse, failure to reuse existing functions, reuse existing function/class/module, extension reuse, extending existing logic without changing old behavior, extracting classes, object modeling, inheritance, reflection, advanced refactor, oversized file/class/function, unreadable main flow, deep nesting, boolean trap, weakly typed parameter bag, side-effect pollution, missing comments, doc comments, test comments, exported API comments, public API comments, useless comments, excessive comments, stale comments, or comment quality, select `implementation-structure-design`, `code-clarity-maintainability`, `agent-execution-discipline`, and `language-idiom-enforcement`; add `ai-code-review-refactor` when reviewing AI-generated code; add `refactoring` when behavior-preserving movement is required; add `quality-test-gate` when tests, fixtures, helpers, or test comments are affected; add `architecture-impact-reviewer` when module boundaries or dependency direction may change.
- If test helpers, fixtures, factories, mocks, or golden files are placed in shared/common test utilities, or tests call private helpers instead of public behavior, select `quality-test-gate`, `code-clarity-maintainability`, and `implementation-structure-design`.
- If the change is being executed by an AI or agent and has any non-trivial diagnosis, code-mutation, deployment, or handoff component, select `agent-execution-discipline` alongside the substantive skills so the execution carries evidence inventory, verified-cause statement, route-repair ledger after repeated failure, same-pattern scan record, reuse-and-placement rationale, and a proactive closure package.
- If an agent has retried the same approach twice without success, force a route change via `agent-execution-discipline` and route the substantive diagnosis to `failure-diagnosis`; do not permit a third same-path retry.
- If an agent proposes a local fix for a bug or defect, require `agent-execution-discipline` with a same-pattern scan record and route to `change-impact-analyzer` when the scan reveals occurrences in other modules.
- If an agent claims a change is complete or ready for handoff, require the `agent-execution-discipline` proactive closure package with boundary, validation results, residual risk, and handoff target regardless of which professional skills handled the substantive work.
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

## Action-Specific Owner And Review Routing

Select only rows that match the actual action; the owner and review skill must differ.

| Action type | Owner skill / capability | Typical review skill / capability |
| --- | --- | --- |
| Requirement clarification | `change-intake-compiler` with `requirement-clarification`, `requirement-structuring`, `non-goal-boundary-definition` | `acceptance-criteria-builder` or `quality-test-gate` |
| Acceptance / TDD | `acceptance-criteria-builder` with `acceptance-standard-definition`, `scenario-decomposition` | `quality-test-gate` |
| Impact analysis | `change-impact-analyzer` with `context-packaging` | `change-forge-router` or `quality-test-gate` |
| Planning | `task-dag-planner` with `task-dag-decomposition`, `engineering-stage-professionalism` | `change-impact-analyzer` or `quality-test-gate` |
| Senior programming judgment | Current action owner with `senior-programming-judgment-core` evidence attached | `quality-test-gate` or `ai-code-review-refactor` |
| Frontend implementation | `frontend-change-builder` | `quality-test-gate` or `ai-code-review-refactor` |
| Backend implementation | `backend-change-builder` | `quality-test-gate` or `ai-code-review-refactor` |
| API/data contract | `data-api-contract-changer` | `quality-test-gate` or `architecture-impact-reviewer` |
| Data middleware | `data-middleware-change-builder` | `reliability-observability-gate` or `quality-test-gate` |
| External integration | `integration-change-builder` | `security-privacy-gate`, `reliability-observability-gate`, or `quality-test-gate` |
| Security-sensitive work | relevant implementation owner | `security-privacy-gate` |
| Reliability/performance | relevant implementation owner or `reliability-observability-gate` | `reliability-observability-gate` or `quality-test-gate` |
| Documentation | `change-documentation-gate` | `change-forge-router` or `quality-test-gate` |
| Final handoff | `agent-execution-discipline` | `quality-test-gate` |
