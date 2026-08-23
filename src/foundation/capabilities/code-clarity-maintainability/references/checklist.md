# Changed Flow Checklist

This checklist applies the root traceability contract to the changed path without expanding into placement, architecture, or generic evidence governance.

- Start at the affected public entry point and list the material terminal outcomes.
- Mark branches that can deny, retry, fall back, cancel, clean up, mutate, emit, or respond.
- Compare evaluation order, short-circuit behavior, resource release, and externally visible effects before and after the clarity move.
- Name the authority, state, unit, and failure meaning behind conditions, modes, defaults, and magic values.
- For extraction, inline, split, or merge work, record owner, inspected paths, import/export impact, public/test seam, next-change location, and deletion path. Keep it in the current diff or review unless repository policy requires a separate artifact.
- Retain comments that explain a non-obvious contract, invariant, compatibility rule, operational reason, or regression mechanism.
- Use tests that assert public outcomes and the affected failure mechanism rather than private helper shape or mock-call order.
- State limits from dynamic callers, generated code, reflection, unexercised exits, or external behavior that the inspected path does not establish.

## Anti-Patterns

- A guard or early return bypasses cleanup, audit, rollback, or response work.
- A boolean, mode, negated condition, or magic value hides authority or state semantics at the call site.
- Tiny helpers or files force traversal across vague wrappers to understand one decision.
- A shorter diff or lower metric is treated as clarity proof while behavior, ownership, or test intent becomes harder to see.
