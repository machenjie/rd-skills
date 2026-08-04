# Reliability Output And Gates

Load only for assigned L3-L5 analysis, implementation, or independent review that needs mode-specific reliability closure.
Use it for an owned objective, alert, degraded mode, recovery path, capacity or cost risk, or incident-readiness decision.

## Do Not Load

Do not load for work without runtime reliability impact or when the root contract or compact checklist is sufficient. Named Layer 3 Skills own specialized lifecycle, algorithm, transaction, queue, security, and implementation mechanisms.

## Output Contract

Return exactly one mode closure, followed only by fields triggered by the selected risk:

1. **Analysis closure:**
   - Return the failure model, consequence, selected objective or operating expectation, evidence gaps, unknowns, and recommended next step.
   - Make no claim of edits, implementation results, or approval.
2. **Task closure:**
   - Return the actual diff, changed boundaries, post-edit outcomes, behavior delta, rollout/watch conditions, unverified scope, and residual risk.
   - Make no independent approval.
3. **Review closure:**
   - Return `Approved`, `Returned`, or `Blocked` with severity-ranked findings, reviewed and unreviewed scopes, and proof limits.
   - Use `Blocked` for inaccessible required evidence, naming the missing evidence, unblock condition, repair owner, and required re-review.
   - Make no repair to the target.
4. **Objective and alerting:** When an owned objective or consequence requires measurement, state the SLI or operating bound.
   - State target evidence, budget state, and owner.
   - Include an alert strategy and operator action only when operational risk or platform policy triggers alerting.
   - Justify alerting from traffic shape, urgency, error-budget semantics, and maturity.
5. **Resilience and degraded mode:** Map selected failure modes to bounded-call, overload, fallback, stale-data, partial-result, and recovery outcomes. The evidence states what users observe and why each timeout, retry, backpressure, isolation, or circuit-breaking mechanism fits the actual call and failure pattern.
6. **Telemetry quality:** Map symptoms and diagnostic causes to the minimum useful signals and operator actions. The evidence includes label and cardinality bounds, privacy constraints, correlation and sampling limits, ownership, and platform-policy support for each selected signal.
7. **Capacity and cost:** State demand assumptions, headroom, saturation boundary, and material unit-cost or storage and egress exposure.
   - State overload behavior and the evidence-backed scale, throttle, degrade, or rollback trigger.
8. **Recovery, incident, and limits:** State the objective, recovery boundary, mitigation, mechanism, owner, and evidence.
   - State applicable runbook or incident ownership and artifact-to-claim links.
   - State stale or unverified evidence and residual recovery, capacity, or cost risk.

## Quality Gate

1. When an owned objective or material consequence requires measurement, require an observable indicator and accountable target or operating bound.
   - Require current evidence beyond a merely user-facing path.
2. When operational risk or platform policy warrants alerting, require an actionable owner and response.
   - Derive the alert type from the objective, traffic, budget semantics, failure duration, and maturity.
3. When dependency failure can cascade or exhaust shared resources, require bounded calls.
   - Require tested degradation or recovery through controls matched to failure detection and state recovery.
4. When fallback, cache, replica, or delayed processing can return stale or partial data, require freshness semantics and safety bounds. Also require material user-visible state and recovery or reconciliation evidence. Silent staleness is not availability.
5. When diagnosability, operational response, or platform policy triggers telemetry, require decision-bearing signals with bounded label space, controlled sensitive data, and an owned action. Structured fields, trace correlation, sampling, exemplars, dashboards, and runbooks are candidates selected from the diagnostic path and cost/cardinality evidence.
6. When traffic, data volume, concurrency, storage, egress, or resource shape may change materially, require demand, saturation, headroom, overload, cost, and containment evidence. Cost controls remain conditional on an identified material exposure.
7. When failure can cause material harm, require current recovery and incident-readiness outcomes proportional to risk.
   - Material harm includes downtime, data loss, unsafe replay, slow restoration, and customer impact.
   - Select the readiness mechanism from policy, impact, change rate, and prior failures.
   - Candidates include a runbook, tabletop, failover or restore test, status workflow, on-call route, or post-incident review.
   - Do not mandate a universal mechanism or cadence.
