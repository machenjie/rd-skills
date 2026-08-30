# Journey Risk Patterns

Use this reference when `experience-impact-modeler` needs deeper risk review for user journeys, interaction states, instrumentation, or evidence limits. Keep the main body efficient; use this file for mode-specific traps and proof boundaries.

## Risk Pattern Matrix

| Journey risk | Detection signal | Required model evidence | Capability boundary |
| --- | --- | --- | --- |
| Orphaned entry or exit | Changed screen has no upstream or downstream path. | Actor, entry, decision, cancel, retry, completion, and back-navigation map. | User-flow modeling and falsifiable acceptance. |
| Missing state ownership | Loading, empty, permission, timeout, partial success, or retry state is not named. | State table with copy, focus, persistence, recovery, and owner. | Interaction-state modeling and behavior-proof strategy. |
| Accessibility trap | Modal, drawer, route change, async update, or validation error changes focus. | Keyboard path, focus destination, accessible names, live region, and contrast check. | Accessibility judgment and browser-level behavior proof. |
| Destructive or sensitive action | Delete, revoke, payment, permission, account, compliance, or irreversible action. | Consequence copy, confirmation, denial, audit/receipt, undo or recovery, and safe error state. | Security/privacy judgment and release approval. |
| Operational workflow drag | Repeated operator screen adds blocking loading, slow filters, or dense error handling. | Perceived performance behavior, progressive rendering, keyboard efficiency, and recovery path. | Reliability/observability and performance-budget judgment. |
| Instrumentation drift | Event, exposure, assignment, metric, dashboard, or A/B conflict changes. | Event taxonomy, exposure proof, assignment unit, guardrails, SRM check, dashboard migration, rollback. | Experiment-analysis and test-proof judgment. |
| Stale visual proof | Screenshot/report/manual check predates final route, copy, style, data, or instrumentation edit. | Freshness record tied to final diff and validation command or explicit not-run risk. | Evidence-freshness and plan-consistency judgment. |

## State Pattern Requirements

- **Permission-denied**: explain what is safe to reveal, how to request access, and where focus lands.
- **Timeout**: preserve input, distinguish retryable from terminal state, and avoid duplicate destructive submits.
- **Partial success**: show completed work, failed work, recovery action, and whether retry is safe.
- **Cancel/back**: preserve or discard state intentionally; destructive abandon paths need explicit copy.
- **Empty**: connect the zero-data state to the user's intent and a next action; avoid blank containers.
- **Error**: name cause when safe, next action, retry/cancel/contact path, and diagnostic handoff owner.

## Evidence Limits

- Treat screenshots as evidence only for rendered layout in the captured viewport and state. Keyboard access, screen reader behavior, analytics correctness, and other breakpoints remain unproven.
- Automated accessibility scans catch many static violations; they do not prove focus order, recovery copy, or assistive technology compatibility.
- Treat passing E2E tests as evidence only for scripted paths. Other entry points, permission states, and production data conditions remain unproven.
- Treat analytics reports as evidence only for event arrival in inspected data. User comprehension, accessibility, and dashboard migration correctness remain unproven.
- prior task evidence and repository inspection are selectors; current source, final diff, and fresh validation decide closure.

## Handoff Closure

```yaml
journey_risk_closure:
  selected_patterns:
    - risk: ""
      evidence: ""
      owner: ""
  stale_evidence:
    - artifact: ""
      reason: ""
      next_owner: ""
  proof_limits:
    proves: ""
    does_not_prove: ""
  residual_risk:
    - risk: ""
      owner: ""
      next_owner: ""
```
