# Prototype Decision Traps

This reference isolates prototype decisions about uncertainty, fidelity, hierarchy, interaction, failure, responsive behavior, accessibility, and handoff limits.

## Decision Matrix

| Prototype facet | Facts to establish | Accident signal |
| --- | --- | --- |
| Uncertainty and fidelity | Decision question, possible outcome, evidence, owner, fidelity, and excluded claims | Detail accumulates while no decision or evidence need is named |
| Surface boundary | Actor, goal, trigger, preconditions, exit, route and data assumptions, and exclusions | Reviewers infer a complete journey or production contract from a bounded surface |
| Content and action hierarchy | Decision-relevant content, action priority, current source, placeholder assumptions, and disclosure | Invented copy, data, or permissions are mistaken for approved product behavior |
| Interaction and validation | Trigger, preconditions, feedback, validation, persistence, cancel, retry, undo, destructive effect, and outcome | An action looks complete while its failure, cancellation, unknown result, or consequence is absent |
| Reachable states | Trigger, user meaning, system meaning, available action, ownership, and transition handoff | A generic state catalog hides the few transitions the decision actually depends on |
| Responsive behavior | Scoped viewport and content, reading order, reflow, overflow, input method, focus, and unsupported cases | A desktop screenshot is treated as evidence for small, large, zoomed, or translated layouts |
| Accessibility behavior | Semantics, names, keyboard path, focus, announcement, error association, and color-independent meaning | Visual review is reported as accessibility validation or certification |
| Reuse and handoff | Existing component semantics and state fit, extend/local/new choice, design-system gap, owner, and implementation or validation handoff | A prototype invents a component or implies production readiness without a bounded reuse and handoff decision |

## Decision Limits

- Current product, content, route, state, component, and accessibility evidence selects the prototype detail; a named pattern or tool does not settle it.
- Placeholder content, sample data, implied roles, and route assumptions remain labeled until their owning contracts approve them.
- A walkthrough or review covers the shown states, paths, viewport, assistive assumptions, and participants; unexercised behavior remains unknown.
- Prototype evidence can support a design or implementation decision without proving production behavior, performance, rollout safety, or accessibility conformance.
- Final claims cite current prototype artifacts and scoped evidence; otherwise record `not_run` and the remaining uncertainty.
