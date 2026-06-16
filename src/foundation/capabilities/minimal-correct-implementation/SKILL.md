---
name: minimal-correct-implementation
description: Forces the smallest correct implementation by challenging whether work needs to exist, preferring existing repository code, standard library, native platform features, installed dependencies, and deletion/shrink decisions before adding new code, abstractions, dependencies, files, classes, or configuration.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "117"
changeforge_version: 0.1.0
---

# Mission

Force the smallest implementation that is still correct, secure, reliable, testable, and maintainable. Challenge existence first, then prefer existing repository code, standard library, native platform/framework/database/browser/runtime features, already-installed dependencies, local direct code, deletion, or shrink before adding new code, abstractions, dependencies, files, classes, or configuration.

This capability captures anti-overengineering judgment as professional evidence. It complements normal correctness, security, reliability, architecture, and test review; it never replaces them.

# When To Use

Use when a request says simplest, minimal, smallest correct path, YAGNI, do less, avoid overengineering, avoid a dependency, use stdlib/native, delete, shrink, or review bloat.

Use when a diff adds a dependency, abstraction, interface, abstract class, factory, strategy, generic manager/processor/helper, shared/common/utils code, wrapper, feature flag, mode switch, configuration option, cache, retry, rate limiter, parser, validator, formatter, date/time utility, or multiple files for one local behavior.

Use during skill authoring when a skill, reference, registry rule, hook, or benchmark may duplicate existing rules or widen routing without evidence.

# Do Not Use When

Do not use to weaken trust-boundary input validation, authorization, tenant isolation, security controls, data-loss-preventing error handling, accessibility basics, money/accounting/trading correctness, migration/rollback safety, production reliability evidence, or explicitly requested full behavior.

Do not use file count, line count, or "fewest files" as an absolute rule. File granularity still follows `implementation-structure-design`: object, module, owner, boundary, side-effect, public contract, and test evidence decide whether a new file is justified.

Do not remove meaningful smoke or self-check tests merely because they are small. Minimal validation is acceptable only when risk allows it and the check would fail if the relevant logic broke.

# Stage Fit

Owns implementation-planning, coding, code-review, refactoring, testing, and skill-authoring pressure when complexity may be unnecessary. It is conditional in architecture-design, release-delivery, and documentation-handoff when speculative extension, stale flags, or deletion/shrink evidence affects the stage.

# Non-Negotiable Rules

- Challenge existence before implementation. If the work is speculative, skip it and record why.
- Existing repository code comes before new code. Search owning modules and adjacent patterns before adding a helper or abstraction.
- Standard library comes before custom code for parsing, formatting, date/time, math, HTTP, CSV, JSON, validation, debounce, and simple collection behavior.
- Native platform/framework/database/browser/runtime features come before custom code or dependencies when they express the behavior correctly.
- Already-installed dependencies come before adding a dependency, and only when they are already approved for the owning module.
- Local direct code comes before abstraction. One current implementation does not justify an interface, abstract class, factory, strategy, provider, registry, or plugin point.
- Delete or shrink before adding. Remove dead flexibility, stale fallbacks, duplicate helpers, unused config, and scaffold-for-later when caller and rollback evidence allows it.
- A config option nobody sets is not a requirement. A future extension point without current force is overengineering.
- A wrapper that only delegates is suspect unless it protects a real boundary: auth, retry, timeout, observability, translation, lifecycle, side-effect visibility, or public contract.
- A deliberate shortcut must use `changeforge-shortcut: <simplification>; ceiling: <limit>; upgrade when: <trigger>` and must carry validation evidence and residual risk.
- Minimal checks are allowed for low-risk L1 changes only when they are runnable and meaningful. High-risk paths keep their normal unit, integration, contract, e2e, security, reliability, migration, or rollback evidence.

# Industry Benchmarks

Anchor against YAGNI, "you aren't gonna need it"; Google Engineering Practices complexity review; standard-library-first dependency hygiene; platform-native design; architecture decision records for rejected alternatives; trunk-based small-batch delivery; risk-based testing; NIST SSDF dependency review; and cleanup/deletion governance for stale compatibility behavior.

# Selection Rules

Select with `implementation-structure-design` for new functions, classes, files, directories, shared helpers, wrappers, and placement decisions.

Select with `package-dependency-management` for dependency additions, package-manager changes, lockfile changes, or dependency replacements.

