# Regression Guard Decision Patterns

These patterns preserve a known failure mechanism at the narrowest admissible guard boundary.

## Preserve The Failure Mechanism

| Failure mechanism | Admissible guard boundary | Escalate when |
| --- | --- | --- |
| Local rule, parser, mapping, calculation, or state transition | unit guard with the exact trigger and denied outcome | framework serialization or lifecycle caused the defect |
| Query, constraint, transaction, cache, or migration | real persistence/integration slice | vendor behavior, concurrency, rollback, or replica visibility is essential |
| API, authorization, tenant, or ownership boundary | integration/API guard with allowed, denied, and non-leak outcomes | adjacent objects or consumers share the mechanism |
| Browser event, rendering, navigation, or local persistence | frontend/component or assembled journey guard | deployed cross-boundary behavior is causal |
| Queue, retry, scheduler, webhook, or eventual result | deterministic boundary test with duplicate, ordering, failure, and bounded-observation cases | production-only timing or external behavior cannot be isolated safely |
| Race, hardware, or environment-specific condition | controlled scheduler/fault, replay, or compensating detection | deterministic automation cannot preserve the trigger |

## Counterfactual Options

1. Run the new guard against a protected unfixed revision and confirm the matching failure reason.
2. If revision replay is unsafe, reintroduce the causal fault with a targeted mutation or fault seam and confirm the guard rejects it.
3. If neither path is admissible, document why, preserve other mechanism evidence, and assign compensating detection and a revisit trigger.

## Same-Pattern Closure

- Search sibling branches, duplicate implementations, related consumers, alternate entry points, and historical variants for the causal pattern.
- Map each materially reachable match to the new guard, a distinct fresh guard, an implementation correction, or owned residual risk.
- Preserve fixture fields that carry the mechanism; justify minimized equivalents and own drift, redaction, setup, and cleanup.
- For concurrent behavior, assert admissible outcomes and forbidden outcomes instead of one scheduler order.
- For eventual behavior, observe a semantic condition within a risk-derived bound instead of sleeping for a fixed interval.
