---
name: architecture-enforcement-tooling
description: Converts architecture and module rules into static checks, lint rules, dependency graph gates, type strictness, CI commands, generated-code exceptions, and migration paths.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "114"
changeforge_version: 0.1.0
---

# Mission

Turn accepted architecture and module-boundary decisions into deterministic checks, lint rules, dependency graph gates, type strictness, CI commands, generated-code exception policy, and ratcheted baselines so architecture drift is caught by execution evidence rather than memory or review discipline alone.

# When To Use

Use when architecture, module, layer, import, public/private export, forbidden dependency, generated-code, dead-code, lint, type-check strictness, affected-test, build-cache, or complexity rules are declared but not enforced.

Use when a repo needs ArchUnit, Dependency Cruiser, import-linter, ESLint boundaries, go vet, staticcheck, or language-appropriate static checks.

Use when CI green status depends on import boundaries, generated-file policy, public export shape, dependency direction, dead-code detection, or affected-test selection that is only documented.

# Do Not Use When

Do not use to add tooling before the architecture rule is clear and accepted.

Do not block urgent local fixes on full enforcement rollout when a staged migration with warnings is safer.

Do not use to invent the architecture rule itself, approve a new dependency without supply-chain review, or delete violations without caller, consumer, and rollback evidence.

# Stage Fit

Use during design when rules are being converted into executable checks, during implementation when lint or graph tooling is wired into scripts/CI, during review when a boundary rule has no representative failing example, during validation when report-only baselines or ratchets decide release evidence, and during cleanup when old violations are removed. Repository graph and project memory can identify likely drift, but current source, current CI configuration, and fresh command output decide closure.

# Non-Negotiable Rules

- Every enforced rule must map to an architecture or module-boundary decision.
- Tooling must run in CI, pre-merge, or a timeboxed report-only gate; otherwise the rule remains advisory.
- Generated code exceptions must be explicit and narrow.
- Enforcement must include failure examples.
- Migration path must avoid breaking all existing work without owner review, baseline ownership, and ratchet policy.
- Public/private export checks must preserve intentional public contracts.
- Type/lint/complexity strictness must be scoped and ratcheted when immediate full strictness is not feasible.
- Tool selection must fit the language, framework, package graph, and CI runner; a familiar tool that cannot express the rule is not enforcement.
- New tools or plugins must pass dependency, license, install-script, and reproducible-install review.
- Existing violations must be classified as block-now, baseline, suppress-with-owner, or delete; silent ignore is not an option.
- A green enforcement command is not enough unless the rule list, expected failure, exception policy, and changed-path coverage are recorded.

# Industry Benchmarks

Anchor against fitness functions in evolutionary architecture, ArchUnit, Dependency Cruiser, import-linter, ESLint boundaries, go vet, staticcheck, TypeScript strict mode, dead code detection, dependency cycle detection, and CI quality gate practice.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Route or skip |
| --- | --- | --- | --- | --- |
| Import and layer boundary | Forbidden imports, internal module access, layer inversion, or cycle risk. | Encode allowed and forbidden edges without hiding ownership ambiguity. | Rule source, graph edge examples, tool config, representative failing import. | Route rule ownership to `module-boundary-design`. |
| Public export surface | Barrel export, package API, SDK surface, generated client, or public/private split. | Preserve real consumers while preventing accidental API expansion. | Export diff, consumer impact, allowed public facade, failing internal import. | Route consumer risk to `consumer-impact-analysis`. |
| Generated/runtime exception | Codegen, framework registration, reflection, migration, CLI entry point, or plugin discovery. | Keep exceptions narrow enough that real violations still fail. | Source-of-truth, generated path pattern, exception owner, drift check. | Route source/generated policy to `package-dependency-management` or owner skill. |
| Type/lint/complexity strictness | Strict mode, staticcheck, go vet, dead-code, complexity, or language lint upgrade. | Ratchet quality without broad false positives or generated-code noise. | Scope, baseline count, threshold, tool command, ratchet interval. | Skip full rollout when report-only baseline is safer. |
| CI and affected-test gate | Rule must block PRs, affect build cache, or control affected-test selection. | Make enforcement deterministic, fresh, and visible in release evidence. | CI job name, command, cache inputs, generated inputs, full-suite fallback. | Route pipeline placement to `ci-cd` and evidence depth to `quality-test-gate`. |
| Violation cleanup | Existing violations, stale suppressions, deprecated exports, dead code, or old compatibility branches. | Remove or suppress with caller search, owner, telemetry when needed, and rollback. | Caller search, suppress/delete decision, cleanup issue, rollback path. | Route removal to `cleanup-deletion-governance`. |

