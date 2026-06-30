---
name: ai-code-review-refactor
description: Reviews AI-generated or heavily assisted code for hallucinated APIs, hidden assumptions, over-abstraction, duplicated code, missing tests, architecture drift, dependency pollution, type safety, maintainability, and safe refactor boundaries.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---

# AI Code Review Refactor

## Mission
Critically review, validate, and safely refactor AI-generated or AI-assisted code so it references real APIs, respects local architecture conventions, maintains testability, avoids dependency bloat, and stays within safe behavioral change boundaries — because LLM-generated code optimizes for plausibility, not correctness.

## Stage Ownership
Own cross-stage review for PDD/DDD/SDD/TDD traces: verify that problem definition, domain ownership, system design, logging decisions, tests, and validation evidence align with the actual diff. Reject boolean-only traceability and require concrete mappings when process evidence is claimed.

## When To Use
- Code was generated, completed, or significantly transformed by an AI model (Copilot, Claude, ChatGPT, Cursor, etc.).
- Abstractions feel invented, over-engineered, or inconsistent with the existing codebase style.
- Imports, APIs, or library calls are unfamiliar and need existence verification.
- A refactor was AI-suggested and its behavioral boundaries are unclear.
- Dependency additions came from AI output without explicit justification.
- Tests exist only for the AI-generated happy path and don't cover the original behavior.
- An agent claims an AI-generated change is complete without evidence, verified API checks, reuse search, or validation output.

## Do Not Use When
- Code was written entirely by a human with normal review discipline and no AI generation is involved.
- The review is a pure style pass unconnected to behavioral correctness, tests, or architecture.
- The change is read-only documentation with no code execution path.

## Non-Negotiable Rules
- **Direct use still runs the runtime prompt flow.** When `ai-code-review-refactor` is invoked directly and router reclassification is skipped, target-project engineering work must still clarify requirements before action, inspect relevant code/tests/config/docs before planning, name a TDD or validation signal before implementation, map each action to an owner skill and a different review skill, repair and re-review findings, and hand off with validation evidence, residual risk, and route/stage manifests when routed.
- **Independent review starts from the spec and plan**: a review cannot approve generated code until it has inspected the requirement, acceptance criteria, non-goals, accepted plan, changed files, tests, validation output, and repository context. Code quality is reviewed only after spec compliance passes.
- **Approval scope is explicit**: every approval names the exact files, behavior, tests, and validation it covers and what it does not cover. Implementer self-approval is not independent review.
- **Repair requires targeted re-review**: any fix after a review finding must identify the finding, repair owner, changed files, validation evidence, and the specific review stage that was re-run.
- Verify every import and API call exists in the declared version — AI models hallucinate method names and parameter signatures with high confidence.
- Challenge every hidden assumption: if a function assumes a non-null argument, a sorted collection, or a singleton pattern, require explicit documentation or enforcement.
- Prefer existing local patterns over novel AI-invented abstractions — pattern novelty is a risk signal, not a quality signal.
- Require tests for every behavior-changing refactor and every new code path, not just the happy path.
- Reject dependency additions that come without explicit justification, audit, and security review.
- Every refactor must have a clearly bounded scope — changes that silently alter observable behavior must be surfaced and reviewed separately.
- AI-generated code that adds any function, class, file, directory, component, hook, service, repository, adapter, utility, abstraction, or dependency must include an Implementation Structure Plan before acceptance.
- AI-generated completion claims must include an Execution Discipline Report: evidence inventory, same-pattern scan when a local fix is present, reuse-and-placement rationale for new structure, and closure boundary.
- Flag AI-generated error handling that swallows exceptions, returns `null`/`nil`/`undefined` silently, or ignores response status codes.
- Security-sensitive paths (auth, permissions, payment, data access) cannot be accepted from AI output without adversarial review.
- Type annotations from AI must be verified against the actual runtime types — AI generates plausible signatures, not necessarily correct ones.
- Generated code that introduces `any`, `Object`, or untyped assertions in strongly-typed codebases must be explicitly justified.
- Run a complexity-only review lane when AI-generated code may be bloated: use `delete`, `stdlib`, `native`, `existing-code`, `yagni`, and `shrink` tags from `minimal-correct-implementation`; this lane supplements normal correctness, security, dependency, architecture, and test review.
- Reject any AI-generated file addition without same-directory and parent-module file naming evidence.
- Reject any AI-generated helper/utility/common/shared code without a reuse ladder record.
- Reject duplicated logic when existing code could be reused, extended, composed, wrapped, or extracted.
- Reject extension of existing functions/classes/methods/services without old-behavior preservation evidence.
- Reject object/class/interface/inheritance/reflection structure without an advanced refactoring structure decision.
- AI-generated comments are suspect. Reject comments that restate code, invent intent, describe only the happy path, hide uncertainty, or become stale immediately. Require comments only where they document contract, invariant, edge case, non-obvious decision, test scenario, or public API behavior.
- Reject AI-generated helper bags, factories, strategies, registries, or interfaces that do not match current variation, state, invariant, lifecycle, or collaborator boundaries.
- Reject AI-generated code that piles validation, business decisions, I/O, persistence, events, logging, mapping, and fallback in one function without an explicit orchestration boundary.
- Reject AI-generated shared/common/utils additions that contain business vocabulary, business fixtures, permission rules, order/payment/tenant logic, or module-specific assumptions.
- Reject AI-generated compatibility branches, deprecated API use, TODO cleanup, and feature flags without owner, expiry, and removal plan.
- Reject generated code that only adds new abstractions or branches while leaving obsolete code, duplicate logic, or old paths in place without a cleanup assessment.