Select with `design-pattern-selection` for interfaces, abstract classes, factories, builders, strategies, registries, providers, singletons, facades, adapters, decorators, or pattern names.

Select with `code-clarity-maintainability` for delete/shrink, simpler control flow, branch collapse, wrapper removal, and complexity-only review.

Select with `cleanup-deletion-governance` for stale fallback, compatibility branch, feature flag, unused config, dead code, or `changeforge-shortcut:` ledger review.

Select with `quality-test-gate` when minimal validation is proposed or when a shortcut, delete, shrink, or dependency avoidance changes test evidence.

# Risk Escalation Rules

Escalate to `security-privacy-gate` when the smaller path touches authentication, authorization, tenant isolation, secrets, dependency supply chain, privacy, injection, or trust-boundary inputs.

Escalate to `data-api-contract-changer` when delete, shrink, local direct code, or shortcut decisions affect API contracts, DTOs, schemas, generated clients, events, validation semantics, compatibility, or migrations.

Escalate to `data-middleware-change-builder` and `reliability-observability-gate` when custom or avoided cache, queue, retry, rate-limit, lock, pool, scheduler, or backpressure behavior can affect production correctness or SLOs.

Escalate to `delivery-release-gate` when minimal release machinery, feature flags, configuration branches, migrations, rollback, or deployment scripts are proposed or removed.

Escalate to `quality-test-gate` when the proposed minimal validation is the only evidence for a non-trivial behavior, deletion, shortcut, or retained abstraction.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| existence-challenge | Request or diff adds work not tied to a current requirement. | Decide whether the behavior needs to exist now. | Requirement link, non-goal, rejected speculative work. | `acceptance-standard-definition`, `agent-execution-discipline` | Do not create scaffold-for-later. |
| reuse-first-implementation | New helper, shared code, service, component, file, class, or wrapper. | Search and reuse owning code before adding structure. | Search scope, candidates, final reuse/new-code decision. | `implementation-structure-design`, `code-review` | Do not use shared/common as ownership escape. |
| stdlib-or-native-replacement | Parser, validator, formatter, cache, rate limit, date, CSV, HTTP, browser, DB, or framework behavior. | Prefer standard library or native feature when correct. | Stdlib/native candidate, mismatch if rejected, validation proof. | `package-dependency-management`, matching builder | Do not replace security/reliability controls with weaker primitives. |
| dependency-avoidance | New dependency, lockfile change, package upgrade for small behavior. | Avoid supply-chain surface unless justified. | Dependency ladder, transitive/CVE/license result, rejected safer alternative. | `package-dependency-management`, `security-privacy-gate` | Do not add convenience packages without audit. |
| abstraction-yagni-review | Interface, abstract class, factory, strategy, builder, provider, registry, mode switch, config option. | Require current force, current variants, and tests. | Current consumers/variants, direct-code alternative, deletion path. | `design-pattern-selection`, `implementation-structure-design` | Do not future-proof without current requirement. |
| delete-shrink-review | Dead code, duplicate helper, stale branch, wrapper-only delegation, branch-heavy control flow. | Remove or collapse complexity without hiding behavior. | Caller search, behavior preservation, before/after validation. | `code-clarity-maintainability`, `cleanup-deletion-governance` | Do not delete public/runtime paths without consumer evidence. |
| shortcut-ledger | Deliberate shortcut or `changeforge-shortcut:` marker. | Accept only bounded, observable shortcuts. | Ceiling, upgrade trigger, validation, owner, residual risk. | `cleanup-deletion-governance`, `quality-test-gate` | Do not treat shortcut notes as safety evidence. |

# Proactive Professional Triggers

