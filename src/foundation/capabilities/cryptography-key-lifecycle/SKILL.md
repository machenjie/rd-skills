---
name: cryptography-key-lifecycle
description: "Use for cryptographic construction, envelopes, key lifecycle, compromise, destruction, or agility. Skip secrets, authentication, provider APIs, custom primitives, and compliance."
---

# cryptography-key-lifecycle

## Registry Trigger

**Use when**

- A boundary selects cryptography or changes key lifecycle.
- Nonce, envelope, recovery, compromise, destruction, or deprecation changes.

**Do not use when**

- Route generic secret/config storage to `secret-configuration-security`.
- Route auth-only tokens/password hashing elsewhere.
- Keep provider APIs targeted; never invent primitives or claim compliance.

## Skill Role

Own policy-approved construction and lifecycle.

## High-Value Rules

- Require policy, platform support, approved implementation, and qualified review.
- Bind construction/envelope/key authority/version/recovery/plaintext release.
- Select named References for coupled construction, transition, or compromise decisions.

## Anti-Patterns

- Do not invent primitives or infer compliance/provider guarantees from a local round trip.

## Execution Checklist

- Fault the applicable nonce allocation or reuse policy and rotation across concurrency, restart, rollback, and mixed versions.

## Stop Conditions

- Stop without policy/review/construction/nonce authority/decrypt inventory/recovery/destructive authority.
- Route compliance and provider claims to their owners.

## Output Contract

- cryptographic lifecycle decision with policy, construction, applicable nonce policy, identity, envelope, rotation, recovery, compromise, destruction, agility, evidence limits, and owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [primitives nonces and envelopes](references/primitives-nonces-and-envelopes.md) | targeted | Algorithm mode AEAD AAD nonce IV key wrapping or ciphertext envelope remains unresolved | Current approved construction and complete envelope contract are already fixed | analysis-agent, task-agent, review-agent | selected-approach, boundary-decision, proof-limit |
| [rotation versioning and recovery](references/rotation-versioning-and-recovery.md) | targeted | Key versions rotation rewrap re-encryption decrypt compatibility backup recovery or escrow changes | No key transition or decryptability boundary changes | analysis-agent, task-agent, review-agent | boundary-decision, validation-plan, proof-limit |
| [compromise destruction and agility](references/compromise-destruction-and-agility.md) | targeted | Compromise revocation destruction cryptographic erasure deprecation or migration changes | No incident destructive or algorithm-transition decision changes | analysis-agent, task-agent, review-agent | failure-decision, boundary-decision, residual-risk |
