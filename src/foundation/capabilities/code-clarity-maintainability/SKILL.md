---
name: code-clarity-maintainability
description: Reviews implementation readability and maintainability by checking main-flow clarity, control-flow shape, function size, nesting, naming, comments, fallback isolation, cognitive complexity, and future change navigation without duplicating placement or module-boundary design.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "105"
changeforge_version: 0.1.0
---

# Mission

Make code readable, navigable, and maintainable for future engineers by keeping the main path visible, isolating exceptional paths, limiting cognitive complexity, naming concepts precisely, and ensuring a maintainer can locate the responsibility, extension point, and deletion path without reverse-engineering a working-but-opaque implementation.

This capability judges clarity as an engineering quality gate, not style preference. Code that can run but cannot be safely read, changed, tested, or deleted is incomplete.

# When To Use

Use when code is written, reviewed, generated, or refactored and any readability or maintainability signal appears:

- The happy path is buried under validation, fallback, compatibility, retries, logging, mapping, or side effects.
- A function is long, deeply nested, branch-heavy, or hard to name.
- A class, object, helper, component, service, or test reads as a procedural pile.
- Conditions are complex, repeated, weakly named, or packed into boolean expressions.
- Names are vague (`manager`, `processor`, `helper`, `data`, `result`, `mode`, `kind`) or hide domain concepts.
- Comments restate what the code does instead of explaining why a branch, fallback, invariant, or tradeoff exists.
- Maintenance would require changing multiple unrelated places for a small requirement.
- AI-generated code creates a readable-looking wrapper around unclear flow, invented abstractions, or excessive branching.
- Excessive file splitting, one-function files, tiny helper file patterns, trivial helper files, or micro-file sprawl make one cohesive behavior harder to read or change.
- Reckless file merge, over-merged owner files, or file count reduction without boundary evidence hide responsibility, side effects, or public behavior.

# Do Not Use When

Do not use for pure formatting, lint-only cleanup, or personal style preference where the code is already clear and locally idiomatic.

Do not use this as the primary placement or ownership designer. Use `implementation-structure-design` for function/class/file ownership and `module-boundary-design` for directory/module boundaries. This capability evaluates whether the resulting code is understandable and maintainable.

# Non-Negotiable Rules

- Main flow comes first. Validation, exceptional paths, fallback, compatibility, logging, metrics, and cleanup must not obscure the normal behavior.
- Prefer guard clauses and named branch extraction over deep nesting when local language convention supports it.
- A function must not mix validation, business decision, mutation, I/O, mapping, logging, and fallback handling without an explicit orchestration reason.
- Complex conditions must be named as domain or policy concepts before they are repeated or nested.
- Magic numbers, magic strings, and mode names must have domain names or constants with ownership.
- Boolean parameters, vague `mode` or `kind` switches, and weakly typed bags require signature review with `implementation-structure-design`.
- Comments explain why, contract, invariant, compatibility, security, performance, fallback, or external-system quirks. They must not narrate obvious code.
- If comments are needed to explain confusing structure, first consider renaming, extraction, parameter object, or simpler control flow.
- Cognitive complexity is a maintenance risk. Functions above the local tool threshold, or obviously hard to trace without a tool, require decomposition or documented justification.
- Readability must preserve change locality: a small rule change should have one owning location unless the product behavior truly crosses boundaries.
- Complexity-only reviews must identify delete, shrink, reuse, stdlib/native, existing-code, and YAGNI opportunities before proposing rewrites. A net line-count reduction is required only when the requested review is explicitly complexity-only; normal feature, fix, and safety reviews optimize for correct maintainable behavior, not arbitrary fewer lines.
- Excessive file splitting is a readability and maintainability defect when it creates one-function file, trivial helper file, pass-through glue, or navigation cost regression without a real boundary. Use anti-fragmentation evidence from file granularity review when deciding whether to keep in existing file, merge back, or split by a real boundary.
- File count reduction is not automatically a clarity improvement; excessive splitting, excessive merging, reckless file merge, and small file merge without boundary evidence are maintainability defects.
- Clarity review must assess navigation cost, next-change location, and main-flow readability before and after a file split or merge.
- If understanding one business decision requires jumping through multiple vague tiny helpers or files, the structure has a clarity defect.
- If reducing file count mixes responsibilities, hides side effects, erases a public boundary, or creates a lost small-file boundary, the merge has a clarity defect.

