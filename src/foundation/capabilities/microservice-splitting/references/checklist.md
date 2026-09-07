# Microservice Extraction Decisions

Load this reference only when deciding whether and how to extract, retain, merge, or recombine a deployable service. Service count, team count, or generic “best practice” is not split evidence.

## Extraction Decision Matrix

| Axis | Required evidence | Reject/defer condition |
| --- | --- | --- |
| Business capability | Bounded language, lifecycle, policy and accountable product owner are separable. | Same rules/owner or unclear domain boundary. |
| Team/deploy independence | Code, incidents, roadmap and normal releases can be owned without coordinated deployment. | Extraction preserves release coupling or exceeds accepted cognitive/on-call capacity. |
| Scale/cost | Measured CPU/memory/IO/traffic or unit-cost divergence justifies independent runtime scaling. | Generic scale claim or added network/platform cost lacks evidence/owner. |
| Fault/latency isolation | When fault or latency isolation is a split force, define a contained failure or degraded outcome for the new boundary and show the call path meets current latency and availability budgets. | The call path violates accepted isolation, latency, or availability limits, or its selected fallback/degradation is unproved. |
| Compliance/data perimeter | Extraction measurably narrows residency, tenant, audit or regulated scope. | Same classification/control surface remains shared. |
| Data authority | One service owns writes; migration removes shared DB/FK/direct internal reads or explicitly contains them. | Dual authority, unowned reconciliation, or hidden shared-schema contract remains. |
| Public contract/consumers | API/event contract, consumer inventory, versioning and mixed-version behavior are stable enough to own. | Contract exposes persistence internals or unknown consumers lack an owner. |
| Transaction/consistency | Atomic work stays local or the transaction owner's supported cross-participant protocol proves required atomicity or recoverable eventual behavior. | Required ordering, duplicate, participant-failure, or recovery behavior is unproved. |
| Dependency resilience | Timeout/retry/circuit/bulkhead/queue mechanisms are selected only where dependency criticality and failure tests require them. | One-size controls or unknown-outcome replay increase cascade/duplicate risk. |
| Operability | Accountable service, release, and incident owners exist. Platform, identity/config/network, telemetry, capacity, runbook, and escalation evidence follows actual service risks and policy, with justified omissions. | Another runtime would be unowned or its required live controls are unverified. |
| Rollout/rollback/retirement | Strangler/abstraction/parallel/expand-contract mechanism has traffic/data/event reversal and legacy retirement evidence. | Big-bang cutover, no mixed-version proof, or legacy path has no removal signal. |
| Outcome/proof limit | Choose keep modular monolith, repair boundary, extract, phase, merge, or recombine; record rejected outcome and residual owner. | ADR/source graph/local tests are treated as proof of live traffic, provider, production capacity or incident readiness. |

Route cross-module shape to `module-boundary-design`, contracts/consumers to `data-api-contract-changer`/`consumer-impact-analysis`, consistency/events to `transaction-consistency`/`event-driven-architecture`, operability to `reliability-observability-gate`, release to `delivery-release-gate`, and regulated perimeter to `security-privacy-gate`.
