# Interaction State Modeling Evidence Patterns

Use this reference when interaction-state closure depends on validation freshness, backend or ARIA proof, prior source or task evidence claims, tool permission boundaries, or proof limits. Keep it as an evidence map, not a second state matrix catalog.

## State-To-Validation Map

| State claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| State set is complete | Operation scope, source signal list, idle/loading/success/error plus applicable empty/disabled/partial/timeout/permission/optimistic states | Inspected interaction has named states and owners | Future backend signals or uninspected components are covered |
| Empty and error states are distinct | Backend/status signal, empty condition, filtered-empty condition, permission/no-access path, and treatment map | Inspected UI does not collapse distinct recovery meanings | Copy, visual design, or all screen-reader behavior is approved |
| Disabled state is explainable | Prerequisite or permission signal, reachable affordance, `aria-disabled` or equivalent, description source, and keyboard review/test | Inspected disabled action has an accessible reason path | Full accessibility certification or all browser/AT combinations are proven |
| Optimistic update can roll back | Pre-mutation state capture, durable confirmation signal, rollback trigger, user-visible error, and test or review artifact | Inspected optimistic path can recover from rejection | Server idempotency or all conflict branches are proven |
| Timeout copy is truthful | Timeout threshold, cancellation truth, AbortController or equivalent, unknown-outcome language, and recovery test/review | Inspected timeout state avoids false cancellation claims | Server commit outcome or production latency distribution is proven |
| Backend alignment is explicit | HTTP/event/job status to UI-state map, 202/pending handling, error taxonomy, and validation artifact | Inspected frontend states follow declared backend signals | Backend contract correctness unless separately verified |
| ARIA/status evidence is fresh | Live region, alert role, busy state, focus path, screenshot/story/test, and final-source freshness | Inspected status changes are exposed in the named UI path | All assistive technologies or design-system components are certified |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, previous bug reports, generated context, stories, and prior tests as selectors until current source, backend signals, stories, and fresh validation confirm them.
- Accept prior "loading/error already handled", "disabled copy exists", "202 means success", or "state matrix was tested" claims only when current source and tests still match.
- Mark evidence stale after edits to API status mapping, state ownership, disabled conditions, optimistic updates, timeout behavior, ARIA attributes, stories, tests, reports, or generated artifacts.
- For each final-handoff claim about an interaction state, transition, forbidden transition, accessibility treatment, backend signal, or recovery action, name its supporting command, test, story, or owner review. Missing evidence remains an explicit not-run residual risk.

- If live UI experiment, production flag/config change, or backend status mutation, record environment, owner approval, stop condition, rollback plan, and redaction rule.
- If production telemetry, session replay, or support-data query, keep access read-only or approved-connector-scoped, aggregate sensitive labels, and redact tenant/user/private state details.
