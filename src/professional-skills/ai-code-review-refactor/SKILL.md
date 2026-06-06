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
- **Verified API inventory**: Each API call confirmed present / confirmed absent (hallucinated) / unverified.
- **Hidden assumption list**: Every implicit assumption with proposed enforcement or documentation.
- **Dependency audit**: Each new dependency with CVE status, license, transitive size, and standard-library alternative.
- **Refactor boundary analysis**: Scope of behavioral change, equivalence evidence, and test coverage delta.
- **Implementation Structure Plan**: Reuse candidates inspected, reuse vs. extension vs. composition vs. new code decision, function/class/file/directory placement, public/private boundary, shared utils audit, dependency direction, test placement, and rejected alternatives.
- **Naming evidence**: AI-added or AI-renamed variables, functions, methods, classes, files, and directories match repository vocabulary, language convention, semantic responsibility, and local pattern scan; vague names are listed with required replacements.
- **Execution Discipline Report**: Evidence inventory, verified-cause statement when diagnosis is involved, route-repair ledger after repeated failure, same-pattern scan record for local fixes, and closure package.
- **Test quality assessment**: Mock-only tests flagged; missing error path tests listed.
- **Security review note**: Auth, permission, and data access paths reviewed adversarially or escalated.
- **Architecture drift flag**: Any new abstractions, boundaries, or coupling evaluated against existing patterns.
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

## Handoff
- **security-privacy-gate** — for auth, permission, payment, or sensitive data code that requires adversarial review.
- **architecture-impact-reviewer** — when new abstractions, service boundaries, or cross-module coupling are introduced.
- **data-api-contract-changer** — when a refactor silently alters contract semantics or response shapes.
- **quality-test-gate** — when test coverage gaps are identified that require systematic test design.
- **backend-change-builder** — when implementation work is needed to remediate findings.
- **agent-execution-discipline** — when AI-assisted work lacks evidence, verified cause, route repair, same-pattern scan, or closure package.

## Completion Criteria
AI-generated or AI-assisted code is either accepted with documented evidence of API correctness, behavioral equivalence, dependency safety, test coverage, and security review — or returned with a numbered, actionable remediation list that can be resolved without ambiguity.
