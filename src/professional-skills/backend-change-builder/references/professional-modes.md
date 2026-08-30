# Backend Implementation Modes

Owner: `backend-change-builder` using `task-agent` only.

## Load Trigger

Load when an accepted backend task needs implementation-mode-specific proof beyond the root contract, including repair of an accepted external finding.

## Do Not Load

Do not use this reference to diagnose an unknown cause, independently review a diff, or approve completed work.

## Capability Boundaries

- Cause discovery and desired-behavior definition are analysis work; implementation stops until source-backed conclusions are supplied.
- Independent implementation assessment is outside the implementer's authority; provide the actual diff/reference and fresh validation as review inputs.

## Implementation Modes

1. **New or modified behavior:** implement the accepted endpoint, service, repository, worker, validation, or policy change with proof limited to triggered obligations and current patterns.
2. **Behavior-preserving refactor:** implement accepted movement, extraction, split, rename, or deletion with affected caller, contract, authorization, side-effect, error-behavior, and intentional-delta evidence.
3. **Performance or reliability implementation:** implement a control selected from measured evidence with baseline, affected resource, overload or retry behavior, post-edit result, production-scale limits, and no speculative optimization.
4. **Release or migration-sensitive implementation:** implement the accepted compatibility or data-state step with coexistence, migration or rollout, detection, rollback or forward-repair, and current-consumer evidence.

## Review-Finding Or Defect Repair

Stop repair work without an accepted finding or verified failure mechanism.

1. Preserve the accepted finding or verified failure mechanism, affected acceptance, target path, and required outcome within the assigned repair rather than a new diagnosis mode.
2. Confirm current source still exhibits the cited mechanism before editing. When recurrence is credible, scan the mechanism's bounded sibling/caller/contract scope and record results and exclusions; otherwise omit same-pattern claims.
3. Return the actual repair diff or host-native diff reference, post-repair tests run after the last material edit, proof limits, and residual risk.
4. When repairing an externally raised finding, provide the repaired diff and fresh evidence for independent re-review; implementer assertion does not close that finding.

## Selection Limits

- Synchronous retries require duplicate-outcome proof when triggered, but acknowledgement, replay, poison-message, and broker recovery fields apply only to message or job delivery.
- Include authorization, transaction, idempotency, error, observability, placement, migration, and rollback fields only when the accepted change triggers that risk.
