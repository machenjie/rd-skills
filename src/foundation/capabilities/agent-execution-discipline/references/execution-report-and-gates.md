# Execution Report And Gates

Load this reference when `agent-execution-discipline` needs the full Execution Discipline Report field list or exhaustive Quality Gate. The capability body keeps the decision-critical execution kernel compact.

## Output Contract
Return an Execution Discipline Report alongside any non-trivial agent-assisted change:

- **Evidence inventory**: list of commands run, outputs captured, artifacts produced, outcomes.
- **Runtime prompt flow ledger**: requirement clarification, inspected boundaries before plan, TDD/validation signal, action owner/review map, and repair/re-review record.
- **Completion claim status**: verified (with the backing command and outcome), partially verified (with the gap named), or not verified (with the not-verified disclosure: status, why not run, residual risk, exact command).
- **Validation broker result**: selected command level, outcome, evidence strength, coverage alignment, freshness after final material edit, and next route when evidence is weak or negative.
- **Adapter closure contract**: supported closure checks, unsupported checks, degradation policy, fail-open/fail-closed status, and residual risk.
- **Repository context map**: owning surface, related files, caller/callee flow, conventions, tests/config/docs, generated artifacts, rejected locations, and not-inspected boundaries.
- **Workflow state summary**: current phase, allowed transition, owner/reviewer split, validation freshness, open findings, repair/re-review status, and closure readiness.
- **Tool permission/sandbox record**: risky tool/action class, permission state, sandbox boundary, dry-run/revert path, and redaction rule.
- **Verified cause statement** (when a diagnosis is part of the change): symptom, hypothesis, method, verified cause, counter-evidence.
- **Route repair ledger** (when applicable): attempt 1, attempt 2, failure signature, route change, new hypothesis.
- **Same-pattern scan record** (when a local fix is applied): pattern signature, scope, other occurrences, decision.
- **Proactive closure package**: boundary, validation results, residual risk, handoff target.
- **Plan-execution consistency record**: accepted plan, actual changed files, validation commands, skipped work, stale evidence, unplanned behavior changes, and residual-risk reconciliation.
- **Professional evidence contract answer set**: basis; files and boundaries inspected; reuse/placement rationale; behavior preservation when applicable; validation commands; residual risk; next gate.
- **Trajectory inspection record**: optional offline evidence view built from telemetry, memory facts, and validation signals. It may support review of skipped stages, stale validation, missing residual risk, or repair without re-review, but it never auto-mutates skills, routing rules, capabilities, or project content.
- **Discipline violations**: any rule violation that was accepted with justification, or "none".
- **Local convention scan record**: same file, same directory, parent module, sibling module, tests, selected convention.
- **Reuse ladder record**: direct reuse, extension reuse, composition, adapter/wrapper, extraction, new code decision.
- **Extension safety record**: old behavior preserved, compatibility risk, tests covering old and new behavior.
- **Comment quality record**: exported/public comments, complex internal comments, test scenario/regression comments, redundant comments removed, and intentional omissions.

## Quality Gate
1. Completion claim has an evidence inventory with at least one concrete command-output, artifact, or validator result.
2. Engineering work did not start before requirement clarification, unless the output explicitly states no engineering action is being taken.
3. Planning did not start before relevant target-project code, tests, configs, docs, conventions, and call-chain boundaries were inspected, or not-inspected risk was explicitly accepted for non-executing advice.
4. Implementation did not start before a TDD or validation signal was named.
5. Every action names an owner skill/capability and a different review skill/capability.
6. Every review finding has a repair owner and re-review result before closure, or a not-verified residual risk disclosure with owner.
7. Any diagnosis attached to the change carries a verified-cause statement.
8. If the agent attempted the same approach twice and failed, a route repair ledger is attached and no third same-path retry occurred.
9. Any local code fix carries a same-pattern scan record covering the rest of the codebase.
10. Any new function, class, file, directory, component, hook, service, repository, adapter, utility, or abstraction carries reuse and placement rationale.
11. The closure package lists boundary, validation results, residual risks, and the next handoff target.
12. No entertainment rhetoric, persona narration, emoji status lines, or runtime PUA state are introduced by the change.
13. Any new or renamed structure has local naming convention evidence.
14. Any new code has a Reuse Ladder Record.
15. Any extension of existing logic has an Extension Safety Record.
16. Any exported/public declaration has a doc comment in the language-standard format.
17. Any complex internal logic and non-trivial test has required comments or an explicit omission rationale.
18. When a professional skill emits an Evidence Contract, all five canonical answers, basis, files and boundaries inspected, placement rationale, validation commands, and residual risk, are present and non-empty.
19. Any completion claim names a fresh verification (command, validator, or test) that ran against the current change; success-implying language without backing evidence is absent.
20. Partial verification is reported as partial, never generalized to a full pass; "all tests pass" is not claimed from a lint-only or single-test run.
21. When verification could not run, a not-verified disclosure, status, why not run, residual risk, exact command, replaces any completion claim.
22. When the change is a review, spec compliance (requirement, acceptance criteria, non-goals, plan, compatibility, old-behavior preservation) is confirmed before code-quality judgement, and implementer self-review does not replace independent review.
23. AI-generated code is rejected or repaired when it shows local-only fixing, invented helpers, missing reuse search, wrong shared/common placement, hidden scope expansion, or validation overclaim.
24. Every professional skill closure answers the full evidence contract set: inspected boundaries, judgment, reuse/placement rationale, behavior preservation, validation evidence, residual risk, and next gate.
25. Repository context is present before planning or action for target-project engineering and skill-authoring work.
26. Workflow state is explicit before phase transitions and at handoff.
27. Risky shell, connector/MCP, destructive, deploy, migration, network-write, secret-bearing, or untrusted-output actions carry tool permission/sandbox evidence.
28. Final review and handoff include plan-execution consistency and disclose stale validation or unplanned changes.
29. When a trajectory report is cited as evidence, its validation freshness, review integrity, and issue list are reconciled with the final handoff rather than treated as automatic approval.
30. When adapter capabilities limit evidence collection, closure language names the unsupported capability and avoids full-verification claims.