- **Signal:** User asks for a cache, rate limiter, parser, validator, date picker, formatter, or similar utility. **Hidden risk:** custom code duplicates stdlib, native, framework, browser, or database behavior and becomes less correct than the primitive it replaces. **Required professional action:** run the simplicity ladder before implementation. **Route to:** `minimal-correct-implementation`, `package-dependency-management`, matching builder. **Evidence required:** stdlib/native/existing candidate review and why the chosen path is smallest correct.
- **Signal:** Diff adds a dependency for small formatting, parsing, debounce, validation, CSV, date, math, or HTTP behavior. **Hidden risk:** supply-chain and maintenance surface grows for behavior already available locally. **Required professional action:** require dependency ladder and security review. **Route to:** `minimal-correct-implementation`, `package-dependency-management`, `security-privacy-gate`. **Evidence required:** rejected stdlib/native/existing dependency alternatives plus CVE/license/transitive result if dependency remains.
- **Signal:** Diff adds an interface, abstract class, factory, strategy, builder, provider, or registry with one implementation. **Hidden risk:** speculative abstraction hides simple logic and creates public API maintenance. **Required professional action:** require direct-code alternative and current variation evidence. **Route to:** `minimal-correct-implementation`, `design-pattern-selection`, `implementation-structure-design`. **Evidence required:** current variants or collapse decision, tests, and deletion path.
- **Signal:** Diff adds `common`, `shared`, `utils`, `helpers`, `manager`, `processor`, or a wrapper that only delegates. **Hidden risk:** ownership is avoided and business logic moves to a dumping ground. **Required professional action:** run reuse and placement review. **Route to:** `minimal-correct-implementation`, `implementation-structure-design`, `code-clarity-maintainability`. **Evidence required:** owner boundary, same-pattern search, and why a wrapper or shared location protects a real boundary.
- **Signal:** Diff adds config, feature flag, mode, kind, strategy switch, or option without current consumers or lifecycle. **Hidden risk:** hidden strategy system and stale configuration debt. **Required professional action:** reject or require lifecycle and cleanup plan. **Route to:** `minimal-correct-implementation`, `configuration-runtime-policy`, `cleanup-deletion-governance`. **Evidence required:** current consumer, owner, expiry, default behavior, tests, and removal trigger.
- **Signal:** Diff adds multiple files for one local behavior without boundary evidence. **Hidden risk:** micro-file sprawl raises navigation cost and hides the owning behavior. **Required professional action:** run file granularity review without forcing fewest files. **Route to:** `minimal-correct-implementation`, `implementation-structure-design`, `code-clarity-maintainability`. **Evidence required:** owner/module/object boundary, keep-in-existing-file alternative, and navigation-cost result.
- **Signal:** Diff adds hand-rolled retry, cache, lock, rate-limit, pool, or scheduler behavior without measured need or primitive review. **Hidden risk:** custom reliability primitives fail under concurrency and edge conditions. **Required professional action:** compare native/runtime/library primitives and route reliability only when production behavior is affected. **Route to:** `minimal-correct-implementation`, `reliability-observability-gate`, `quality-test-gate`. **Evidence required:** primitive comparison, risk-specific tests, and observability or not-production rationale.
- **Signal:** Diff includes a deliberate shortcut without `ceiling:` and `upgrade when:`. **Hidden risk:** accepted shortcut becomes unbounded rot. **Required professional action:** require shortcut ledger repair before handoff. **Route to:** `minimal-correct-implementation`, `cleanup-deletion-governance`, `agent-execution-discipline`. **Evidence required:** repaired marker, owner, validation, residual risk, and next gate.
- **Signal:** Review discovers dead compatibility branch, fallback, unused config, scaffold-for-later, or unused extension point. **Hidden risk:** obsolete complexity stays active and can mask regressions. **Required professional action:** run caller search and delete/shrink plan. **Route to:** `minimal-correct-implementation`, `cleanup-deletion-governance`, `quality-test-gate`. **Evidence required:** searched callers, retained/deleted decision, rollback note, and tests.
- **Signal:** Agent proposes "future-proof" architecture without a current requirement. **Hidden risk:** the architecture solves hypothetical variation while increasing today's maintenance and review cost. **Required professional action:** force current-force decision and rejected direct-code alternative. **Route to:** `minimal-correct-implementation`, `architecture-impact-reviewer`, `design-pattern-selection`. **Evidence required:** current force, reversibility, direct alternative, and why skipped gates remain safe.

# Output Contract

Return a **Minimal Correctness Decision**:

- **Mode selected**:
- **Requirement existence decision**:
- **Simplicity ladder result**:
  - existing repository code:
  - standard library:
  - native/platform feature:
  - installed dependency:
  - local minimal code:
  - new code/dependency/abstraction:
- **Deleted/shrunk items**:
- **New dependency decision**:
- **New abstraction decision**:
- **File/class/config decision**:
- **Shortcut ledger entries**:
- **Validation evidence**:
- **What evidence proves**:
- **What evidence does not prove**:
- **Residual risk**:
- **Next gate**:

# Critical Details

The simplicity ladder is an evidence order, not a blanket ban on new code. A new file, class, dependency, or abstraction is acceptable when it is the first option that remains correct after current requirements, owner boundaries, safety gates, and validation are considered.

Minimal correctness is different from underengineering. It does not weaken authorization, validation, accessibility, money movement, data integrity, migration safety, rollback, observability, or incident diagnostics. When those risks exist, the smallest correct implementation includes the corresponding gate.

Deletion and shrink decisions require caller search and behavior-preservation evidence. A wrapper that protects timeout, retry, auth, logging, translation, lifecycle, or public contract behavior may be retained, but wrapper-only delegation without a boundary should be collapsed.

Shortcut ledgers are temporary ownership records. A `changeforge-shortcut` marker without `ceiling:` and `upgrade when:` is incomplete and must be repaired or converted into a cleanup issue before handoff.

# Evidence Contract

Close only when the output names the selected mode, current requirement or non-goal, files and boundaries searched for reuse, stdlib/native/installed dependency alternatives considered, direct-code alternative, deleted or retained complexity, shortcut ceiling and upgrade trigger when applicable, validation command or review artifact, what the evidence proves and does not prove, residual risk, rollback or deletion note, and next gate.

# Quality Gate

1. Existence was challenged before new work was accepted.
2. Existing repository code, standard library, native platform feature, installed dependency, and local direct code were considered in order.
3. New dependency, abstraction, file, class, directory, or config has current force and placement evidence.
4. One-implementation interface/factory/strategy/abstract class is collapsed or justified by current variation and tests.
5. Wrapper-only delegation is removed or tied to a real boundary.
6. Delete/shrink candidates have caller search and behavior-preservation evidence.
7. Shortcut markers include `ceiling:` and `upgrade when:`.
8. Minimal validation is proportional to risk and does not replace high-risk evidence.
9. Security, reliability, accessibility, auth, data, money, migration, and explicit full-scope requirements are not weakened.

# Reference Loading Policy

- L1 low-risk local change: body only.
- Dependency, abstraction, new structure, or file/class/config decision: load [references/simplicity-ladder.md](references/simplicity-ladder.md).
- Review, audit, AI-generated code bloat, or delete/shrink pass: load [references/complexity-review.md](references/complexity-review.md).
- Deliberate shortcut, shortcut marker, temporary debt, or cleanup ledger: load [references/shortcut-ledger.md](references/shortcut-ledger.md).

# Handoff

Hand off to `implementation-structure-design` when placement or file/class/module boundary is unresolved; `package-dependency-management` when a dependency remains; `design-pattern-selection` when a pattern or abstraction remains; `code-clarity-maintainability` or `refactoring` for shrink/collapse work; `cleanup-deletion-governance` for deletion or shortcut ledger work; `quality-test-gate` for risk-appropriate validation; and `security-privacy-gate` when dependency, secret, auth, privacy, or trust-boundary risk is present.

# Completion Criteria

The capability is complete when the final decision proves the requirement exists, uses the lowest valid ladder level, keeps required safety and validation gates intact, rejects speculative dependency/abstraction/config/file growth, documents any accepted shortcut with ceiling and upgrade trigger, and hands off residual risk to the correct gate.

# Failure Modes

- Speculative work is implemented because it is easy to generate.
- A new dependency replaces a standard-library or native feature.
- A factory, strategy, interface, or abstract base class has one implementation.
- A wrapper only delegates and hides the real boundary.
- Business behavior lands in shared/common/utils.
- Multiple files are created for one local behavior with no owner boundary.
- Stale fallback, compatibility branch, or unused config remains because deletion was not considered.
- A shortcut note lacks ceiling or upgrade trigger.
- Minimal validation is misreported as full evidence for security, money, migration, auth, data, or production reliability.

# Used By

- change-forge-router
- backend-change-builder
- frontend-change-builder
- data-api-contract-changer
- data-middleware-change-builder
- integration-change-builder
- quality-test-gate
- ai-code-review-refactor
- security-privacy-gate
- code-review
- refactoring
- implementation-structure-design
- code-clarity-maintainability
- design-pattern-selection
- package-dependency-management
- cleanup-deletion-governance