## Industry Benchmarks
- **OWASP Code Review Guide**: Security-focused code review checklist — injection points, auth bypass, insecure defaults, input handling.
- **Google Engineering Practices**: Code review focus on correctness, complexity, tests, naming, comments, style. AI code frequently fails the complexity and tests criteria.
- **NIST SSDF (SP 800-218)**: Secure software development framework — verify third-party components, check for known vulnerabilities.
- **CWE Top 25**: Most dangerous software weaknesses — AI-generated code disproportionately risks CWE-20 (Improper Input Validation), CWE-22 (Path Traversal), CWE-798 (Hardcoded Credentials).
- **SemVer Compatibility**: Any API or library used must be verified against the project's declared dependency versions — AI mixes version APIs.
- **Test Adequacy (Mutation Testing)**: Generated tests that only call mocks without behavioral assertions provide zero real coverage.
- **Dependency Audit (npm audit, pip audit, OWASP Dependency-Check)**: Every AI-added dependency must pass automated vulnerability scan and license check.

### Risk Classification Matrix

| AI Output Category | Risk Level | Required Review Action |
|---|---|---|
| New external dependency | Critical | Existence, CVE scan, license, transitive deps |
| Security/auth code | Critical | Adversarial review, threat model check |
| Data mutation / migration | High | Behavioral boundary audit, rollback review |
| Error handling | High | Exception path coverage, silent failure check |
| New abstraction layer | Medium | Justify vs. existing patterns, coupling check |
| Refactored logic | Medium | Behavioral equivalence check, before/after test |
| Test code | Medium | Mock-only vs real assertion audit |
| Style / formatting | Low | Standard review sufficient |

## Technical Selection Criteria
Evaluate AI-generated code across these dimensions:
- **API existence**: Every method, property, and module exists in the declared version.
- **Assumption inventory**: Every implicit assumption (non-null, ordered, single-instance, idempotent) is documented or enforced.
- **Code element review**: Generated variables, expressions, and statements are checked for uninitialized reads, shadowing, mutable/default sentinel bugs, nullish/truthiness drift, hidden assignments, magic constants, no-op statements, fallthrough, broad try scope, missing cleanup, and event-before-commit ordering.
- **Pattern consistency**: Abstractions match local naming, structure, error handling, and DI conventions.
- **Implementation structure**: Existing reusable functions/classes/modules inspected; placement rationale for every new function/class/file/directory; shared/common/utils audit; dependency direction check.
- **Duplication**: AI tends to generate complete self-contained functions that duplicate existing utility functions — cross-reference before accepting.
- **Abstraction pressure**: Is a new interface, factory, or strategy justified by current use cases or is it speculative extensibility?
- **Dependency vetting**: Each added package has a clear purpose, acceptable CVE posture, compatible license, and minimal transitive footprint.
- **Type safety**: All type annotations are verified against runtime behavior, not accepted on syntactic plausibility.
- **Error path coverage**: Every failure mode (upstream error, invalid input, timeout, empty result) has an explicit code path and test.
- **Refactor boundary**: The changed code's observable behavior is identical to the original — diff is structurally equivalent, not just approximately similar.
- **Test quality**: Tests assert real behavioral outcomes, not implementation structure — mock-only tests pass even when the production logic is broken.
- **Clarity and cleanup**: Main flow remains readable; generated helpers are not stateless bags; I/O and decisions are separated; obsolete code, feature flags, and deprecated branches have a deletion path.

