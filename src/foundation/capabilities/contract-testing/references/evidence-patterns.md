# Contract Testing Evidence Patterns

These records bound compatibility claims to named providers, consumers, versions, and observed behavior.

## Claim Records

- **Named surface:** provider, consumer class, operation or message, contract source, compared versions, and compatibility direction.
- **Provider behavior:** fresh verification command or artifact, selected expectations, outcome, and behavior outside the selected cases.
- **Consumer admissibility:** named consumer version, parsing/compilation/behavior result, fixture or generated input, and unrepresented consumer classes.
- **Mixed-version safety:** producer-reader matrix, retained or replayed payload source, rollout order, and combinations not exercised.
- **External behavior:** fixture provenance, capture environment and time, provider/spec version, redaction, replay result, and drift trigger.
- **Compatibility service:** subject or selector, configured policy, compared versions, environment, result, and semantic behavior outside that check.

## Freshness And Limits

- Refresh provider and consumer evidence after material contract, fixture, generator, compatibility-policy, or selector changes.
- Treat historical CI, prior reports, and repository inspection as discovery until current artifacts and selected validation confirm them.
- Limit schema-diff claims to described structure and compatibility rules; name semantic, unknown-consumer, traffic, and rollout gaps separately.
- Limit generated-client claims to the generated/runtime versions and call sites actually compiled or exercised.
- Limit fixture replay to captured cases; disclose unrecorded errors, optional fields, rate behavior, and provider drift.
- Close with covered versions and consumers, fresh proof, non-proof boundaries, residual owner, and next gate.
