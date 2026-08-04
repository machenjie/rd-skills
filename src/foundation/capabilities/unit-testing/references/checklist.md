# Unit Testing Checklist

- Identify the changed local behavior or invariant.
- Record an exact failure mechanism only when an accepted defect, incident, review finding, or equivalent recurrence case exists.
- Capture relevant input, state, ordering, branch, or dependency response and an adjacent non-trigger when useful. For a known failure, preserve its causal trigger under the `regression-testing` contract.
- Assert caller-visible success, error, state, event, or absence of a forbidden effect.
- For money, permission, quota, inventory, or transitions, prove denied and unauthorized outcomes.
- Control relevant clock, randomness, identifiers, scheduler, environment, and mutable global state through owned seams.
- Record double behavior, omitted semantics, fidelity limits, and the real-boundary evidence still required.
- Challenge critical assertions with a replayable mutation or fault only when it materially improves confidence or the selected regression contract requires counterfactual proof.
- Clean fixtures, temporary resources, scheduled work, and changed global state after success, failure, and cancellation.
- Run the mapped command after the final material edit. Retain red-before-fix only for selected regression work when feasible; otherwise record current post-edit evidence and its proof limit.
- State skipped entry points, real boundaries, concurrency schedules, and production effects as residual risk.
