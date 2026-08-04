---
name: code-clarity-maintainability
description: "`analysis-agent`/`task-agent`/`review-agent`: use when changed flow, naming, or navigation hides obligations; skip placement, API-contract, language, or performance decisions."
---

# code-clarity-maintainability

## Registry Trigger

**Use when**

- Changed main or exceptional flow is hard to trace because branches, helpers, comments, or simplification obscure outcomes, cleanup, cancellation, or side effects.
- Naming, conditions, split/merge navigation, or test readability makes the owning rule, next change, or deletion path ambiguous.

**Do not use when**

- The unresolved decision is file, object, module, signature, or public-contract placement; use the owning structure or API capability.
- The work is behavior-preserving movement, language-specific semantics, or runtime performance with no remaining clarity decision.

## Skill Role

Make changed behavior and obligations traceable from its public entry point. Exclude placement, module/API ownership, language semantics, runtime safety, and behavior-preserving movement.

## High-Value Rules

- Trace the affected entry point to each material terminal outcome. Validation, denial, fallback, retry, cancellation, cleanup, and response obligations stay visible where they can alter the result.
- When changing guards, extraction, inlining, or branch shape, verify evaluation order, short-circuiting, resource release, cancellation, and visible side-effect order.
- Names distinguish semantic role, state, unit, authority, and failure meaning; they do not turn a domain rule or public failure into a vague helper or mode.
- Extract or name a condition when it separates an owned decision; keep direct code when extraction would hide effects, introduce indirection, or split one cohesive obligation.
- Comments record non-obvious contract, invariant, compatibility, or operational reason; tests assert public behavior and the regression mechanism rather than private call shape.
- Use complexity, length, and file-count signals to select inspection scope; approve only from traceability and preserved obligations, not a generic threshold.
- A split or merge preserves a discoverable entry point, one owner per decision, visible public/test/effect boundaries, and an obvious location for the next related change or deletion.

## Anti-Patterns

- A guard or early return bypasses cleanup, audit, rollback, or response work.
- A boolean, mode, negated condition, or magic value hides authority or state semantics at the call site.
- Tiny helpers or files force traversal across vague wrappers to understand one decision.
- A shorter diff or lower metric is treated as clarity proof while behavior, ownership, or test intent becomes harder to see.

## Stop Conditions

- Route placement or public-contract ownership to `implementation-structure-design`, `module-boundary-design`, or the relevant API capability.
- Route behavior-preserving movement to `refactoring`, language semantics to `language-idiom-enforcement`, and runtime cost or safety to `language-performance-safety`.

## Output Contract

- code-clarity decision with obscured path preserved obligations selected move rejected simplification public-behavior proof evidence limits and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | A code-clarity choice between guard extraction inline split merge or direct flow remains unresolved | The code-clarity change is a direct naming or comment correction with no competing flow or navigation move | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | A code-clarity change spans exceptional paths, cleanup, side effects, or split-merge navigation and requires obligation-to-outcome traceability | The code-clarity obligation and affected terminal outcomes are explicit in the changed path | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
