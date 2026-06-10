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
| AI generated code review | Generated diff, helper, class, dependency, tests, or broad patch. | Hallucinated APIs, hidden assumptions, reuse/placement, tests, validation evidence. | API existence search, local-pattern scan, command output, severity findings. | `code-review`, `agent-execution-discipline`, `implementation-structure-design` | Refactor before findings are classified. |
| Behavior-preserving refactor | AI proposes move/extract/split/cleanup or reviewer requests cleanup. | Preserve behavior, public contract, errors, side effects, and tests. | Characterization/regression tests, before/after behavior, affected callers. | `refactoring`, `code-clarity-maintainability`, `quality-test-gate` | New behavior in same refactor. |
| Bug-fix review | AI patch fixes one failure, lint error, test failure, or incident symptom. | Verify cause, same-pattern scan, local/broad fix boundary, regression proof. | Cause, pattern searched, related occurrences, failing/passing test. | `failure-diagnosis`, `regression-testing`, `agent-execution-discipline` | "Looks plausible" approval. |
| Structure/reuse audit | New abstraction, helper, utility, shared component, file, directory, dependency. | Reject invented helpers, duplicate logic, wrong placement, speculative abstraction. | Reuse ladder, owner, dependency direction, deletion path. | `implementation-structure-design`, `architecture-impact-reviewer` when boundaries move | Shared/common placement without proof. |
| Test/refactor quality review | Generated tests, fixtures, mocks, snapshots, golden files, or cleanup. | Behavior assertions, fixture ownership, no over-mocking private internals. | What tests prove/do not prove, mock contract, fixture owner. | `quality-test-gate`, `code-clarity-maintainability` | Mock-call-only approval. |
| Security/performance-sensitive AI code | Generated auth, SQL, migration, secret, integration, retry, concurrency, or hot path. | Adversarial review, measured risk, no silent fallback or speculative optimization. | Security scan/tests, profile/benchmark, rollback/contract proof. | `security-privacy-gate`, `reliability-observability-gate`, `data-middleware-change-builder` | Trusting AI comments as proof. |

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
- **Signal:** AI adds feature flags, mode/kind switches, deprecated branches, fallbacks, or compatibility code without owner, expiry, or deletion path. **Hidden risk:** permanent config strategy drift and cleanup debt. **Required professional action:** require runtime policy and cleanup governance. **Route to:** `configuration-runtime-policy`, `cleanup-deletion-governance`. **Evidence required:** owner, default, validation, expiry, telemetry, cleanup issue, and rollback.
- **Signal:** AI changes public API, SDK, schema, event payload, generated client, or package export without consumer inventory or migration plan. **Hidden risk:** generated code appears internally consistent while downstream consumers break. **Required professional action:** require consumer impact analysis. **Route to:** `consumer-impact-analysis`, `version-compatibility`. **Evidence required:** changed contract, consumer list, generated-client impact, compatibility, deprecation/migration, telemetry, and rollback.
- **Signal:** AI introduces or bypasses module, import, export, generated-code, dead-code, complexity, or forbidden-dependency rules with no automated check. **Hidden risk:** hidden dependency leaks and wrong module boundaries are approved because the generated diff looks plausible. **Required professional action:** require enforceable architecture tooling or a staged baseline. **Route to:** `architecture-enforcement-tooling`, `architecture-impact-reviewer`. **Evidence required:** rule list, tool choice, CI command, failure example, exception policy, and owner.
- **Signal:** AI adds dependency for simple parsing, date, utility, crypto, HTTP, or formatting task without scan/license/CVE. **Hidden risk:** dependency pollution and supply-chain risk. **Required professional action:** evaluate stdlib/local alternative. **Route to:** `package-dependency-management`, `security-privacy-gate`. **Evidence required:** CVE/license/size and alternative.
- **Signal:** generated code catches and suppresses errors or returns default/null fallback. **Hidden risk:** silent failure. **Required professional action:** require typed error/log/metric or safe fallback rationale. **Route to:** `logging-error-handling`, `reliability-observability-gate`. **Evidence required:** negative test and observability.
- **Signal:** AI expands scope from local fix to broad refactor, new abstraction, dependency, or architecture change without boundary statement. **Hidden risk:** unbounded scope means review cannot prove behavior preservation. **Required professional action:** split the change or document scope, unchanged boundaries, and evidence. **Route to:** `agent-execution-discipline`, `change-impact-analyzer`. **Evidence required:** boundary statement, changed/unchanged file list, validation command output, and residual risk owner.
- **Signal:** completion claim lacks command output or uses stale validation from before generated changes. **Hidden risk:** unverified AI code. **Required professional action:** block approval until fresh evidence or not-verified disclosure. **Route to:** `agent-execution-discipline`. **Evidence required:** command, exit code, outcome, residual risk.

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

