# Contract Testing Evidence Patterns

These records bound compatibility claims to the named providers, consumers, versions, and observed behavior.

## Current Claim Records

- Name provider, consumer classes, operation/message, contract source, versions, compatibility direction, and rollout or replay boundary.
- Record fresh provider verification and named consumer parse/compile/behavior results, including fixture/generated input and unrepresented consumers.
- Record old/new writer-reader cases, retained/replayed payload provenance, registry/broker subject and policy, external capture environment/time/version, redaction, and drift trigger.
- Refresh after contract, fixture, generator, compatibility-policy, selector, or consumer changes.

## Proof Limits

Limit schema checks to the configured structure/reader-writer rules; generated proof to the exercised versions/calls; captures to the observed cases; provider checks to the named expectations. Disclose unknown consumers, semantic/error/authorization gaps, unavailable environments, traffic/rate behavior, rollout gaps, residual owner, and next gate.

## Anti-Patterns

- Declaring compatibility from schema shape alone while semantic meaning, error behavior, or consumer tolerance changed.
- Inventing a vendor or consumer mock from memory, or treating one captured response as the provider's complete behavior.
- Applying one broker, registry mode, versioning style, or consumer-driven workflow to every boundary.
- Replacing integration, journey, consumer discovery, or rollout proof with contract tests.
