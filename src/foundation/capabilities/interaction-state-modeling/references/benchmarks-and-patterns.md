# Interaction State Benchmarks And Patterns

Use this reference when a real state matrix needs detailed benchmark anchors, state examples, or a decision tree. Keep `SKILL.md` focused on routing, evidence, and quality gates.

## Benchmark Anchors

- **Nielsen's 10 Usability Heuristics**: visibility of system status, error prevention, and recoverable errors require explicit state transitions and user actions.
- **WCAG 2.1 / 2.2**: status messages use `role` or `aria-live`; relationships and disabled explanations remain programmatically determinable; all functionality remains keyboard reachable.
- **XState**: explicit finite states prevent impossible combinations and make transitions reviewable.
- **TanStack Query / React Query**: `status`, `fetchStatus`, stale state, background refetch, pause, retry, and error states separate data availability from request progress.
- **SWR**: stale-while-revalidate distinguishes existing data, loading, validation, and error.
- **Remix `useNavigation` / `useFetcher`**: idle, submitting, and loading states distinguish form submission from page loading.
- **Skeleton loading**: skeletons fit layout-defining content; spinners fit short actions such as button submit or file upload.
- **ARIA authoring practices**: use `aria-busy`, `aria-live="polite"`, and `role="alert"` according to urgency.

## Complete State Matrix

| State | Trigger | User-visible treatment | ARIA / Accessibility | Allowed actions | Recovery |
| --- | --- | --- | --- | --- | --- |
| Idle | Page load, reset | Default content or empty prompt | None required | All available actions | N/A |
| Loading | API call initiated | Skeleton or spinner; disable submit | `aria-busy="true"` on container; `aria-label="Loading..."` | Cancel when cancellable; navigation | Retry or cancel |
| Success | Durable 2xx completion | Content rendered; transient success status | `aria-live="polite"` on status region | All actions | N/A |
| Error | 4xx/5xx or network error | Error message with recovery CTA | `role="alert"` or `aria-live="assertive"` | Retry; dismiss; contact support | Retry; fix input |
| Empty | 2xx with zero results | Empty state plus meaningful CTA | Visible text; no special ARIA | Create; import; invite | Create first item |
| Permission-denied | 403 or policy check | Non-leaking unavailable/access message | `role="alert"` when blocking | Request access when allowed | Request access CTA |
| Disabled | Prerequisite unmet or no permission | Focusable disabled affordance plus reason | `aria-disabled="true"` plus `aria-describedby` | Focus to see reason | Complete prerequisite |
| Partial | Some data or actions failed | Available data plus warning banner | `aria-live="polite"` warning | Use available data; retry failed parts | Retry failed parts |
| Timeout | Threshold exceeded | Uncertainty copy plus refresh/check action | `aria-live="polite"` | Refresh to check; cancel only when true | Refresh; retry safely |
| Optimistic | UI updated before durable confirmation | Projected state with pending indication | `aria-busy="true"` on affected item | Undo when available | Rollback on error |
| Rollback | Optimistic update rejected | Revert UI plus error message | `role="alert"` for error | Retry; dismiss | Retry action |

## State Machine Decision Tree

For each async operation:

1. Define initial state:
   - User-triggered action starts in idle.
   - Page-triggered fetch starts in loading or stale-with-refreshing.
2. Define loading transition:
   - Layout-defining content uses skeleton loading.
   - Short actions use button-level spinner or status.
   - Timeout threshold is explicit.
3. Define success outcomes:
   - Returned data maps to success.
   - Empty array maps to empty, not error.
   - `202 Accepted` maps to pending/processing, not durable success.
4. Define error outcomes:
   - Network error maps to retryable error.
   - 4xx maps to fix-input, unavailable, or permission state.
   - 5xx maps to retry/backoff or support state.
   - Timeout uses uncertainty language.
5. Define disabled state:
   - Temporary in-flight work should show progress, not unexplained disabled UI.
   - Permission or prerequisite disabled states remain reachable with an explanation.
6. Define optimistic rollback:
   - Durable success preserves optimistic state.
   - Rejection reverts and announces the error.

## Anti-Pattern Review

- Single spinner for loading, timeout, and error hides recovery paths.
- Blank empty state leaves users unsure whether content failed or does not exist.
- Success toast on `202 Accepted` lies about durable completion.
- Optimistic delete without rollback creates UI/data divergence.
- HTML `disabled` without explanation hides unavailable actions from keyboard users.
- Console-only or visually-only error feedback is inaccessible.
- Timeout copy that says "cancelled" can cause unsafe duplicate submission.
