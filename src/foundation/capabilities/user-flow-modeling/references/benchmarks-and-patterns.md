# User Flow Modeling Benchmarks And Patterns

Use this reference when a user-flow-modeling output needs more detail than the `SKILL.md` body can carry efficiently. Keep the main skill body focused on routing, evidence, output contract, and quality gates.

## Benchmark Anchors

- Jesse James Garrett, The Elements of User Experience: flow connects information architecture to interaction design.
- Nielsen Norman Group journey mapping: multi-step journeys need touchpoints, decisions, emotions, and recovery moments.
- Hierarchical Task Analysis: tasks decompose into goals, operations, plans, and exception paths.
- Material navigation guidance: back, up, deep link, and state-preservation behavior must match user expectations.
- WCAG 2.2 SC 3.3.4 and 2.4.3: consequential submissions should be reversible or confirmed, and focus order must stay logical through branches.
- HTML History API and modern routers: `pushState`, `replaceState`, route params, and navigation state affect back/re-entry behavior.
- RFC 7807 Problem Details: structured errors should support recoverable user-facing failure exits.
- OAuth 2.0 PKCE redirect flows: preserve `state` and return intent safely across authentication redirects.

## Flow Node Classification Matrix

| Node type | Description | Required design elements | Failure to handle risk |
| --- | --- | --- | --- |
| Entry point | Where the actor enters the flow. | Trigger, auth, required params, state precondition, return intent. | Unauthorized access or broken deep link. |
| Decision branch | Conditional fork based on user/system state. | Boolean predicate, both destinations, denied/unknown outcome. | Undefined state or hidden permission defect. |
| Action step | User submits data or triggers system action. | Loading state, error feedback, idempotency, retry/cancel behavior. | Duplicate submission or silent failure. |
| Wait state | Async operation in progress. | Progress feedback, status source, timeout, failure exit, away/return behavior. | User abandonment or duplicate job. |
| Partial checkpoint | Some steps completed and may be resumed. | Re-entry detection, draft/state owner, duplicate prevention. | Restart loop or duplicate side effect. |
| Success exit | Flow completed successfully. | Confirmation, persisted system state, next action, breadcrumb/history cleanup. | User lacks confidence or re-enters stale flow. |
| Failure exit | Flow cannot complete. | Non-leaking error, recovery options, support path, preserved input where safe. | Dead end or unnecessary abandonment. |
| Cancellation exit | Actor abandons or intentionally stops. | Data preserved/discarded rule, cleanup/compensation, navigation target. | Orphaned records or unexpected data loss. |
| Permission branch | Actor lacks access to path/resource/action. | Non-revealing denial, escalation/request access path, audit/test obligation. | Resource existence leak or blocked legitimate user. |

## Interruption Decision Tree

```text
User navigates away from an in-progress form or multi-step flow:
  Has the user entered data that is not yet safely persisted?
    NO  -> Allow navigation freely.
    YES -> Is the flow re-entrant from the same state?
      YES -> Auto-save draft, navigate, and offer resume on return.
      NO  -> Warn before leaving.
        If leave: discard draft or run cleanup/compensation, then navigate.
        If stay: return to the flow and restore focus/input state.

Session expires mid-flow:
  Is partial data persisted server-side?
    YES -> Preserve draft for a declared retention window.
           Redirect to login with safe return intent.
           After re-authentication, resume from last valid step.
    NO  -> Explain that the session expired and data was not saved.
           If unacceptable, require draft persistence before implementation.

Async operation completes while the user is away:
  -> Record durable result status.
  -> Notify in-app or push/email only when appropriate for sensitivity and urgency.
  -> Deep link to result/status view.
  -> Do not make email the primary feedback for time-sensitive actions.
```

## Branch Review Checklist

- Every branch has a predicate that can be asserted in a test.
- Every branch has a user-visible outcome and a system-state outcome.
- Every failure branch has at least one recovery option or explicit terminal reason.
- Every cancellation branch states what data is preserved, discarded, or cleaned up.
- Every retry branch states whether the action is idempotent and how duplicates are detected.
- Every back-navigation branch states whether browser back and in-app back differ.
- Every permission branch states resource-existence disclosure policy.
- Every deep-link entry states auth, parameters, state precondition, and stale-link behavior.
- Every async wait has in-flow, away, timeout, failure, and return-to-result handling.
- Every reused flow pattern has current route/screen/test confirmation or a freshness limit.

## Anti-Patterns To Reject

| Anti-pattern | Failure | Safer treatment |
| --- | --- | --- |
| Flow model contains only "start -> submit -> success" | Failure, cancellation, permission, and timeout are implementation guesses. | Model every exit and branch predicate before implementation. |
| Retry button re-posts without idempotency key | Duplicate order, charge, record, import, or job. | Use client/request idempotency key and duplicate-result return. |
| Permission branch says "requires admin" for a sensitive resource | Reveals resource and role model to unauthorized actors. | Use non-revealing denial and log/request-access path where appropriate. |
| Browser back after submit revisits a side-effecting step | Replays or confuses an irreversible action. | Use history replace, status/result route, or read-only completed step. |
| Cancellation exits without cleanup | Pending records, uploaded files, or abandoned jobs remain. | Define cleanup, compensation, retention, or explicit preserved draft. |
| Async job has spinner only | User cannot tell whether work completed, failed, or is safe to retry. | Provide status source, timeout, failure, notification, and result route. |
| Reused old journey from memory without source check | Keeps stale route, dead-end, or outdated permission branch. | Confirm against current route graph, source, tests, and product constraints. |
