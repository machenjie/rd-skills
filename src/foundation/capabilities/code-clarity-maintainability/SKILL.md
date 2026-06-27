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
- A function, class, object, helper, component, service, or test is long, deeply nested, branch-heavy, procedural, or hard to name.
- Conditions, names, comments, boolean flags, `mode`/`kind` switches, or magic values hide domain concepts or policy decisions.
- Maintenance would require changing unrelated places, guessing the next-change location, or retaining obsolete code without a deletion path.
- AI-generated code, excessive split/merge churn, one-function files, tiny helper files, or file-count reduction make cohesive behavior harder to read or change.

# Do Not Use When

Do not use for pure formatting, lint-only cleanup, or personal style preference where the code is already clear and locally idiomatic.

Do not use this as the primary placement or ownership designer. Use `implementation-structure-design` for function/class/file ownership and `module-boundary-design` for directory/module boundaries. This capability evaluates whether the resulting code is understandable and maintainable.

# Stage Fit

Owns coding, code-review, refactoring, and testing readability slices. During implementation-planning, confirm the selected owner, graph, and file shape leave a readable main flow. During coding, keep the normal path, branch names, and side effects visible. During code-review/refactoring, verify behavior preservation, navigation cost before/after, next-change location, deletion path, and validation evidence. During testing, ensure tests read as public behavior evidence rather than private implementation scripts. At handoff, disclose stale source, repository graph, project memory, or execution trajectory signals instead of treating them as current proof.

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
- File split or merge changes must improve owner clarity or navigation clarity, not merely change line count or file count.
- Reject one-function files, trivial helper files, pass-through glue, micro-file sprawl, reckless file merge, lost small-file boundary, and merges that hide side effects, public behavior, dependency direction, or test boundaries.
- If one business decision requires jumping through vague tiny helpers or one broad mixed-responsibility file, the structure has a clarity defect.

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

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities / gates | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| main-flow clarity review | Happy path is buried under fallback, retry, logging, mapping, or side effects. | Make primary behavior visible and isolate exceptional paths without hiding side effects. | Entry point inspected, obscuring branches named, guard/extraction decision, review artifact or validation command. | `implementation-structure-design`, `language-idiom-enforcement` | Skip for formatter-only or lint-only edits with no readability risk. |
| control and naming cleanup | Repeated condition, deep nesting, magic value, vague name, boolean flag, or `mode` switch. | Name the domain policy and simplify control flow before adding abstractions. | Condition inventory, owner concept, before/after flow, rejected abstraction if direct naming is enough. | `refactoring`, `design-pattern-selection` | Skip speculative strategy/interface creation without current variants. |
| split/merge navigation review | File split, file merge, one-function file, tiny helper, or file-count reduction. | Prove owner clarity, public/test boundary, and navigation cost improve or stay no worse. | Files opened before/after, owner boundary, import/export impact, next-change location, deletion path. | `implementation-structure-design`, `module-boundary-design`, `refactoring` | Skip line-count-only split or merge decisions. |
| test clarity review | Tests assert private helpers, mock calls, snapshots, or shared fixture bags. | Make tests readable public-behavior evidence with owned fixtures. | Public behavior boundary, fixture owner, assertion purpose, what the evidence proves and does not prove. | `quality-test-gate`, `testability-seam-design` | Skip private-helper assertions unless no public seam can expose the behavior and the limit is stated. |
| agent or AI maintainability review | Generated code looks plausible but hides unclear flow, wrappers, broad helpers, or stale proof. | Require same-pattern scan, reuse/placement rationale, graph/memory/trajectory freshness, and validation evidence. | Changed paths, source inspected, current graph/memory accepted or rejected, command output, residual risk. | `ai-code-review-refactor`, `agent-execution-discipline` | Skip approval from final-diff readability alone. |

# Proactive Professional Triggers