## Critical Details
- AI models generate syntactically correct code that calls non-existent methods at the declared version — always run `grep` or IDE symbol lookup to confirm existence.
- Hallucination patterns to watch: method chaining that doesn't exist, optional parameters treated as required, deprecated APIs used with new signatures, invented enum values.
- "Refactors" generated by AI are frequently semantically equivalent for the happy path but diverge on error paths, edge inputs, and concurrency — never accept without test evidence.
- AI-generated tests almost exclusively test the happy path through mocks — check that mocks are configured to return realistic error states and that assertions cover those paths.
- Generated abstractions often introduce hidden coupling: a utility function that "simplifies" code may carry implicit dependency on global state, singleton, or execution order.
- When reviewing an AI-generated security check: assume it is bypassable. Test with invalid tokens, expired credentials, null inputs, and injection strings.
- Dependency footprint: AI frequently adds a 200 kB library to solve a problem solvable with 10 lines of standard library code — always propose the standard-library alternative.
- Code comments generated by AI describe the happy-path intent, not the failure modes — treat AI-generated comments as documentation placeholders, not as analysis.

### Anti-Examples

| AI Output Pattern | Problem | Required Action |
|---|---|---|
| `lodash.deepClone(obj)` (using non-existent method) | Hallucinated API | Verify method name and version; replace with `structuredClone` or `_.cloneDeep` |
| `catch (e) {}` (swallowed exception) | Silent failure | Require logging, error propagation, or explicit ignore with comment |
| New `AbstractFactory` for single implementation | Over-abstraction | Collapse to direct instantiation; reintroduce factory when second implementation exists |
| New stateless `Helper` class with unrelated methods | Helper bag | Move methods to owning objects/modules or collapse to local functions |
| Policy function writes to database and emits events | Side-effect pollution | Split pure policy from orchestrating service and adapter side effects |
| Business fixture added to shared test utils | Test ownership pollution | Move fixture/factory to owning module test boundary |
| Feature flag added with no cleanup path | Permanent compatibility debt | Add owner, expiry, old/new tests, and removal plan |
| Test asserts `expect(mockFn).toHaveBeenCalled()` only | Mock-only test | Add assertion on actual output or side effect |
| `import { compress } from 'lz4-wasm'` (new dep) | Undeclared dependency | CVE scan, license review, standard-library alternative evaluation |

