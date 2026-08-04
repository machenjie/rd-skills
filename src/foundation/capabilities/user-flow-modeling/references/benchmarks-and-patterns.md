# User Flow Decision Traps

This reference isolates ordered-journey decisions about actors, entries, branches, interruptions, authority, side effects, and asynchronous recovery.

## Decision Matrix

| Flow facet | Facts to establish | Accident signal |
| --- | --- | --- |
| Actor and goal | Named actor, goal, starting state, preconditions, authority context, and completion meaning | One generic user masks different starts, disclosures, or allowed outcomes |
| Reachable entry | In-flow, direct link, notification, return, expired session, stale parameter, missing context, and recovery | The nominal entry works while another reachable entry strands or misdirects the actor |
| Branch and exit | Observable predicate, known or unknown system outcome, user-visible result, persisted state, and next action | A fork or terminal node omits the system result or recovery contract |
| Interruption and re-entry | Back, refresh, cancellation, timeout, session expiry, draft/input owner, sensitive cleanup, and focus | Navigation loses work, exposes stale values, or resumes an invalid step |
| Side-effect outcome | Initiation, commit, unknown result, duplicate attempt, retrieval, partial completion, compensation, and re-entry | Retry or refresh repeats an effect or tells the actor it failed after commit |
| Permission handling | Backend authority, disclosure rule, visible/disabled/hidden presentation, denial copy, and recovery | UI presentation is treated as authorization or leaks protected state |
| Async completion | In-flow, away, timeout, failure, return, notification, stale-view behavior, and next valid action | Background work completes or fails after the view has lost its state owner |

## Decision Limits

- Current actor, route, state, authority, side-effect, and product evidence selects the journey; a named flow pattern does not settle it.
- A flow may identify duplicate and unknown-result obligations without prescribing a client key, HTTP status, queue, or backend transaction mechanism.
- When an affected submission creates a legal or financial commitment, name the applicable reversible, checked-and-correctable, or confirmation path. Apply the same requirement when it changes or deletes user-controlled data or submits test responses. The flow model does not certify implementation.
- Analytics, support exports, and live observations cover their authorized cohort, event definition, redaction, retention, and time window; unobserved branches remain unknown.
- A prototype, review, or focused test can expose journey risk without proving rollout behavior, exhaustive entry-path coverage, or production accessibility.
- Final claims cite current source and scoped post-change evidence; otherwise record `not_run` and the remaining journey risk.