# Selection Rules

Select this capability when the primary gap is enforcement tooling. Use `module-boundary-design` for the rule itself, `architecture-impact-reviewer` for architectural tradeoffs, `ci-cd` for pipeline placement, `package-dependency-management` for tool dependency risk, and `quality-test-gate` when enforcement becomes release evidence.

Keep ownership narrow. This capability owns executable enforcement design: rule-to-tool mapping, command, CI placement, exception policy, baseline, failure sample, and validation freshness. It does not own architecture rule creation, consumer migration, dependency approval, cleanup deletion, or release gate approval; it hands those surfaces off after naming the enforcement boundary.

# Technical Selection Criteria

Evaluate enforcement by rule expressiveness, language/framework fit, graph visibility, generated-source policy, public API surface, package/workspace topology, CI determinism, cache invalidation inputs, baseline size, expected false positives, suppressions, local developer feedback, failure messaging, and ratchet path. Prefer the smallest existing tool that can express the rule and run deterministically in CI; add a new tool only when standard lint/type/build/test commands cannot enforce the rule.

# Risk Escalation Rules

Escalate to `delivery-release-gate` when new CI gates affect release flow. Escalate to `architecture-impact-reviewer` when enforcement reveals ambiguous ownership. Escalate to `ai-code-review-refactor` when generated code or AI-produced files need exemptions that could hide real violations.

Escalate to `security-privacy-gate` when a rule touches authentication, authorization, secrets, permission boundaries, or supply-chain-sensitive tooling. Escalate to `package-dependency-management` when enforcement requires a new package, plugin, action, binary, container image, or lockfile change. Escalate to `consumer-impact-analysis` before blocking or removing public exports that may be used outside local search scope.

# Reference Loading Policy

Current mode is inline-only: this capability has no deep reference files today, so this `SKILL.md` contains the active architecture enforcement rules.

If deep references are added later, load them only for L3+ work, module or public-boundary enforcement, import/cycle/export rules, generated-code exceptions, CI gate design, or staged migration of existing violations.

Do not load deep references for L1/L2 local checks where the inline output contract for rule list, tool choice, CI command, failure example, and exception policy is sufficient.

# Critical Details

- Import boundary checks enforce allowed dependency direction and forbidden cross-module internals.
- Cycle detection prevents circular module, package, class, or project graph dependencies.
- Public/private export checks catch accidental public API expansion and internals imported by consumers.
- Forbidden dependency rules block UI-to-data, domain-to-infrastructure, feature-to-feature, or test-to-production violations.
- Dead code detection must account for runtime reflection, generated entry points, CLI commands, migrations, and framework registration.
- Complexity thresholds should match local language tooling and avoid punishing generated code.
- CI command must be deterministic and documented.
- Migration path can begin in report-only mode, baseline existing violations, then ratchet.
- Suppressions require owner, reason, scope, and expiry or review trigger.
- Local developer feedback should be fast, but CI remains the source of enforcement evidence.
- Failure output should point to the violated rule and the intended replacement path, not just a generic lint error.

# Proactive Professional Triggers

