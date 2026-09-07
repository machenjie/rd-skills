# Reliability Output And Gates

Load only for analysis, implementation, or independent review needing extended mode-specific closure for an owned objective, alert, degradation, capacity/cost, recovery, or incident-readiness decision.

## Do Not Load

Do not load without runtime reliability impact or when root/checklist closes the selected risk. Specialized lifecycle, algorithm, transaction, queue, security, and implementation mechanisms remain with their authoritative capability boundaries.

## Mode Closure

- **Analysis closure:** Return failure model, consequence, selected objective or operating expectation, evidence gaps, unknowns, and next step; claim no edit or approval.
- **Task closure:** Return actual diff, changed boundaries and behavior, post-edit evidence, rollout/watch conditions, unverified scope, and residual risk; claim no independent approval.
- **Review closure:** Return `Approved`, `Returned`, or `Blocked`, ranked findings, reviewed/unreviewed scope, and proof limits; make no repair. A block names missing evidence, unblock condition, repair owner, and re-review.

## Reliability Decision Output

- **Objective:** When consequence requires measurement, state indicator/bound, target evidence, budget state, and owner.
- **Alert:** Derive risk-triggered alert action from traffic, urgency, budget semantics, and maturity.
- **Failure outcomes:** Map reachable failure to bounded-call, overload, fallback/staleness, partial-result, and recovery outcomes.
- **Control fit:** State what users observe and why each selected timeout, retry, backpressure, isolation, or breaker fits.
- **Telemetry:** Map symptom and cause to minimum signals and actions with label/cardinality, privacy, correlation, sampling, ownership, and policy bounds.
- **Capacity/cost:** State demand, headroom, saturation, unit-cost/storage/egress exposure, overload behavior, and evidence-backed throttle/degrade/rollback trigger when material.
- **Recovery/limits:** State recovery boundary, mitigation, mechanism, owner, current artifact-to-claim evidence, stale/unverified scope, and residual recovery/capacity/cost risk.

## Quality Gate

- Require an indicator and accountable owner only when an objective or material consequence needs measurement.
- Require an alert only when risk or policy supplies an owned response.
- Require bounded calls and tested degradation/recovery for cascade or shared-resource exhaustion risk.
- Record that silent staleness is not availability through freshness semantics, material user-visible state, and recovery or reconciliation evidence for the selected fallback.
- Require decision-bearing, privacy-safe, bounded-cardinality signals when diagnosis or response needs telemetry.
- Require demand, saturation, headroom, overload, cost, and containment evidence only for material shape or exposure.
- Require current recovery and incident-readiness evidence proportional to harm.
- Select the mechanism from policy, impact, change rate, and prior failures rather than a universal cadence.
- Bind incident closure to verified cause, customer impact, corrective-action owner, and a current watch signal.
- Choose runbook, tabletop, failover/restore test, status workflow, on-call route, or post-incident review only when the named risk and policy require it.