# Industry Benchmarks

Anchor against: Google Engineering Practices readability review; SonarSource cognitive complexity; Martin Fowler refactoring catalog for Extract Function, Introduce Parameter Object, Replace Conditional with Polymorphism, and Decompose Conditional; Clean Code guidance for intention-revealing names and comments that explain why; Domain-Driven Design ubiquitous language for domain names; Testing Library and xUnit guidance for behavior-named tests; architecture review practice that treats change locality and deletion path as maintainability indicators.

# Selection Rules

Select this capability when the primary review question is whether code is easy to read, modify, extend, test, and delete.

Use with:

- `implementation-structure-design` when clarity problems come from oversized functions, weak signatures, mixed responsibilities, object split decisions, or side-effect pollution.
- `module-boundary-design` when clarity problems come from directories with multiple owners, weak public APIs, shared/common dumping grounds, or poor change locality.
- `refactoring` when the clarity issue must be fixed while preserving behavior.
- `code-review` and `ai-code-review-refactor` when completed or generated code needs severity-classified maintainability findings.
- `quality-test-gate` when test code readability, fixture ownership, or behavior-oriented assertion structure is unclear.
- `language-idiom-enforcement` when clarity depends on language-specific idioms, visibility, or public API conventions.

# Risk Escalation Rules

Escalate to `refactoring` when the code is too hard to review without behavior-preserving decomposition.

Escalate to `implementation-structure-design` when unclear flow reveals mixed file, object, function, signature, collaborator, lifecycle, or side-effect responsibility.

Escalate to `module-boundary-design` when a small requirement spreads across unrelated modules, shared utilities, or public APIs.

Escalate to `quality-test-gate` when tests are hard to understand, over-mock internals, depend on private helpers, or hide fixture ownership.

Escalate to `agent-execution-discipline` when an agent claims clarity is improved without before/after evidence, same-pattern scan, or validation output.

# Reference Loading Policy

Current mode is inline-only: this capability has no deep reference files today, so this `SKILL.md` contains the active code clarity, maintainability, and split/merge readability rules.

If deep references are added later, load them only for L3+ work, AI-generated or refactored code with unclear main flow, high cognitive complexity, file split/merge risk, hidden side effects, test clarity or private-helper pressure, or cross-module change locality risk.

Do not load deep references for L1/L2 local clarity edits where the inline output contract can state main-flow readability, owning location, deletion path, test clarity, rejected simplifications, and validation evidence.

# Critical Details

## Future Maintainer Review Steps

Review as the next engineer who must change or delete this code:

1. Read only the public entry point and ask whether the normal path is visible.
2. Identify the single owner of the rule, state, side effect, fallback, and error behavior.
3. Name the next related change and the file/function where it should land.
4. Name the deletion path for compatibility branches, feature flags, dead code, old adapters, stale fixtures, or temporary fallbacks.
5. Check that tests describe public behavior and fixture ownership rather than private helper structure.
6. State what simpler naming, extraction, parameter object, or side-effect separation was rejected and why.

## Main Flow Review

Read the code once as a future maintainer would. The normal path should be visible before exceptional paths. Push denial, validation, fallback, compatibility, retry, and cleanup branches to named guards or helpers when doing so improves local readability and does not hide side effects.

Reject flow that requires a reader to jump through several vague helpers to understand the one business decision being made.