## Mode Matrix
Select the AI review/refactor mode before approving or changing generated code. Review findings must be severity-classified before remediation.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
|---|---|---|---|---|---|
| AI generated code review | Generated diff, helper, class, dependency, tests, or broad patch. | Hallucinated APIs, hidden assumptions, code-element defects, reuse/placement, tests, validation evidence. | API existence search, local-pattern scan, element-risk pass, command output, severity findings. | `code-review`, `agent-execution-discipline`, `implementation-structure-design`, `code-element-professionalism` | Refactor before findings are classified. |
| Behavior-preserving refactor | AI proposes move/extract/split/cleanup or reviewer requests cleanup. | Preserve behavior, public contract, errors, side effects, and tests. | Characterization/regression tests, before/after behavior, affected callers. | `refactoring`, `code-clarity-maintainability`, `quality-test-gate` | New behavior in same refactor. |
| Bug-fix review | AI patch fixes one failure, lint error, test failure, or incident symptom. | Verify cause, same-pattern scan, local/broad fix boundary, regression proof. | Cause, pattern searched, related occurrences, failing/passing test. | `failure-diagnosis`, `regression-testing`, `agent-execution-discipline` | "Looks plausible" approval. |
| Structure/reuse audit | New abstraction, helper, utility, shared component, file, directory, dependency. | Reject invented helpers, duplicate logic, wrong placement, speculative abstraction. | Reuse ladder, owner, dependency direction, deletion path. | `implementation-structure-design`, `architecture-impact-reviewer` when boundaries move | Shared/common placement without proof. |
| Complexity-only review | Bloat, overengineering, wrapper-only delegation, unnecessary dependency, one-implementation abstraction, scaffold-for-later, or delete/shrink request. | Produce complexity tags without replacing normal AI review. | Tagged findings, simpler alternative, retained-risk decision, validation required. | `minimal-correct-implementation`, `code-clarity-maintainability`, `cleanup-deletion-governance` | Treating line count as the approval standard. |
| Test/refactor quality review | Generated tests, fixtures, mocks, snapshots, golden files, or cleanup. | Behavior assertions, fixture ownership, no over-mocking private internals. | What tests prove/do not prove, mock contract, fixture owner. | `quality-test-gate`, `code-clarity-maintainability` | Mock-call-only approval. |
| Security/performance-sensitive AI code | Generated auth, SQL, migration, secret, integration, retry, concurrency, or hot path. | Adversarial review, measured risk, no silent fallback or speculative optimization. | Security scan/tests, profile/benchmark, rollback/contract proof. | `security-privacy-gate`, `reliability-observability-gate`, `data-middleware-change-builder` | Trusting AI comments as proof. |
| Business semantic review | Generated diff, refactor, SQL/controller/mapper/DTO, stale memory, or golden case may change business meaning. | Detect changed, hidden, stale, rejected, or untested business semantics. | BSP diff, source-backed facts, rule/workflow map, memory/graph selector limits, golden case evidence. | `business-semantic-control-plane`, `domain-impact-modeler`, `quality-test-gate` | Approving from clean structure alone. |

## Proactive Professional Triggers