## Failure Modes
- **Hallucinated API silently returns `undefined`** in dynamic languages — feature ships broken, discovered in production not code review.
- **Over-abstraction hides simple logic**: a three-layer factory wrapping a single `if` statement — maintainers cannot reason about it.
- **Dependency additions bloat the attack surface**: a new package with a transitive dependency on a known CVE ships without audit.
- **Tests pass only on mocks**: all assertions check mock call counts; the production code path is never actually executed.
- **Silent behavioral divergence**: refactored code produces the same output for happy-path inputs but handles edge cases differently — regression is discovered later.
- **Type annotation drift**: AI annotates a function as returning `User` but the actual return includes `null` for missing records — crashes downstream consumers.
- **Assumed singleton breaks under test parallelism**: AI-generated code assumes global state is process-scoped; parallel test execution causes flaky failures.
- **Security bypass via AI-generated check**: a generated RBAC check validates role name as a string comparison but misses case-sensitivity or role hierarchy.
- **Generated migration has no rollback**: AI writes `ALTER TABLE DROP COLUMN` without a corresponding rollback migration — accepted without review.
- **Generated comments describe intent, not behavior**: reviewers skip the code because the comment "looks complete" — the edge case is invisible.
- **Generated helper bag becomes permanent API**: a stateless class collects unrelated helpers, gains public exports, and is too coupled to delete.
- **Generated side-effect pollution hides business decisions**: a policy writes the database and calls an API, so pure decision tests require mocks for infrastructure.
- **Generated code only adds paths**: deprecated branches, feature flags, TODOs, and compatibility code remain with no owner or expiry.

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
Return a structured review with:
- **Mode selected**: generated review, behavior-preserving refactor, bug-fix review, structure/reuse audit, test quality review, or security/performance-sensitive AI code, with trigger signal.
- **Severity-classified findings**: Critical/High/Medium/Low findings first, each with file/line, impact, evidence, and required action; no generic suggestion list.
- **Boundaries inspected**: requirements, acceptance criteria, non-goals, changed files, call sites, public contracts, reuse candidates, tests, dependencies, security/performance boundaries, and validation outputs inspected or skipped with reason.
- **Professional judgment**: accept, return, split, or refactor decision; AI-specific risks ruled out; and risks still possible.
- **Verified API inventory**: Each API call confirmed present / confirmed absent (hallucinated) / unverified.
- **Hidden assumption list**: Every implicit assumption with proposed enforcement or documentation.
- **Dependency audit**: Each new dependency with CVE status, license, transitive size, and standard-library alternative.
- **Refactor boundary analysis**: Scope of behavioral change, equivalence evidence, and test coverage delta.
- **Implementation Structure Plan**: Reuse candidates inspected, reuse vs. extension vs. composition vs. new code decision, function/class/file/directory placement, public/private boundary, shared utils audit, dependency direction, test placement, and rejected alternatives.
- **Naming evidence**: AI-added or AI-renamed variables, functions, methods, classes, files, and directories match repository vocabulary, language convention, semantic responsibility, and local pattern scan; vague names are listed with required replacements.
- **Execution Discipline Report**: Evidence inventory, verified-cause statement when diagnosis is involved, route-repair ledger after repeated failure, same-pattern scan record for local fixes, and closure package.
- **Test quality assessment**: Mock-only tests flagged; missing error path tests listed.
- **Testability seam review**: public behavior boundary, fake/stub/mock/spy decision, fixture ownership, deterministic time/randomness strategy, and private-helper non-export findings.
- **Dependency lifecycle review**: composition root, dependency graph, lifecycle scope, service locator/global state, reusable client/pool ownership, shutdown cleanup, and test override findings.
- **Algorithm/data-structure review**: input scale, complexity, memory budget, load-all/nested-scan risk, selected structure, benchmark/profile evidence, and rejected alternatives.
- **Failure contract review**: typed failure states, boundary translation, retryability, silent fallback, partial failure, safe diagnostics, and negative-path evidence.
- **Model and side-effect review**: DTO/domain/persistence/event boundary leakage, mapper-owned business logic, hidden side effects, event-before-commit, cache source of truth, and idempotency/compensation evidence.
- **Config and cleanup review**: typed config, feature flag owner/expiry, mode/kind governance, stale compatibility branch, deletion path, telemetry, and rollback after deletion.
- **Architecture enforcement and consumer impact review**: whether public exports and architecture rules have CI enforcement and whether changed public contracts have consumer migration evidence.
- **Security review note**: Auth, permission, and data access paths reviewed adversarially or escalated.
- **Architecture drift flag**: Any new abstractions, boundaries, or coupling evaluated against existing patterns.
- **Spec Compliance Result**: Stage 1 pass/fail, naming the requirement, acceptance criterion, non-goal, or compatibility gap that fails.
- **Code Quality Result**: Stage 2 result, recorded only after spec compliance passes.
- **Open Issues**: unresolved spec or quality issues, each tagged with its stage.
- **Re-review Required**: which stage must be re-reviewed after the fix.
- **Approval Scope**: what the approval covers and what it explicitly does not.
- **Approval status**: Approved with evidence / Returned for remediation with numbered action items.
- **Local naming evidence**:
  same-directory file names inspected;
  parent-module naming pattern inspected;
  selected filename/function/class/method name;
  rejected alternatives;
  repository vocabulary alignment.