Check file navigation cost as part of the main-flow read. A split is a clarity improvement only when the entry point still tells the story and helpers have names, ownership, and boundaries that reduce cognitive load. A merge is a clarity improvement only when the owner stays cohesive and side effects, public contracts, and test boundaries remain visible. Reject split/merge changes that make the main behavior require more file jumps, create a larger mixed-responsibility file, or obscure the next-change location.

## Control-Flow Review

Nested conditions, repeated boolean expressions, long switch/case blocks, and `mode` or `kind` branches are clarity signals. Decide whether they are local readability issues, missing policy/strategy objects, missing state-machine modeling, or missing domain names.

## Naming And Comments

Names should make the code mostly self-explanatory. Comments are still required for non-obvious intent, invariants, compatibility branches, fallback behavior, security decisions, performance tradeoffs, external API quirks, and regression tests. A comment that repeats syntax is a defect; a comment that explains why a surprising branch exists is evidence.

## Maintainability And Change Navigation

For non-trivial changes, identify where the next related change would go and how obsolete code would be deleted. If the answer is "several unrelated modules" or "search for all callers and guess," clarity and change locality are not acceptable.

Next-change location and deletion path are mandatory professional evidence, not optional commentary. A compatibility branch without an expiry owner, a feature flag without cleanup path, or a fallback without removal condition is maintainability debt.

Assess navigation cost before and after file splits and merges. The next-change location must remain obvious after decomposition or consolidation. If a maintainer must inspect multiple tiny policy/helper/adapter files to place a small cohesive rule, the split is a maintainability regression unless those files represent real independent boundaries. If a maintainer must inspect one broad owner file that now hides adapter, policy, value-object, and orchestration responsibilities, the merge is a maintainability regression even though file count decreased.

## Test Clarity Risks

Tests are unclear when they over-mock private internals, assert helper call order instead of public behavior, hide fixture ownership in broad shared helpers, or update snapshots without explaining the protected behavior. A regression test must state the bug condition it proves; a fixture must have an owner and a reason to change; a mock must represent an external boundary, not private implementation trivia.

# Failure Modes

- A happy path is buried under nested validation, retries, metrics, mapping, and fallback code.
- A long function is split into poorly named helpers that make the call chain harder to follow.
- A complex condition is copied three times instead of named once as a policy or domain concept.
- A boolean flag silently changes behavior in a way callers cannot read at the call site.
- A `mode` or `kind` switch becomes a hidden strategy system without explicit extension rules.
- A shared test helper contains business fixture logic from one module and becomes a dumping ground.
- Tests pass by over-mocking private helper calls, so the public behavior can regress while implementation-shaped assertions stay green.
- A fixture factory is shared across unrelated modules without an owner, causing hidden coupling and broad test churn.
- Comments narrate assignments and loops while missing the compatibility or security reason for a branch.
- A small requirement changes shared utilities, feature modules, tests, and adapters because no owner is clear.
- Excessive file split turns a cohesive flow into micro-file sprawl.
- Reckless file merge turns clear small-boundary files into one mixed-responsibility owner.
- A one-function file, trivial helper file, or pass-through glue file makes the reader jump without improving ownership, testing, or public contract clarity.
- Navigation cost regression hides the next-change location after a split.
- File count reduction hides side effects, public behavior boundaries, or dependency direction.

# Output Contract

Return a Code Clarity Maintainability Review with:

- **Main flow assessment**: whether the primary behavior is visible, and which branches obscure it.
- **Control-flow assessment**: nesting, branch count, switch/case, fallback, compatibility, and guard-clause decisions.
- **Function size and purpose assessment**: oversized or multi-purpose functions; decomposition decision or justification.
- **Condition naming assessment**: complex repeated conditions, magic values, and missing domain names.
- **Signature readability assessment**: boolean traps, weakly typed bags, vague modes, and parameter object needs.
- **Comment quality assessment**: comments required, comments rejected, and places where naming/extraction should replace comments.
- **Change navigation assessment**: owning location for the next related change and deletion path for obsolete behavior.
- **File navigation cost assessment**: files a maintainer must open before/after the change, and whether the split or merge improves or regresses readability.
- **Split/merge readability decision**: keep together, keep in existing file, merge back, split by real boundary, or leave split as-is; include file granularity, small file merge, merge restraint, anti-fragmentation rationale, and the split merge decision evidence.
- **Complexity Delete List**: for complexity-only review, findings tagged `delete`, `shrink`, `stdlib`, `native`, `existing-code`, or `yagni`, with validation impact and any safety reason a line-count reduction is not accepted.
- **Next-change location before/after**: whether the next adjacent requirement has a clearer owner file/function/module after decomposition or consolidation.
- **Main-flow readability before/after**: whether the primary behavior became easier to read, stayed no worse, or regressed.
- **Next-change location**: the exact owner file/function/module where the next adjacent requirement should land.
- **Deletion path**: removal condition, owner, and validation for obsolete compatibility branches, flags, fallbacks, or temporary code.
- **Test clarity assessment**: whether tests express public behavior, fixture ownership, regression purpose, and what is over-mocked or private-internal.
- **Rejected split/merge simplification**: split or merge shortcuts considered, why file count reduction/increase alone was rejected, and why the accepted structure is clearer.
- **Rejected simplifications**: simpler structures considered and why they were not appropriate.
- **Validation evidence**: formatter/linter/tests/static-analysis or review evidence used to support the judgment.

# Evidence Contract

Close a clarity review only when it states the **mode selected** for coding, review,
refactoring, or testing, boundaries inspected, professional judgment on readability and
change locality, reuse or placement rationale when structure is affected, behavior
preservation for clarity refactors, validation evidence, what evidence proves and does not
prove, command output or review artifact with exit code when available, residual risk, and the
next gate or handoff.

# Quality Gate

1. The normal path is readable without tracing unrelated fallback, compatibility, or side-effect details.
2. Deep nesting, long switch/case blocks, and repeated complex conditions are decomposed, named, or justified.
3. Each non-trivial function has one readable purpose or an explicit orchestration reason.
4. Boolean flags, vague modes, weakly typed bags, and unclear return contracts are escalated for signature review.
5. Magic values have domain names and owners.
6. Comments explain why, contract, invariant, risk, or tradeoff; no comments merely restate obvious code.
7. The next related change has an obvious owning location.
8. Obsolete behavior has a plausible deletion path when compatibility or feature flags are introduced.
9. Test code reads as behavior evidence and does not depend on private helper structure.
10. Any clarity refactor preserves behavior with appropriate test evidence.
11. Fixture ownership and regression purpose are explicit for non-trivial tests.
12. Private internals are not over-mocked unless no public boundary can expose the behavior and that limitation is stated.
13. File splits do not make the main flow harder to read than before the split.
14. One-function file, trivial helper file, pass-through glue, and micro-file sprawl are rejected when they increase navigation cost without a real boundary.
15. File merges do not make the owner file mix responsibilities, hide side effects, or erase public/test boundaries.
16. The next related change has an obvious owner after every split or merge.
17. File count changes produce owner clarity or navigation clarity, not cosmetic neatness.

# Used By

- backend-change-builder
- frontend-change-builder
- ai-code-review-refactor
- quality-test-gate
- change-forge-router

# Handoff

Hand off to `implementation-structure-design` for file, function, object, signature, collaborator, or side-effect ownership decisions; `module-boundary-design` for module ownership and change locality problems; `refactoring` for behavior-preserving cleanup; `code-review` or `ai-code-review-refactor` for severity-classified findings; and `quality-test-gate` for test readability and fixture ownership gaps.

# Completion Criteria

The capability is complete when a maintainer can read the main flow, locate the owning responsibility, understand exceptional paths and comments, see how tests prove behavior, identify where the next change or deletion belongs, and see that any file split or merge improved owner clarity or navigation clarity without hiding responsibilities, side effects, public contracts, or test boundaries.