- **Signal:** generated code calls an API, method, enum, parameter, import, CLI flag, or provider feature not found in local code/docs/version. **Hidden risk:** hallucinated API. **Required professional action:** verify symbol existence before quality approval. **Route to:** `code-review`, `language-runtime-selection`, `language-idiom-enforcement`. **Evidence required:** search/typecheck/build output.
- **Signal:** AI adds helper/utility/common/shared abstraction before reuse search. **Hidden risk:** duplicated logic, helper-bag pollution, and wrong placement. **Required professional action:** require reuse ladder, owner boundary, and rejected-alternative rationale. **Route to:** `implementation-structure-design`. **Evidence required:** reuse-search output, reuse candidates, rejected alternatives, owner, and placement rationale.
- **Signal:** generated refactor changes errors, edge cases, ordering, transactions, async timing, or public contract while claiming cleanup. **Hidden risk:** hidden behavior change. **Required professional action:** require characterization/regression evidence. **Route to:** `refactoring`, `quality-test-gate`. **Evidence required:** before/after tests and affected callers.
- **Signal:** generated tests assert mock calls, CSS/classes, or private helpers without public behavior. **Hidden risk:** false confidence. **Required professional action:** rewrite tests by behavior and state what they prove. **Route to:** `quality-test-gate`, `code-clarity-maintainability`. **Evidence required:** behavior assertion, fixture/mocking boundary.
- **Signal:** AI exports private helpers, adds test-only public APIs, or over-mocks internals to make tests pass. **Hidden risk:** encapsulation loss and implementation-shaped tests. **Required professional action:** require a testability seam plan. **Route to:** `testability-seam-design`, `quality-test-gate`. **Evidence required:** public behavior boundary, seam map, test double decision, and private-helper non-export decision.
- **Signal:** AI uses API DTOs as domain objects, returns ORM/persistence models from APIs, leaks generated SDK models, or puts business decisions in mapper code. **Hidden risk:** plausible model code couples API, persistence, generated, and domain boundaries. **Required professional action:** require model boundary mapping. **Route to:** `model-boundary-mapping`, `data-api-contract-changer`. **Evidence required:** source/target map, validation owner, null/default semantics, generated boundary, and mapping tests.
- **Signal:** AI adds clients, pools, service locators, globals, singletons, timers, subscriptions, or dependency injection wiring without lifecycle ownership. **Hidden risk:** resource leak, hidden graph, or circular dependency. **Required professional action:** review dependency wiring and lifecycle. **Route to:** `dependency-wiring-lifecycle`, `reliability-observability-gate`. **Evidence required:** composition root, lifecycle scope, construction/shutdown owner, and cycle check.
- **Signal:** AI uses nested scans, load-all, full sort, unbounded grouping, or mismatched data structures on non-trivial input. **Hidden risk:** wrong complexity, memory loss, or stale performance assumptions in code that appears to work. **Required professional action:** require algorithm/data-structure decision evidence before approval. **Route to:** `algorithm-data-structure-selection`, `solution-optimality-evaluation`. **Evidence required:** input size, complexity, memory budget, rejected alternatives, and benchmark/profile report.
- **Signal:** AI hides writes, cache mutations, events, external IO, logging, metrics, time, random, or env reads inside mappers, getters, policies, or domain objects. **Hidden risk:** side-effect opacity and wrong transaction ordering. **Required professional action:** trace side-effect flow. **Route to:** `data-side-effect-flow-tracing`, `implementation-structure-design`. **Evidence required:** flow map, ordering, transaction/cache/event boundary, and tests.
- **Signal:** AI-generated code uses uninitialized or shadowed variables, mutable defaults, null/default sentinels, `||`/truthiness for missing values, nested ternaries, hidden assignment in conditions, magic constants, empty loops/catches, switch fallthrough, broad try scope, missing cleanup, or event-before-commit statements. **Hidden risk:** local code elements look idiomatic but can cause wrong edge-case behavior, missing cleanup, permission leak, or inconsistent transaction order. **Required professional action:** verify and route code-element findings before approval. **Route to:** `code-element-professionalism`, `quality-test-gate`, `language-idiom-enforcement`. **Evidence required:** element finding, language-specific test or typecheck command output, static-analysis report when available, and residual risk.
- **Signal:** AI adds feature flags, mode/kind switches, deprecated branches, fallbacks, or compatibility code without owner, expiry, or deletion path. **Hidden risk:** permanent config strategy drift and cleanup debt. **Required professional action:** require runtime policy and cleanup governance. **Route to:** `configuration-runtime-policy`, `cleanup-deletion-governance`. **Evidence required:** owner, default, validation, expiry, telemetry, cleanup issue, and rollback.
- **Signal:** AI changes public API, SDK, schema, event payload, generated client, or package export without consumer inventory or migration plan. **Hidden risk:** generated code appears internally consistent while downstream consumers break. **Required professional action:** require consumer impact analysis. **Route to:** `consumer-impact-analysis`, `version-compatibility`. **Evidence required:** changed contract, consumer list, generated-client impact, compatibility, deprecation/migration, telemetry, and rollback.
- **Signal:** AI introduces or bypasses module, import, export, generated-code, dead-code, complexity, or forbidden-dependency rules with no automated check. **Hidden risk:** hidden dependency leaks and wrong module boundaries are approved because the generated diff looks plausible. **Required professional action:** require enforceable architecture tooling or a staged baseline. **Route to:** `architecture-enforcement-tooling`, `architecture-impact-reviewer`. **Evidence required:** rule list, tool choice, CI command, failure example, exception policy, and owner.
- **Signal:** AI adds dependency for simple parsing, date, utility, crypto, HTTP, or formatting task without scan/license/CVE. **Hidden risk:** dependency pollution and supply-chain risk. **Required professional action:** evaluate stdlib/local alternative. **Route to:** `package-dependency-management`, `security-privacy-gate`. **Evidence required:** CVE/license/size and alternative.
- **Signal:** AI adds one-implementation abstraction, wrapper-only delegation, scaffold-for-later, unused config, or custom code where stdlib/native/existing code likely applies.
  **Hidden risk:** duplicate wrapper, unused config, or custom parser/formatter hides generated behavior change and leaves unverified maintenance surface for future caller edits.
  **Required professional action:** require reviewer to classify delete/shrink/reuse findings, scan current callers, and verify retained structure before approval.
  **Route to:** `minimal-correct-implementation`, `code-clarity-maintainability`, `cleanup-deletion-governance`.
  **Evidence required:** `delete` / `stdlib` / `native` / `existing-code` / `yagni` / `shrink` finding, current-caller scan, validation command output, or explicit no-finding rationale.
