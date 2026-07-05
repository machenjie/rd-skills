# Example Output

```markdown
## Resilience Plan

mode_selected: optional graceful degradation.

resilience_evidence:
- Source inspected: product detail controller and recommendation client.
- Graph/memory/trajectory judgment: prior memory that recommendations are optional accepted only after current source confirmed no checkout dependency.
- Validation freshness: fallback unit test planned after final implementation.

Dependency: recommendation service.
Protected flow: product detail page must load even when recommendations fail.
Criticality: OPTIONAL-DEGRADABLE.

Behavior:
- Timeout recommendation call after 300 ms, below the 800 ms page budget.
- Do not retry on user-facing path; retry belongs to async cache warmup.
- Open circuit after 20 failures in 60 seconds.
- Show product page with a typed degraded state and without recommendation rail while circuit is open.
- Half-open with 5 trial requests after 2 minutes.

Observability:
- Metric: recommendation_fallback_total.
- Metric: recommendation_circuit_state.
- Alert when fallback rate exceeds 30 percent for 10 minutes.

changed_degradation_to_validation_map:
- timeout_config -> unit test with delayed fake client.
- fallback_behavior -> unit test with client failure and degraded state assertion.
- circuit_breaker -> integration or fault-injection test for open and half-open behavior.
- observability -> metric assertion for fallback and circuit state.

handoff_boundaries:
- observability owns dashboard and alert tuning.
- quality-test-gate owns fallback and circuit test evidence.

evidence_limits:
- Does not prove provider production recovery behavior or all tenant-specific traffic shapes.
```
