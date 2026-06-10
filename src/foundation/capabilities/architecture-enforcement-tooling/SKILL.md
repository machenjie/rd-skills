---
name: architecture-enforcement-tooling
description: Converts architecture and module rules into static checks, lint rules, dependency graph gates, type strictness, CI commands, generated-code exceptions, and migration paths.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "114"
changeforge_version: 0.1.0
---

# Mission

Turn architecture rules into repeatable tooling and CI gates so module boundaries, dependency direction, exports, cycles, and complexity limits are enforced by more than documentation.

# When To Use

Use when architecture, module, layer, import, public/private export, forbidden dependency, generated code, dead code, lint, type-check strictness, or complexity rules are declared but not enforced.

Use when a repo needs ArchUnit, Dependency Cruiser, import-linter, ESLint boundaries, go vet, staticcheck, or language-appropriate static checks.

# Do Not Use When

Do not use to add tooling before the architecture rule is clear and accepted.

Do not block urgent local fixes on full enforcement rollout when a staged migration with warnings is safer.

# Non-Negotiable Rules

- Every enforced rule must map to an architecture or module-boundary decision.
- Tooling must run in CI or the rule remains advisory.
- Generated code exceptions must be explicit and narrow.
- Enforcement must include failure examples.
- Migration path must avoid breaking all existing work without owner review.
- Public/private export checks must preserve intentional public contracts.
- Type/lint/complexity strictness must be scoped and ratcheted when immediate full strictness is not feasible.

# Industry Benchmarks

Anchor against fitness functions in evolutionary architecture, ArchUnit, Dependency Cruiser, import-linter, ESLint boundaries, go vet, staticcheck, TypeScript strict mode, dead code detection, dependency cycle detection, and CI quality gate practice.

# Selection Rules

Select this capability when the primary gap is enforcement tooling. Use `module-boundary-design` for the rule itself, `architecture-impact-reviewer` for architectural tradeoffs, `ci-cd` for pipeline placement, `package-dependency-management` for tool dependency risk, and `quality-test-gate` when enforcement becomes release evidence.

# Risk Escalation Rules

Escalate to `delivery-release-gate` when new CI gates affect release flow. Escalate to `architecture-impact-reviewer` when enforcement reveals ambiguous ownership. Escalate to `ai-code-review-refactor` when generated code or AI-produced files need exemptions that could hide real violations.

# Critical Details

- Import boundary checks enforce allowed dependency direction and forbidden cross-module internals.
- Cycle detection prevents circular module, package, class, or project graph dependencies.
- Public/private export checks catch accidental public API expansion and internals imported by consumers.
- Forbidden dependency rules block UI-to-data, domain-to-infrastructure, feature-to-feature, or test-to-production violations.
- Dead code detection must account for runtime reflection, generated entry points, CLI commands, migrations, and framework registration.
- Complexity thresholds should match local language tooling and avoid punishing generated code.
- CI command must be deterministic and documented.
- Migration path can begin in report-only mode, baseline existing violations, then ratchet.

# Failure Modes

- Architecture rule exists only in README or ADR and has no CI gate.
- Tool blocks generated code or framework conventions without an exception model.
- Rule is so broad that developers disable it locally.
- Existing violations are ignored without baseline or cleanup owner.
- Dead-code tool deletes reflection, registration, migration, or generated references.
- Public export check breaks consumers without consumer impact analysis.

# Output Contract

Return an Architecture Enforcement Plan:

- Rule list.
- Tool choice.
- Language or framework fit.
- CI command.
- Failure examples.
- Generated code exceptions.
- Baseline and migration path.
- Ownership.
- Rollout and ratchet policy.
- Residual unenforced rule.

# Evidence Contract

Close the plan only when each rule maps to an accepted architecture decision, the tool command is named, generated/runtime exceptions are listed, at least one expected failure example exists, CI placement or report-only migration is defined, and residual unenforced rules have owners.

# Quality Gate

1. Enforced rule maps to a real architecture decision.
2. Tool choice fits the language and repo.
3. CI command exists or report-only migration is explicitly timeboxed.
4. Failure examples are documented.
5. Generated and runtime-reflection exceptions are narrow.
6. Public/private export behavior is covered.
7. Ownership and residual unenforced rules are explicit.

# Used By

- architecture-impact-reviewer
- backend-change-builder
- frontend-change-builder
- delivery-release-gate
- ai-code-review-refactor
- quality-test-gate

# Handoff

Hand off to `module-boundary-design` for rule definition, `ci-cd` for pipeline integration, `package-dependency-management` for tool introduction, `consumer-impact-analysis` for public export effects, and `cleanup-deletion-governance` for violation cleanup.

# Completion Criteria

The capability is complete when architecture rules have tool-backed checks, CI or staged enforcement, exceptions, failure examples, ownership, migration path, and residual unenforced rule disclosure.