- **Signal:** generated code catches and suppresses errors or returns default/null fallback. **Hidden risk:** silent failure. **Required professional action:** require typed error/log/metric or safe fallback rationale. **Route to:** `logging-error-handling`, `reliability-observability-gate`. **Evidence required:** negative test and observability.
- **Signal:** AI expands scope from local fix to broad refactor, new abstraction, dependency, or architecture change without boundary statement. **Hidden risk:** unbounded scope means review cannot prove behavior preservation. **Required professional action:** split the change or document scope, unchanged boundaries, and evidence. **Route to:** `agent-execution-discipline`, `change-impact-analyzer`. **Evidence required:** boundary statement, changed/unchanged file list, validation command output, and residual risk owner.
- **Signal:** completion claim lacks command output or uses stale validation from before generated changes. **Hidden risk:** unverified AI code. **Required professional action:** block approval until fresh evidence or not-verified disclosure. **Route to:** `agent-execution-discipline`. **Evidence required:** command, exit code, outcome, residual risk.
- **Signal:** review approves AI code without the requirement, accepted plan, final diff, test evidence, or validation freshness. **Hidden risk:** clean-looking code can miss the requested behavior or approve stale proof. **Required professional action:** run spec-compliance review first, then code-quality review with approval scope. **Route to:** `plan-execution-consistency`, `quality-test-gate`. **Evidence required:** requirement/plan match, final diff covered, changed-code-to-test map, validation freshness, and explicit approval limits.
- **Signal:** review inspects only the final diff while runtime trajectory, project memory, or repository context pack shows edit-before-read, repeated failure, fragile file, stale context, or skipped validation. **Hidden risk:** the final diff can look clean while process evidence shows unreviewed repair or stale assumptions. **Required professional action:** read the trajectory, memory projection, and context pack as review inputs, then verify current source evidence. **Route to:** `execution-trajectory-analysis`, `project-memory-governance`, `repository-graph-analysis`. **Evidence required:** trajectory findings, memory limits, context-pack freshness, final diff scope, and current-source confirmation.
- **Signal:** an implementer claims their own generated patch is reviewed or a repair closes without re-review. **Hidden risk:** review findings are silently bypassed. **Required professional action:** require independent review or targeted re-review after repair. **Route to:** `code-review`, `agent-workflow-state-machine`. **Evidence required:** reviewer skill/capability, finding ID, repair diff, validation, and re-review result.

