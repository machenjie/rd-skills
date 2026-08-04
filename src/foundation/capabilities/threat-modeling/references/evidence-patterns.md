# Threat Modeling Evidence Patterns

Load this reference when graph delta, actor capability, reachability, impact, control placement, bypass, validation, detection, or residual-risk claims need fresh proof. Do not use it as a framework, regulation, or control catalog.

| Claim | Minimum fresh evidence | Proof limit |
| --- | --- | --- |
| Security delta is bounded | Current asset/authority owner, changed entry point or dependency, trust transition, data/control flow, downstream effect, and unknown edges | Does not establish uninspected siblings or dynamic exposure |
| Actor capability is reachable | Actor access, knowledge, timing, control and prerequisites plus current source/config/policy path | Does not prove capability outside the inspected environment or identity state |
| Abuse path reaches an effect | Source-to-transformation-to-decision-to-storage/transport-to-sink trace, attacker-controlled or stale values, assumptions, and alternate branches | Does not establish hidden routes, external consumers, or future graph changes |
| Protected outcome and impact are current | Named invariant, affected data/authority/system, exposure, reversibility, propagation, and blast-radius evidence | Does not establish production prevalence or incident frequency without current data |
| Control intercepts the path | Control location and authority, owner, failure or unavailable behavior, compatibility, alternate-entry scan, and implementation/config evidence | Does not prove deployed state or untested bypass variants |
| Validation and detection cover the claim | Applicable abuse/negative test, current source/config/policy, parsed outcome, monitoring/audit signal, safe fields, and final-edit freshness | Does not prove unrelated actors, environments, detection latency, or response readiness |
| Residual risk is accountable | Unclosed path or consequence, containment or compensating evidence, owner, decision authority, release effect, and reopen trigger | Acceptance can become stale when scope, exposure, data, actor, or control changes |

## Freshness And Closure

- Treat prior threat models, architecture notes, scanner output, generated artifacts, incidents, and compaction summaries as search leads until current graph, owner, scope, configuration, and affected paths match.
- Classify known and discovered graph edges as evidenced, assumed, unreachable, externally owned, or unknown without treating missing evidence as safety.
- Re-run applicable abuse or negative validation after the final route, policy, parser, dependency, configuration, generated artifact, fixture, or control edit.
- Map the final confidence claim to current graph paths, control evidence, parsed validation, detection or audit artifact, owner evidence, and explicit residual scope.
