# State Transition and Backend Evidence

Use this evidence-pattern Reference only for the named state-transition-and-backend-evidence decision.

## Evidence Contract

- Bind the inspected state set to operation scope, source signals, applicable empty, disabled, partial, timeout, permission, and optimistic states, and their owners.
- Distinguish empty and error through backend status, empty and filtered-empty conditions, permission paths, and treatment mapping.
- Prove optimistic rollback from pre-mutation capture, durable confirmation, rollback trigger, visible error, and current test or review evidence.
- Bind timeout copy to threshold, cancellation truth, unknown-outcome language, and recovery evidence.
- Map HTTP, event, and job status to UI states, including `202` or pending behavior, without claiming backend correctness.

Reject local or optimistic completion before the authoritative effect and any late response that overwrites newer intent.