### Decision Tree: Accept or Return for Remediation

```
Does the code reference external APIs or libraries?
├── Yes → Verify all APIs exist in declared version
│   └── Unverified → Return with hallucinated API list
Does it add new dependencies?
├── Yes → CVE scan + license check required
│   └── Fails → Block until dependency is replaced or audited
Does it touch auth, permissions, payments, or data access?
├── Yes → Adversarial security review required
│   └── Fails → Escalate to security-privacy-gate
Does it introduce new abstractions?
├── Yes → Justify against existing patterns
│   └── Unjustified → Propose collapse to existing pattern
Does it refactor existing logic?
├── Yes → Behavioral equivalence + test coverage required
│   └── Missing → Request before/after behavioral test
All checks pass → Approve with evidence
```

## Two-Stage Review

Review in order: spec compliance first, code quality second. Good code that does not meet the requirement is still a failed change.

- **Stage 1 — Spec Compliance Review.** Confirm the change meets the requirement, the acceptance criteria, and the non-goals; matches the plan task; preserves API/schema compatibility; and preserves old behavior that must not change. If Stage 1 fails, return the change for spec remediation and do not record a code-quality approval — "the code is clean" never offsets a missing requirement.
- **Stage 2 — Code Quality Review.** Only after Stage 1 passes, review structure, naming, reuse, test quality, performance, security, and maintainability.

Forbidden: entering quality approval before spec compliance passes; letting a clean diff mask a missing requirement; reviewing the diff without the requirement and plan; and accepting an implementer's self-review in place of an independent review.

For L4/L5 changes and large refactors, run a Review Loop: a Stage 1 spec issue is fixed and spec-re-reviewed; a Stage 2 quality issue is fixed and quality-re-reviewed; no open issue from either stage may carry into the next task. When the runtime supports a separate reviewer, prefer a fresh reviewer; when it does not, the same agent must perform the stages explicitly and in order rather than assume a subagent exists.

## Solution Optimality Self-Check
Apply when reviewing AI-generated code that makes algorithmic choices, introduces data structures, changes concurrency models, or claims performance gains. Answer the **Three-Challenge Rule**: (1) why did the model choose this approach (AI optimizes for plausibility, not optimality), (2) is there a simpler sufficient implementation (AI over-engineers), (3) what is the strongest alternative and why is the AI's choice preferred. Verify complexity class, bounded memory/caches, I/O-call count, concurrency safety, and cognitive complexity on every non-trivial path.

Load [references/solution-optimality.md](references/solution-optimality.md) for the full algorithm/performance review matrix and the AI-specific optimality anti-patterns to reject when the change touches a performance-sensitive path. Method compiled from `solution-optimality-evaluation`.

## Risk Escalation Rules
- Escalate to `security-privacy-gate` when AI code touches authentication, authorization, session handling, or credential management.
- Escalate to `data-api-contract-changer` when a refactor silently alters API response shapes, error codes, or contract semantics.
- Escalate to `architecture-impact-reviewer` when AI introduces a new service boundary, shared abstraction, or cross-module dependency.
- Escalate to `data-middleware-change-builder` when a generated migration script, ORM query, or schema change is involved.
- Escalate when AI has added or upgraded a dependency with known CVEs, GPL/AGPL license conflict, or broad transitive attack surface.
- Escalate when the refactor is large enough that behavioral equivalence cannot be established without running the full integration test suite.
- Escalate to `agent-execution-discipline` when the agent cannot produce evidence for completion, repeats the same failed route twice, or proposes a local fix without a same-pattern scan.
- Escalate to `code-element-professionalism` for generated local defaults, shadowing, hidden expression side effects, no-op statements, cleanup gaps, fallthrough, or event-before-commit ordering.

