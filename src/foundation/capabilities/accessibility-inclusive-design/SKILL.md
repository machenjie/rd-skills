---
name: accessibility-inclusive-design
description: "`analysis-agent`/`task-agent`/`review-agent`: use when UI semantics, keyboard/focus, announcements, contrast, motion, alternatives, or scaling changes; skip non-UI work."
---

# accessibility-inclusive-design

## Registry Trigger

**Use when**

- A user-interface change can alter perception, keyboard or switch operation, focus, assistive-technology meaning, motion, scaling, error recovery, or pointer alternatives.

**Do not use when**

- No user interface changes, the task only names a platform accessibility API, or the question is limited to design-system consistency.

## Skill Role

Define cross-platform inclusive interaction semantics and proof obligations. Exclude platform API encyclopedias, visual-system ownership, product-flow ownership, legal conformance certification, and the general testing workflow.

## High-Value Rules

- **Preserve semantic meaning before decoration.** Give every meaningful control an owned role, accessible name, state, value, relationship, and update behavior.
- **Provide a complete keyboard path.** Keep focus order logical, focus indication perceivable, composite navigation conventional, and every action operable without pointer-only gestures.
- **Restore focus to the continuing task.** Define initial, modal return, navigation, deletion, validation, and asynchronous-update focus destinations.
- **Announce consequential dynamic changes once.** Expose loading, completion, error, validation, and changed-state meaning without stealing focus or repeating noise.
- **Keep information independent of color.** Preserve text and non-text contrast under supported themes while adding shape, text, position, or programmatic meaning.
- **Respect user presentation settings.** Support text scaling, reflow, zoom, high contrast, reduced motion, and localization without hiding content or controls.
- **Require an equivalent direct-manipulation path.** Add a non-drag and non-precision alternative for touch, pointer, swipe, or motion-operated outcomes.
- **Combine automated and human evidence.** Pair semantic-tree and contrast checks with manual keyboard, focus, scaling, motion, and assistive-technology journeys.

## Anti-Patterns

- Add an accessibility label while leaving the control's role, state, focus behavior, or action inaccessible.
- Treat passing automation, a screenshot, or one screen reader as proof of accessibility conformance.
- Remove visible focus, error text, or non-color cues because a mouse path still works.

## Stop Conditions

Stop when the intended semantic role, keyboard convention, focus destination, or applicable accessibility requirement is unresolved. Escalate platform-specific implementation to its Domain Skill and conformance claims to the accountable policy or legal owner.

## Output Contract

- accessibility decision with semantic contract keyboard and focus behavior announcements visual and motion alternatives scaling behavior form recovery automated and manual evidence unverified scope and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [inclusive interaction contracts](references/inclusive-interaction-contracts.md) | targeted | Semantics keyboard focus contrast scaling touch alternatives or proof expectations remain open | Current product and platform contracts already determine the affected inclusive interaction | analysis-agent, task-agent, review-agent | selected-approach, proof-limit |
