---
name: accessibility-inclusive-design
description: "`analysis-agent`/`task-agent`/`review-agent`: use when UI semantics, keyboard/focus, announcements, contrast, motion, alternatives, or scaling changes; skip non-UI work."
---

# accessibility-inclusive-design

## Registry Trigger

**Use when**

- A UI change alters perception, keyboard or switch operation, focus, assistive-technology meaning, motion, scaling, recovery, or pointer alternatives.

**Do not use when**

- No UI changes, only a platform accessibility API, or only design-system consistency.

## Skill Role

Own cross-platform inclusive interaction meaning and proof; exclude platform encyclopedias, visual or product-flow ownership, legal certification, and general testing workflow.

## High-Value Rules

- Preserve meaning, operability, and focus on the continuing task.
- Preserve presentation and direct-manipulation alternatives under supported settings.
- Bind accessibility claims to current automated and human evidence.

## Anti-Patterns

- Do not substitute a local scan, screenshot, or one assistive-technology run for the inclusive interaction contract.

## Stop Conditions

Stop on unresolved semantic role, keyboard convention, focus destination, requirement authority, or representative proof; return platform or conformance ownership.

## Output Contract

- accessibility decision with semantic contract keyboard and focus behavior announcements visual and motion alternatives scaling behavior form recovery automated and manual evidence unverified scope and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [semantic keyboard and focus contracts](references/semantic-keyboard-and-focus-contracts.md) | targeted | Semantic meaning, keyboard operation, or focus behavior remains open | Current semantic, keyboard, and focus contracts fix the changed behavior | analysis-agent, task-agent, review-agent | selected-approach, boundary-decision, proof-limit |
| [announcements and form recovery contracts](references/announcements-and-form-recovery-contracts.md) | targeted | Announcement, status, validation, or form-recovery behavior remains open | Current announcement and form-recovery contract fixes the changed behavior | analysis-agent, task-agent, review-agent | selected-approach, failure-decision, proof-limit |
| [visual adaptation and direct manipulation contracts](references/visual-adaptation-and-direct-manipulation-contracts.md) | targeted | Visual meaning, adaptation, motion, or direct-manipulation alternative remains open | Current presentation and input-alternative contracts fix the changed behavior | analysis-agent, task-agent, review-agent | selected-approach, boundary-decision, proof-limit |
| [accessibility verification evidence](references/accessibility-verification-evidence.md) | evidence-pattern | Accessibility claim needs automated and human verification evidence | No changed accessibility claim awaits verification | analysis-agent, task-agent, review-agent | evidence-record, validation-plan, proof-limit, residual-risk |