- **Signal:** an ADR, README, CODEOWNERS note, or review comment states an import, layer, export, or dependency rule with no executable check. **Hidden risk:** architecture drift returns after memory of the decision fades. **Required professional action:** convert the rule to a tool-backed check or staged report-only baseline. **Route to:** `architecture-enforcement-tooling`, `ci-cd`. **Evidence required:** accepted rule, tool command, CI location, failure example, and owner.
- **Signal:** a boundary rule is enforced by a broad glob, blanket ignore, or generated-code exemption. **Hidden risk:** the exception hides real violations. **Required professional action:** narrow the exception to source-of-truth paths, generated outputs, or framework entry points. **Route to:** `architecture-enforcement-tooling`, `package-dependency-management`. **Evidence required:** exception pattern, source/generated authority, drift check, and residual uncovered rule.
- **Signal:** public exports, package barrels, SDK surfaces, or generated clients are gated without consumer inventory. **Hidden risk:** enforcement breaks real downstream consumers or locks in an accidental public API. **Required professional action:** run consumer impact before blocking or removing exports. **Route to:** `consumer-impact-analysis`, `version-compatibility`. **Evidence required:** export diff, known/unknown consumers, compatibility path, and rollback.
- **Signal:** a new lint, graph, dead-code, or complexity tool is added because it is popular rather than because it expresses the accepted rule. **Hidden risk:** dependency and CI cost without real enforcement. **Required professional action:** compare existing commands and dependency cost before adding the tool. **Route to:** `package-dependency-management`, `quality-test-gate`. **Evidence required:** rejected existing option, dependency review, command, and proof of a violation it catches.
- **Signal:** CI gate is switched from report-only to blocking while existing violations remain. **Hidden risk:** all teams are blocked or the gate is disabled under pressure. **Required professional action:** classify baseline, ownership, ratchet threshold, and unblock path before enforcing. **Route to:** `ci-cd`, `cleanup-deletion-governance`. **Evidence required:** baseline count, owner list, suppression policy, ratchet rule, and cleanup issue.
- **Signal:** affected-test selection, build cache, or generated-file freshness depends on module graph rules. **Hidden risk:** tests are skipped because graph edges or generated inputs are invisible. **Required professional action:** include graph edges, generated inputs, lockfiles, and full-suite fallback in enforcement evidence. **Route to:** `quality-test-gate`, `validation-broker`. **Evidence required:** changed-path map, cache inputs, affected-test proof, and fallback cadence.
- **Signal:** dead-code enforcement proposes deletion where reflection, registration, migrations, config, scripts, or docs may reference the artifact. **Hidden risk:** static success deletes runtime behavior. **Required professional action:** require caller search and rollback before cleanup. **Route to:** `cleanup-deletion-governance`. **Evidence required:** static/runtime/generated/reference search, deletion test, and rollback path.

# Execution Coupling

- **Repository graph:** inspect package/module graph, import edges, public exports, generated sources, CI workflow files, scripts, and current violations before selecting a rule or command. A rule that cannot name the graph edge it protects is not ready for enforcement.
- **Project memory:** use prior drift incidents, hook warnings, or historical suppressions only as leads. Accept them only after current source, registry/routing, CI config, or command output confirms freshness.
- **Execution path:** map every rule to a runnable command, representative failing example, CI/report-only placement, and validator result. If the command is not run, state why and who owns the gap.
- **Plan consistency:** after changing rules, suppressions, generated inputs, CI jobs, or baselines, re-run mapped validation or mark previous evidence stale. Do not report a lint pass as architecture proof unless the lint command actually covers the rule.

# Failure Modes

- Architecture rule exists only in README or ADR and has no CI gate.
- Tool blocks generated code or framework conventions without an exception model.
- Rule is so broad that developers disable it locally.
- Existing violations are ignored without baseline or cleanup owner.
- Dead-code tool deletes reflection, registration, migration, or generated references.
- Public export check breaks consumers without consumer impact analysis.
- New dependency is added for enforcement without lockfile, license, or CVE review.
- CI cache or affected-test selection omits generated inputs and silently skips consumers.
- A blanket suppression converts a real boundary violation into permanent debt.

# Output Contract

Return an Architecture Enforcement Plan:

- Mode selected: trigger signal, selected enforcement mode, and skipped heavier mode with reason.
- Rule source: ADR, module-boundary decision, layer rule, public export policy, generated-source policy, or accepted review finding.
- Boundaries inspected: package/module graph, import edges, public exports, generated paths, CI jobs, scripts, existing tests, reports, and project-memory leads accepted or rejected.
- Rule list: allowed and forbidden imports, cycles, public/private exports, forbidden dependencies, dead-code, type/lint/complexity, generated-file, affected-test, or cache rules.
- Tool choice: existing command or new tool, language/framework fit, dependency cost, rejected alternatives, and local/CI runner compatibility.
- Enforcement config: rule snippet or config location, CI job name, command, fail/report-only behavior, cache/generated inputs, and full-suite fallback when applicable.
- Failure examples: at least one representative violation, expected error, and replacement path.
- Exceptions: generated code, runtime reflection, framework registration, migrations, CLI entry points, tests, suppressions, owner, scope, and expiry or review trigger.
- Baseline and migration path: current violation count, block-now versus report-only decision, owner, cleanup issue, ratchet threshold, and timeline trigger.
- Validation evidence: command, exit code, relevant result, covered paths, uncovered paths, freshness after final edit, and what the evidence proves or does not prove.
- Ownership and rollout: rule owner, pipeline owner, cleanup owner, communication path, rollback/unblock path, and residual unenforced rule.

# Evidence Contract

Close the plan only when each rule maps to an accepted architecture decision; graph, exports, generated inputs, CI placement, and current violations are inspected or explicitly marked not verified; the tool command is named; generated/runtime exceptions are listed with owners; at least one expected failure example exists; CI blocking or report-only migration is defined; validation output is fresh after the final material edit; and residual unenforced rules have owners, rollback/unblock path, and evidence limits.

# Benchmark Coverage

This capability covers executable architecture fitness functions, import/layer/cycle/export/forbidden-dependency checks, generated-source exceptions, CI gate placement, report-only baselines, ratchet policies, suppression governance, affected-test and build-cache coupling, failure examples, and validation freshness. It does not define the architecture rule itself, approve new dependency risk, or prove consumer compatibility; route those surfaces to the owning capability.

# Routing Coverage

Routes from `architecture-impact-reviewer`, `backend-change-builder`, `frontend-change-builder`, `delivery-release-gate`, `change-documentation-gate`, `ai-code-review-refactor`, and `quality-test-gate` should arrive here when a documented architecture, import, export, generated-code, lint, type, dead-code, complexity, affected-test, or cache rule needs executable enforcement. Route away when the primary need is rule definition, pipeline design, package approval, consumer migration, deletion cleanup, or release approval.

# Quality Gate

1. Enforced rule maps to a real architecture decision.
2. Tool choice fits the language and repo.
3. Existing commands and local tools were considered before adding a new dependency.
4. CI command exists or report-only migration is explicitly timeboxed.
5. Failure examples are documented with expected output and replacement path.
6. Generated and runtime-reflection exceptions are narrow and owner-scoped.
7. Public/private export behavior is covered and consumer impact is handled when public contracts change.
8. Current violations are blocked, baselined, suppressed with owner, or routed to cleanup.
9. Baseline and ratchet policy are defined when immediate full strictness is unsafe.
10. Affected-test, cache, and generated-input coverage is named when enforcement drives validation selection.
11. Suppressions include reason, scope, owner, and expiry or review trigger.
12. Validation evidence names command, outcome, covered paths, freshness, and evidence limits.
13. Rollback or unblock path exists for a bad gate, false positive, or emergency release.
14. Residual unenforced rules are explicit with owners.

# Used By

- architecture-impact-reviewer
- backend-change-builder
- frontend-change-builder
- delivery-release-gate
- change-documentation-gate
- ai-code-review-refactor
- quality-test-gate

# Handoff

Hand off to `module-boundary-design` for rule definition, `ci-cd` for pipeline integration, `package-dependency-management` for tool introduction, `consumer-impact-analysis` for public export effects, and `cleanup-deletion-governance` for violation cleanup.

# Completion Criteria

The capability is complete when architecture rules have tool-backed checks, CI or staged enforcement, exceptions, failure examples, ownership, migration path, and residual unenforced rule disclosure.