- **Reuse ladder review**:
  direct reuse candidates;
  extension reuse candidates;
  composition/wrapper candidates;
  extraction candidates;
  final new-code justification.
- **Extension safety review**:
  old behavior preserved;
  compatibility risk;
  old behavior tests;
  new behavior tests;
  rejected parallel implementation.
- **Advanced refactor review**:
  object/function/module choice;
  class/interface/inheritance/reflection justification;
  state/invariant/lifecycle/collaborator rationale;
  public behavior tests.
- **Comment quality review**:
  exported declarations missing doc comments;
  public APIs with incomplete contract comments;
  complex internal logic missing critical comments;
  tests missing scenario/regression comments;
  redundant or misleading comments removed;
  AI-generated comments accepted / rewritten / rejected.
- **Clarity and maintainability review**:
  main-flow readability;
  oversized function/class/file findings;
  side-effect boundary findings;
  stateless helper bag findings;
  speculative interface/factory/strategy findings;
  cleanup/deprecation/feature-flag removal findings;
  change-locality findings.
- **Validation evidence**: commands run, outputs, what they prove/do not prove, stale/unrun validations, residual risk, and next gate.
- **Evidence limits**: what API searches, typechecks, tests, scans, and review evidence prove and what they do not prove about edge behavior, performance, security, or broad refactor equivalence.

## Evidence Contract
Close an AI-code review or refactor only when all five canonical answers are concrete (answer schema: `agent-execution-discipline`). Keep the two phases distinct: review only finds problems; refactor must prove behavior is preserved.
- **Basis**: the selected mode, standard, requirement, repository pattern, or real API the judgment rests on — every cited symbol or signature verified to exist, not assumed.
- **Files and boundaries inspected**: requirements, acceptance criteria, non-goals, same-pattern scan across the codebase, call sites, public contracts, tests, dependencies, and security/performance boundaries read, and the duplication or boundary drift found.
- **Placement rationale**: the reuse-versus-new and placement decision for each added or moved element (via `implementation-structure-design`), with the rejected alternative.
- **Validation commands**: hallucinated-API check, typecheck/build, characterization/regression tests, security/performance checks, and generated-test review run, each with its outcome, what evidence proves, and what evidence does not prove.
- **AI review judgment and handoff**: mode selected, accept/return/refactor judgment, behavior preservation, evidence limits, and re-review or next gate.
- **Residual risk**: unreviewed path, untested branch, accepted finding, stale validation, hidden behavior-change risk, or broad refactor boundary that remains, and the named owner of the follow-up.

