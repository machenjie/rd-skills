# Semantic, Keyboard, and Focus Contracts

Use this Reference only for the named semantic-keyboard-and-focus-contracts decision.

## Decision Rules

- When a control is meaningful to the current task, give it an owned purpose, role, accessible name, state, value, relationship, and update behavior.
- Preserve keyboard entry, exit, tab sequence, composite keys, activation, escape, shortcuts, visible focus, modal containment, return, removal, and restoration to the continuing task.
- Prefer native semantics and verify the accessibility tree and interaction; ARIA guidance is informative and cannot recreate an inaccessible action automatically.
- WCAG 2.2 covers names and focus, while APG supplies keyboard conventions rather than a conformance standard or design system.

Reject a label-only repair that leaves role, state, focus, or action inaccessible. Return the semantic boundary, keyboard and focus approach, and proof limits.
