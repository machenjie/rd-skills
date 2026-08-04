# Interaction State Benchmarks And Patterns

Use this reference when a real state matrix needs detailed benchmark anchors, state examples, or a decision tree. Keep `SKILL.md` focused on routing, evidence, and quality gates.

## Benchmark Anchors

- **Nielsen / XState**: visible status, prevention, recovery, and explicit finite transitions expose impossible combinations and user actions.
- **WCAG 2.1/2.2 / ARIA APG**: prefer native semantics for user-facing functions affected by the state change.
- Select urgency-appropriate `aria-busy`, `aria-live`, or `role="alert"` semantics.
- Preserve programmatic relationships, explainable disabled states, and keyboard operability.
- Verify the changed interaction without claiming unaffected routes or assistive technologies.
- **TanStack Query / SWR**: separate data availability from request progress across status/fetchStatus, stale data, background refresh, pause, retry, validation, and error.
- **Remix `useNavigation` / `useFetcher`**: idle, submitting, and loading states distinguish form submission from page loading.
- **Progress treatment**: skeletons and action-level indicators are candidates selected from layout stability, duration, interaction, and accessibility needs.

## Non-Normative State Examples

These rows are calibration prompts, not a complete matrix or default mapping. Select only distinctions supported by product and operation semantics.
Derive treatment, actions, recovery, and accessibility signals from authority, side effects, recoverability, disclosure, urgency, focus behavior, and current evidence.

| Example distinction | Evidence that may justify it | Decisions to derive |
| --- | --- | --- |
| Available or idle | No active operation, or authoritative data is ready. | Available actions, empty meaning, focus entry, and refresh behavior. |
| Pending or unknown | Work is accepted, running, disconnected, timed out, or awaiting reconciliation. | Progress treatment, repeat safety, cancellation truth, stale data, and status urgency. |
| Durable success or empty | Authoritative outcome and returned data cardinality are known. | Whether acknowledgement, empty guidance, follow-up action, or no announcement is useful. |
| Rejected, denied, missing, or filtered | Typed operation outcome and disclosure policy distinguish the reason. | Safe explanation, visible actions, focus, and whether access recovery exists. |
| Failed or retryable | Failure mechanism, provider guidance, idempotency, and operation cost support recovery. | Retry eligibility, backoff, preserved input, diagnostics, and support path. |
| Partial, optimistic, or rolled back | Local projection or subset completion differs from durable state. | Reconciliation, compensation, duplicate prevention, conflict handling, and announcement. |
| Transport outcome | A 2xx, 4xx, 5xx, or network result describes one exchange, not the complete operation state. | Interpret payload, durability, authority, disclosure, and retry contract before choosing UI behavior. |

## State Derivation Questions

1. Identify the authoritative outcome and whether a transport response proves durable completion.
2. Determine whether repeat, cancel, or navigation can duplicate or abandon side effects.
3. Offer retry only when idempotency, provider guidance, operation cost, and current authority make it safe.
4. Derive submit availability from duplicate-effect risk, prerequisites, cancellation, and supported concurrency.
5. Choose status text, focus behavior, live regions, or alerts from urgency, interruption cost, and accessibility requirements.
6. Apply disclosure policy before distinguishing denied, missing, filtered, or failed states.
7. Keep unknown, partial, and optimistic outcomes distinct until reconciliation evidence closes them.

## Anti-Pattern Review

- Single spinner for loading, timeout, and error hides recovery paths.
- Blank empty state leaves users unsure whether content failed or does not exist.
- Success toast on `202 Accepted` lies about durable completion.
- Optimistic delete without rollback creates UI/data divergence.
- HTML `disabled` without explanation hides unavailable actions from keyboard users.
- Console-only or visually-only error feedback is inaccessible.
- Timeout copy that says "cancelled" can cause unsafe duplicate submission.