## Quality Gate
1. All external API calls verified to exist in the declared dependency version.
2. All new dependencies have passed CVE scan and license review.
3. Security-sensitive code has been reviewed adversarially or escalated to `security-privacy-gate`.
4. All behavior-changing refactors have behavioral equivalence evidence (test or documented diff).
5. Tests assert real behavioral outcomes, not only mock call counts.
6. All hidden assumptions are documented or enforced.
7. No new abstraction without documented justification against existing alternatives.
8. Type annotations are runtime-accurate, not syntactically plausible.
9. Error paths have explicit handling — no silent swallows.
10. The review result is either: Approved with evidence, or Returned with a numbered remediation list.
11. AI-added functions, classes, files, directories, components, hooks, services, repositories, adapters, utilities, and abstractions have reuse and placement rationale.
12. AI-added abstractions are justified against existing local patterns and the simplest sufficient alternative.
13. AI-added or AI-renamed variables, functions, methods, classes, files, and directories follow repository vocabulary, language convention, semantic responsibility, and local pattern scan evidence.
14. AI-generated code did not introduce business logic into shared, common, or utils.
15. AI-assisted completion is not accepted without execution evidence, validation results, residual risk, and handoff boundary.
16. Reject exported/public declarations without language-standard doc comments.
17. Reject complex business, concurrency, transaction, retry, compatibility, fallback, performance-sensitive, or security-sensitive logic without concise intent comments.
18. Reject non-trivial tests that do not explain scenario, regression, fixture purpose, or edge case.
19. Reject comments that merely repeat the code.
20. Reject AI-generated comments that claim intent not proven by code or tests.
21. Reject AI-generated file additions without same-directory and parent-module naming evidence.
22. Reject AI-generated helper/utility/common/shared code without reuse ladder evidence.
23. Reject AI-generated duplicated logic when an existing implementation can be reused or extended safely.
24. Reject AI-generated advanced abstraction without advanced refactor evidence.
25. Reject AI-generated stateless helper bags and speculative factories, strategies, interfaces, or registries without current variation and public behavior tests.
26. Reject AI-generated functions that mix policy, validation, mutation, persistence, external API calls, events, logging, mapping, and fallback without an orchestration boundary.
27. Reject AI-generated feature flags, deprecated API use, compatibility branches, dead code, and TODO cleanup without owner, expiry, and removal plan.
28. Findings are severity-classified and ordered by impact; approvals without findings severity and validation evidence are rejected.
29. AI-generated fixes include same-pattern scan and behavior-preservation evidence before approval.
28. Reject AI-generated test helpers that place business fixtures in shared/common test utilities instead of the owning module boundary.
29. Reject completion claims that use success-implying language ("done", "fixed", "should pass", "works") without a fresh command output, validator result, or artifact from the current change.
30. Reject partial verification reported as full: a lint-only or single-test pass presented as "all tests pass" or "build is green" is returned for honest scoping with the gap named.

## Handoff
- **security-privacy-gate** — for auth, permission, payment, or sensitive data code that requires adversarial review.
- **architecture-impact-reviewer** — when new abstractions, service boundaries, or cross-module coupling are introduced.
- **data-api-contract-changer** — when a refactor silently alters contract semantics or response shapes.
- **quality-test-gate** — when test coverage gaps are identified that require systematic test design.
- **backend-change-builder** — when implementation work is needed to remediate findings.
- **testability-seam-design** — when AI-generated tests or code expose private helpers, over-mock internals, or need deterministic seams.
- **dependency-wiring-lifecycle** — when AI changes dependency graphs, clients, pools, globals, service locators, or shutdown paths.
- **algorithm-data-structure-selection** — when AI chooses algorithms, data structures, batching, streaming, sorting, grouping, or load-all processing.
- **failure-contract-design** — when AI swallows, generalizes, retries, leaks, or mistranslates failures across boundaries.
- **data-side-effect-flow-tracing** — when AI hides side effects in mappers, getters, domain objects, policies, helpers, decorators, or proxies.
- **configuration-runtime-policy** — when AI introduces runtime config, flags, kill switches, mode/kind switches, or config-driven behavior.
- **model-boundary-mapping** — when AI leaks DTOs, ORM/persistence models, generated clients, events, or mapper-owned business rules across boundaries.
- **consumer-impact-analysis** — when AI changes public contracts, generated clients, schemas, events, SDKs, or exports that downstream consumers may depend on.
- **architecture-enforcement-tooling** — when AI changes architecture rules, imports, exports, generated-code policy, or forbidden dependencies without CI enforcement.
- **cleanup-deletion-governance** — when AI leaves dead code, flags, fallbacks, deprecated APIs, or compatibility branches without removal path.
- **agent-execution-discipline** — when AI-assisted work lacks evidence, verified cause, route repair, same-pattern scan, or closure package.

## Completion Criteria
AI-generated or AI-assisted code is either accepted with documented evidence of API correctness, behavioral equivalence, dependency safety, test coverage, and security review — or returned with a numbered, actionable remediation list that can be resolved without ambiguity.