## Critical Details
- Verify syntactically plausible APIs against declared versions; hallucinations include missing method chains, wrong optional parameters, deprecated signatures, and invented enum values.
- Treat AI refactors as happy-path equivalent until tests prove edge, error, ordering, and concurrency behavior.
- Treat generated tests and comments as suspect when they only prove mocks or happy-path intent.
- Challenge generated abstractions, globals, singletons, helpers, factories, strategies, and dependency additions against local patterns and standard-library alternatives.
- Test AI-generated security checks adversarially with invalid tokens, expired credentials, null inputs, injection strings, tenant mismatches, and role hierarchy edges.

Pattern catalog: load `references/ai-review-pattern-catalog.md` when examples are needed to calibrate hallucinated APIs, silent failure, helper bags, side-effect pollution, mock-only tests, feature-flag debt, dependency pollution, or other recurring AI-generated failure modes.

## Failure Modes
- **Hallucinated APIs** compile or typecheck incompletely, then fail at runtime because the symbol, signature, enum, or provider feature never existed in the declared version.
- **Mock-only tests** and happy-path fixtures approve code that breaks real outputs, side effects, error paths, permissions, or concurrency.
- **Over-abstraction and helper bags** create public APIs, factories, strategies, wrappers, or shared utilities without current variation, owner, or deletion path.
- **Silent failure and side-effect pollution** hide swallowed errors, fallback defaults, database writes, events, cache mutation, or external IO in the wrong layer.
- **Security, migration, dependency, and cleanup debt** ship when AI-added checks, destructive DDL, packages, feature flags, compatibility branches, or TODO paths lack adversarial review, rollback, audit, owner, and expiry.
- **Spec-missing approval** accepts clean-looking generated code that never satisfies the original requirement, non-goal, or compatibility promise.
- **Stale validation approval** reuses a typecheck, test, or scan from before the generated repair and treats it as current evidence.
- **Self-review bypass** lets the implementer mark their own generated patch as reviewed without independent findings, repair evidence, and re-review.

## Reference Loading Policy
Do not load every reference by default. Treat references as targeted support selected by the router and the task risk.

- L1 changes: do not read references unless the task touches security, data, auth, external integration, performance, release, or irreversible behavior.
- L2 changes: read `references/capabilities/index.md` and only capability files explicitly selected by `change-forge-router`.
- L3 changes: read all selected capability references and `references/checklist.md` when present.
- L4/L5 changes: read all selected capability references, `references/checklist.md` when present, and domain extension references when selected.
- Selected capability reference path format: `references/capabilities/<capability-id>-<capability-name>.md`.

## Output Contract
Return a structured review with severity-classified findings first:
- **Mode selected:** generated review, behavior-preserving refactor, bug-fix review, structure/reuse audit, test quality review, or security/performance-sensitive AI code, with trigger.
- **Findings:** Critical/High/Medium/Low issues with file/line, impact, evidence, and required action.
- **Boundaries inspected:** requirements, plan, changed files, call sites, public contracts, reuse candidates, tests, dependencies, and security/performance surfaces.
- **API and dependency evidence:** verified API inventory, hallucinated/unverified symbols, dependency audit, CVE/license posture, and stdlib/local alternatives.
- **Structure review:** reuse ladder, placement rationale, naming evidence, owner boundary, dependency direction, and rejected alternatives.
- **Behavior preservation:** refactor scope, equivalence evidence, changed-code-to-test map, old/new behavior tests, and compatibility risk.
- **Business semantic review:** changed/hidden/rejected/stale business rules, workflow transitions, owner decisions, memory/graph selector limits, golden case gaps, and BSP residual risk when selected.
- **Approval decision:** approved, returned, split, blocked, or refactor-required, with approval scope and re-review requirement.
- **Validation evidence:** fresh commands, outputs, what evidence proves, what evidence does not prove, residual risk, and next gate.

## Business Semantic Review

When BSP is selected or a business semantic trigger appears in the diff, review must check:

- silent business rule changes hidden behind refactors, helper moves, SQL filters, fixture updates, or mapper/default changes
- wrong authoritative enforcement layer, including controller-only, UI-only, SQL-only, test-only, and support-tool-only rules
- DTO, table, resource, generated model, or read model used as the domain object without mapping owner and compatibility evidence
- hidden SQL/controller/UI/test-only rule that lacks rule id, owner, entry points, enforcement path, and validation map
- missing entry-point coverage across UI, public API, internal API, jobs, imports, admin, replay, migration, and support paths
- workflow state drift, new statuses, changed allowed transitions, or missing forbidden transition tests
- project memory or repository graph used as source truth instead of selector evidence
- missing business golden cases for changed rules, workflow transitions, reason codes, and negative paths
- BSP-vs-actual-diff inconsistency, including a BSP claim not supported by the changed files or a changed semantic not represented in BSP

Return findings rather than approval when any check lacks source-backed evidence, owner review, validation evidence, or explicit residual risk.

For the full enumerated output fields, quality gate list, and handoff routing table, load `references/review-output-and-gates.md`.

## Evidence Contract
Close an AI-code review or refactor only when the canonical answers from `agent-execution-discipline` are concrete.
- **Basis:** selected mode, standard, requirement, repository pattern, or real API; cited symbols/signatures are verified.
- **Files and boundaries inspected:** requirements, acceptance, non-goals, same-pattern scan, call sites, public contracts, tests, dependencies, and security/performance surfaces.
- **Reuse / placement rationale:** every added or moved element has reuse-versus-new rationale, owner boundary, dependency direction, and rejected alternatives.
- **Validation evidence:** hallucinated-API checks, typecheck/build, characterization/regression tests, security/performance checks, and generated-test review name outcomes and limits.
- **What evidence proves / what evidence does not prove:** state the covered behavior, uncovered edge cases, stale evidence, and limits of API searches, typechecks, tests, scans, or review.
- **Judgment, residual risk, and next gate:** accept/return/refactor decision, approval scope, behavior preservation, re-review or next gate, and named owner for remaining risk.

## Quality Gate
- APIs and dependency versions are verified; new dependencies have CVE/license/stdlib alternative evidence.
- Security-sensitive code is adversarially reviewed or escalated.
- Behavior-changing refactors have equivalence evidence and tests for real outcomes, not only mock calls.
- Hidden assumptions, runtime types, error paths, and fallback behavior are documented, enforced, or returned.
- Generated variable, expression, and statement hazards are explicitly checked or returned as findings.
- New structures have reuse ladder, placement rationale, naming evidence, owner boundary, dependency direction, and local-pattern comparison.
- Shared/common/utils additions do not contain business rules, fixtures, permission logic, tenant/payment/order assumptions, or module-specific behavior.
- Generated comments, docs, feature flags, compatibility branches, TODOs, deprecated APIs, and cleanup paths have owner, expiry, and removal evidence.
- Business semantic changes have source-backed facts, rule/workflow validation, golden cases or owner review, and no memory/graph-as-fact approval.
- BSP and actual diff agree on changed business rules, objects, workflows, entry points, evidence classes, and validation obligations; inconsistencies are findings.
- Findings are severity-classified; completion or approval claims require fresh validation evidence, scope, limits, and repair/re-review status.

## Handoff
- Escalate security/auth/payment/sensitive data to `security-privacy-gate`.
- Escalate new boundaries, shared abstractions, contract changes, or consumer impact to `architecture-impact-reviewer`, `data-api-contract-changer`, `consumer-impact-analysis`, or `architecture-enforcement-tooling`.
- Escalate test gaps, private-helper exposure, generated test weakness, or deterministic seam gaps to `quality-test-gate` or `testability-seam-design`.
- Escalate hidden side effects, lifecycle, config, cleanup, failure-contract, model-boundary, or algorithm choices to the matching capability owner.
- Escalate local variable, expression, statement, default, cleanup, and fallthrough hazards to `code-element-professionalism`.
- Escalate evidence gaps, repeated failures, missing same-pattern scan, or closure gaps to `agent-execution-discipline`.

## Completion Criteria
AI-generated or AI-assisted code is either accepted with documented evidence of API correctness, behavioral equivalence, dependency safety, test coverage, and security review — or returned with a numbered, actionable remediation list that can be resolved without ambiguity.
