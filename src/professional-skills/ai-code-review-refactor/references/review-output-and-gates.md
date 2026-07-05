# AI Review Output And Gates

Load this reference when a review needs the full output schema, exhaustive gate checklist, or detailed handoff routing for `ai-code-review-refactor`. The skill body keeps the default flow concise; this file preserves the detailed professional contract.

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
- **Independent review record**: requirement, accepted plan, final diff, test/validation evidence, reviewer skill/capability, implementer separation, and repair/re-review result.
- **Process evidence review**: trajectory view, memory projection limits, context-pack freshness, and whether any edit-before-read, repeat-failure, fragile-file, or stale-validation signal changes approval scope.
- **Plan-execution consistency**: accepted plan compared to actual changed files, validation commands, skipped work, stale evidence, unplanned behavior changes, and residual risk before approval.
- **Local naming evidence**: same-directory file names inspected; parent-module naming pattern inspected; selected filename/function/class/method name; rejected alternatives; repository vocabulary alignment.
- **Reuse ladder review**: direct reuse candidates; extension reuse candidates; composition/wrapper candidates; extraction candidates; final new-code justification.
- **Extension safety review**: old behavior preserved; compatibility risk; old behavior tests; new behavior tests; rejected parallel implementation.
- **Advanced refactor review**: object/function/module choice; class/interface/inheritance/reflection justification; state/invariant/lifecycle/collaborator rationale; public behavior tests.
- **Comment quality review**: exported declarations missing doc comments; public APIs with incomplete contract comments; complex internal logic missing critical comments; tests missing scenario/regression comments; redundant or misleading comments removed; AI-generated comments accepted / rewritten / rejected.
- **Clarity and maintainability review**: main-flow readability; oversized function/class/file findings; side-effect boundary findings; stateless helper bag findings; speculative interface/factory/strategy findings; cleanup/deprecation/feature-flag removal findings; change-locality findings.
- **Complexity-only delete list**: `delete` / `stdlib` / `native` / `existing-code` / `yagni` / `shrink` findings when `minimal-correct-implementation` is selected; normal correctness, security, reliability, and test findings remain separate.
- **Validation evidence**: commands run, outputs, what they prove/do not prove, stale/unrun validations, residual risk, and next gate.
- **Evidence limits**: what API searches, typechecks, tests, scans, and review evidence prove and what they do not prove about edge behavior, performance, security, or broad refactor equivalence.

## Evidence Contract
Close an AI-code review or refactor only when all five canonical answers are concrete (answer schema: `agent-execution-discipline`). Keep the two phases distinct: review only finds problems; refactor must prove behavior is preserved.
- **Basis**: the selected mode, standard, requirement, repository pattern, or real API the judgment rests on; every cited symbol or signature verified to exist, not assumed.
- **Files and boundaries inspected**: requirements, acceptance criteria, non-goals, same-pattern scan across the codebase, call sites, public contracts, tests, dependencies, and security/performance boundaries read, and the duplication or boundary drift found.
- **Placement rationale**: the reuse-versus-new and placement decision for each added or moved element (via `implementation-structure-design`), with the rejected alternative.
- **Validation commands**: hallucinated-API check, typecheck/build, characterization/regression tests, security/performance checks, and generated-test review run, each with its outcome, what evidence proves, and what evidence does not prove.
- **AI review judgment and handoff**: mode selected, spec-compliance result, code-quality result, approval scope, accept/return/refactor judgment, behavior preservation, evidence limits, and re-review or next gate.
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
9. Error paths have explicit handling; no silent swallows.
10. The review result is either Approved with evidence or Returned with a numbered remediation list.
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
30. Reject AI-generated test helpers that place business fixtures in shared/common test utilities instead of the owning module boundary.
31. Reject completion claims that use success-implying language without a fresh command output, validator result, or artifact from the current change.
32. Reject partial verification reported as full: a lint-only or single-test pass presented as "all tests pass" or "build is green" is returned for honest scoping with the gap named.
33. Reject approvals that do not explicitly cover requirement compliance, accepted plan match, final diff scope, changed-code-to-test mapping, validation freshness, and approval limits.
34. Reject final-diff-only approval when trajectory, memory, or context-pack evidence indicates unreviewed repair, stale context, or unsupported closure.
35. Reject implementer self-approval as independent review.
36. Reject repaired findings that have not been re-reviewed at the stage where the finding was raised.

## Handoff
- **security-privacy-gate**: auth, permission, payment, or sensitive data code that requires adversarial review.
- **architecture-impact-reviewer**: new abstractions, service boundaries, or cross-module coupling.
- **data-api-contract-changer**: refactor silently alters contract semantics or response shapes.
- **quality-test-gate**: test coverage gaps require systematic test design.
- **backend-change-builder**: implementation work is needed to remediate findings.
- **testability-seam-design**: generated tests or code expose private helpers, over-mock internals, or need deterministic seams.
- **dependency-wiring-lifecycle**: AI changes dependency graphs, clients, pools, globals, service locators, or shutdown paths.
- **algorithm-data-structure-selection**: AI chooses algorithms, data structures, batching, streaming, sorting, grouping, or load-all processing.
- **failure-contract-design**: AI swallows, generalizes, retries, leaks, or mistranslates failures across boundaries.
- **data-side-effect-flow-tracing**: AI hides side effects in mappers, getters, domain objects, policies, helpers, decorators, or proxies.
- **configuration-runtime-policy**: AI introduces runtime config, flags, kill switches, mode/kind switches, or config-driven behavior.
- **model-boundary-mapping**: AI leaks DTOs, ORM/persistence models, generated clients, events, or mapper-owned business rules across boundaries.
- **consumer-impact-analysis**: AI changes public contracts, generated clients, schemas, events, SDKs, or exports that downstream consumers may depend on.
- **architecture-enforcement-tooling**: AI changes architecture rules, imports, exports, generated-code policy, or forbidden dependencies without CI enforcement.
- **cleanup-deletion-governance**: AI leaves dead code, flags, fallbacks, deprecated APIs, or compatibility branches without removal path.
- **agent-execution-discipline**: AI-assisted work lacks evidence, verified cause, route repair, same-pattern scan, or closure package.
