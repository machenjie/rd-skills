# Workflow Identity, State, And Unknown Outcomes

**Load when:** Cross-service workflow identity, durable step state, command/effect correlation, completion authority, or unknown outcomes remain unresolved.

**Do not load when:** One local operation has no independently committed participant effect or durable workflow state.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `boundary-decision`, `failure-decision`, `proof-limit`

## One Decision

Select one durable identity and state contract that distinguishes intent, dispatch, participant effect, observation, and terminal workflow outcome.

## Decision Matrix

| Boundary | Required decision | Failure signal |
|---|---|---|
| Business identity | Subject, tenant, canonical intent, duplicate semantics, and authority | Transport attempt becomes workflow identity |
| Execution identity | Workflow, run, definition version, and continuation relationship | Restart creates an unrelated logical operation |
| Step identity | Stable step meaning, participant, prerequisites, and attempt relation | Retry creates a second logical step |
| Durable state | State invariant, writer, transition guard, fence/version, timestamp, and terminal meaning | In-memory progress is treated as workflow authority |
| Command | Command identity, workflow/step correlation, input version, and intent persistence | Dispatch occurs before durable intent |
| Effect | Participant effect identity, idempotency scope, result authority, and status query | Broker acknowledgement is treated as effect completion |
| Unknown outcome | Trigger, stored state, repeat prohibition, query/reconciliation authority, deadline, and owner | Timeout is converted directly to failure or retry |
| Completion | Required participant facts, workflow transition, response/result persistence, and publication | Completion is lost after the participant commits |

## Verification

- Crash before and after intent persistence, dispatch, participant commit, result receipt, and terminal transition.
- Drop completion responses and acknowledgements while the participant both commits and rejects.
- Repeat commands concurrently and after deduplication retention boundaries.
- Reorder delayed results from prior attempts and runs.
- Query unknown states through the authoritative participant or reconciliation path.

## Primary Sources

- [Temporal Workflow Execution overview](https://docs.temporal.io/workflow-execution)
- [Temporal Events and Event History](https://docs.temporal.io/workflow-execution/event)
- [Azure Saga distributed transactions pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/saga)

Official workflow and platform pages were accessed on 2026-07-26.

## Proof Limits

Temporal and Azure describe product and pattern semantics, not guarantees for another implementation. Focused crash tests prove only inspected state stores, transports, participants, retention windows, and versions; external commit status needs direct participant evidence.