- **Signal:** A review says code is "readable enough" without naming the public entry point and normal path. **Hidden risk:** hidden fallback, retry, logging, or side-effect branches can leave the behavior future maintainers must change unverified. **Required professional action:** run a main-flow pass and name any branch that obscures the primary behavior. **Route to:** `code-clarity-maintainability`, `implementation-structure-design`. **Evidence required:** entry point, obscuring branches, guard/extraction decision, and validation or review artifact.
- **Signal:** A diff splits or merges files and the rationale is line count, file count, or "cleanup". **Hidden risk:** hidden navigation cost, public boundaries, side effects, lost small-file boundary, or test ownership can regress while the diff looks simpler. **Required professional action:** require file granularity and split/merge readability evidence before acceptance. **Route to:** `implementation-structure-design`, `module-boundary-design`, `refactoring`. **Evidence required:** files opened before/after, owner boundary, import/export impact, next-change location, and behavior-preservation proof.
- **Signal:** A repeated condition, boolean flag, `mode`, `kind`, or magic value controls business behavior. **Hidden risk:** an unnamed policy becomes a hidden strategy system that callers cannot read at the call site. **Required professional action:** name the policy or route to signature/pattern review before adding branches. **Route to:** `implementation-structure-design`, `design-pattern-selection`, `state-machine-modeling`. **Evidence required:** condition inventory, selected domain name, current variants, rejected abstraction, and tests or review proof.
- **Signal:** Tests read as mock-call checks, snapshots, private helper calls, or shared fixture setup. **Hidden risk:** tests stop documenting public behavior and preserve implementation shape instead of user-visible outcomes. **Required professional action:** move the assertion to a public behavior boundary or document why no public seam exists. **Route to:** `quality-test-gate`, `testability-seam-design`. **Evidence required:** public behavior assertion, fixture owner, regression purpose, and evidence limits.
- **Signal:** An agent or AI patch claims clarity improved after edits without source freshness, same-pattern scan, or command output. **Hidden risk:** a clean-looking diff can approve stale assumptions, missed adjacent cases, or unverified behavior preservation. **Required professional action:** require execution discipline closure before handoff. **Route to:** `agent-execution-discipline`, `ai-code-review-refactor`, `validation-broker`. **Evidence required:** changed paths, current source/graph/memory/trajectory status, validation command with exit code or not-run disclosure, and residual risk.
- **Signal:** A repository graph, project-memory note, benchmark/report, or previous review is used to approve a clarity refactor, split/merge, helper extraction, or comment cleanup without rereading current source and tests. **Hidden risk:** stale evidence can hide changed callers, new side effects, or degraded navigation after the final edit. **Required professional action:** reconcile graph, memory, execution order, and validation freshness before approval. **Route to:** `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, `validation-broker`. **Evidence required:** accepted/rejected prior claim, current source paths, changed-file map, command or review artifact, what evidence proves/does not prove, and residual risk.

# Risk Escalation Rules

Escalate to `refactoring` when the code is too hard to review without behavior-preserving decomposition.

Escalate to `implementation-structure-design` when unclear flow reveals mixed file, object, function, signature, collaborator, lifecycle, or side-effect responsibility.

Escalate to `module-boundary-design` when a small requirement spreads across unrelated modules, shared utilities, or public APIs.

Escalate to `quality-test-gate` when tests are hard to understand, over-mock internals, depend on private helpers, or hide fixture ownership.

Escalate to `agent-execution-discipline` when an agent claims clarity is improved without before/after evidence, same-pattern scan, or validation output.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 clarity routing, mode selection, output, and gates. Use inline-only mode for L1/L2 local readability decisions where the output contract can state main-flow readability, owning location, deletion path, test clarity, rejected simplifications, and validation evidence.

Read [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete clarity, split/merge, comment, or test readability decision. Read [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for L3+ work, AI-generated or refactored code with unclear main flow, high cognitive complexity, file split/merge risk, hidden side effects, test clarity/private-helper pressure, or cross-module change locality risk. Read [references/evidence-patterns.md](references/evidence-patterns.md) when closure depends on repository graph, project memory, execution trajectory, validation freshness, command output, review artifacts, or what clarity evidence proves versus does not prove.

Do not load deep references for L1/L2 local clarity edits where the inline output contract is enough.

# Critical Details

## Future Maintainer Review Steps

Review as the next engineer who must change or delete this code: read the public entry point; confirm the normal path is visible; identify the owner of the rule, state, side effect, fallback, error behavior, next related change, and deletion path; check that tests describe public behavior and fixture ownership; and state what simpler naming, extraction, parameter object, split/merge, or side-effect separation was rejected and why.

## Main Flow Review

Read the code once as a future maintainer would. The normal path should be visible before exceptional paths; denial, validation, fallback, compatibility, retry, and cleanup branches should be named or isolated only when that improves local readability without hiding side effects. Reject flow that requires several vague helpers to understand one business decision. Check navigation cost: a split helps only when the entry point still tells the story, and a merge helps only when the owner stays cohesive and side effects, public contracts, and test boundaries remain visible.

## Control-Flow Review

Nested conditions, repeated boolean expressions, long switch/case blocks, and `mode` or `kind` branches are clarity signals. Decide whether they are local readability issues, missing policy/strategy objects, missing state-machine modeling, or missing domain names.

## Naming And Comments

Names should make the code mostly self-explanatory. Comments are still required for non-obvious intent, invariants, compatibility branches, fallback behavior, security decisions, performance tradeoffs, external API quirks, and regression tests. A comment that repeats syntax is a defect; a comment that explains why a surprising branch exists is evidence.

## Maintainability And Change Navigation

For non-trivial changes, identify where the next related change would go and how obsolete code would be deleted. If the answer is "several unrelated modules" or "search for all callers and guess," clarity and change locality are not acceptable. Navigation cost must remain obvious after decomposition or consolidation; multiple tiny policy/helper/adapter files or one broad mixed owner are regressions unless they prove real independent boundaries.

## Test Clarity Risks

Tests are unclear when they over-mock private internals, assert helper call order instead of public behavior, hide fixture ownership in broad shared helpers, or update snapshots without explaining the protected behavior. A regression test must state the bug condition it proves; a fixture must have an owner and a reason to change; a mock must represent an external boundary, not private implementation trivia.

# Failure Modes

- **Buried main path:** A happy path is buried under nested validation, retries, metrics, mapping, and fallback code.
- **Vague helper chain:** A long function is split into poorly named helpers that make the call chain harder to follow.
- **Unnamed policy branch:** A complex condition, boolean flag, `mode`, or `kind` switch is copied instead of named as a policy or domain concept.
- **Narrative comments:** Comments narrate assignments and loops while missing the compatibility, security, performance, or fallback reason for a branch.
- **Ownerless change path:** A small requirement changes shared utilities, feature modules, tests, and adapters because no owner is clear.
- **Private-helper test lock-in:** Tests pass by over-mocking private helper calls or shared fixture bags while public behavior can regress.
- **Micro-file sprawl:** Excessive split turns a cohesive flow into micro-file sprawl or hides the next-change location.
- **Mixed-responsibility merge:** Reckless file merge turns clear small-boundary files into one mixed-responsibility owner.
- **Pass-through glue:** A one-function file, trivial helper file, pass-through glue file, or file-count reduction hides ownership, side effects, public behavior, or dependency direction.

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
- **Main-flow readability before/after**: whether the primary behavior became easier to read, stayed no worse, or regressed.
- **Next-change location before/after**: the exact owner file/function/module for the next adjacent requirement and whether it became clearer.
- **Deletion path**: removal condition, owner, and validation for obsolete compatibility branches, flags, fallbacks, or temporary code.
- **Test clarity assessment**: whether tests express public behavior, fixture ownership, regression purpose, and what is over-mocked or private-internal.
- **Rejected split/merge simplification**: split or merge shortcuts considered, why file count reduction/increase alone was rejected, and why the accepted structure is clearer.
- **Rejected simplifications**: simpler structures considered and why they were not appropriate.
- **Validation evidence**: formatter/linter/tests/static-analysis or review evidence used to support the judgment.

# Evidence Contract

Close a clarity review only when these answers are concrete:

- **Mode selected and judgment**: coding, code-review, refactoring, testing, split/merge, or agent/AI maintainability mode plus approved, blocked, or route-to-next-gate decision.
- **Boundaries inspected**: public entry point, callers, tests, fixtures, side effects, comments, file split/merge paths, imports/exports, repository graph, project memory, and execution trajectory accepted or rejected for freshness.
- **Reuse / placement rationale**: why naming, extraction, split, merge, direct code, or owner placement is clearer than rejected alternatives.
- **Behavior preservation**: public outputs, errors, ordering, side effects, test boundaries, and contracts preserved for clarity refactors, or explicit not-a-refactor disclosure.
- **Validation evidence**: formatter, linter, test, static-analysis, diff review, or validator command with exit code when run, or not-run disclosure with owner.
- **What evidence proves / what evidence does not prove**: state the covered paths and the unproven consumers, dynamic calls, production scale, browser/runtime differences, or stale memory limits.
- **Residual risk and next gate**: accepted gap, stale or partial proof, owner, and handoff to `implementation-structure-design`, `refactoring`, `quality-test-gate`, `ai-code-review-refactor`, or `agent-execution-discipline`.

# Quality Gate

1. The normal path is readable without tracing unrelated fallback, compatibility, or side-effect details.
2. Deep nesting, long switch/case blocks, repeated complex conditions, magic values, and vague names are decomposed, named, or justified.
3. Each non-trivial function has one readable purpose or an explicit orchestration reason.
4. Boolean flags, vague modes, weak bags, and unclear return contracts are escalated for signature review.
5. Comments explain why, contract, invariant, risk, or tradeoff; no comment merely restates obvious code.
6. The next related change has an obvious owning location and obsolete behavior has a deletion path.
7. Test code reads as behavior evidence, owns fixtures, states regression purpose, and avoids private-helper coupling unless the limitation is explicit.
8. Any clarity refactor preserves behavior with appropriate test or review evidence.
9. File splits do not make the main flow harder to read than before the split.
10. One-function files, trivial helper files, pass-through glue, and micro-file sprawl are rejected when they increase navigation cost without a real boundary.
11. File merges do not mix responsibilities, hide side effects, erase public/test boundaries, or break dependency direction.
12. File count changes produce owner clarity or navigation clarity, not cosmetic neatness.

# Used By

`backend-change-builder`; `frontend-change-builder`; `ai-code-review-refactor`; `quality-test-gate`; `change-forge-router`.

# Handoff

Hand off to `implementation-structure-design` for file, function, object, signature, collaborator, or side-effect ownership decisions; `module-boundary-design` for module ownership and change locality problems; `refactoring` for behavior-preserving cleanup; `code-review` or `ai-code-review-refactor` for severity-classified findings; and `quality-test-gate` for test readability and fixture ownership gaps.

# Completion Criteria

The capability is complete when a maintainer can read the main flow, locate the owning responsibility, understand exceptional paths and comments, see how tests prove behavior, identify where the next change or deletion belongs, and see that any file split or merge improved owner clarity or navigation clarity without hiding responsibilities, side effects, public contracts, or test boundaries.
