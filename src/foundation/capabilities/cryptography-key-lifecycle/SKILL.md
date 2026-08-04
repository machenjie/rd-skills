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

Define cryptographic lifecycle under authoritative policy without implementing primitives.

## High-Value Rules

- Require authoritative policy, threat/lifetime, platform support, and qualified review before selecting algorithms, modes, parameters, or cryptoperiods.
- Select approved libraries/providers and record algorithm, parameter, purpose, format versions, authentication, and plaintext-release conditions.
- Record construction-specific nonce/IV policy: per-key domain, allocation, concurrency, restart, exhaustion, retention, and proof where uniqueness is required, or documented reuse and misuse-resistance bounds for approved constructions.
- Define AAD, data/wrapping-key hierarchy, identities, permissions, envelope metadata, and trust boundaries with canonical mismatch rejection.
- Separate generation, storage, cryptographic operations, administration, recovery, and audit authority.
- Define rotation and recovery through encrypt/decrypt sets, version routing, rollout, rollback, adoption, rewrap/re-encryption, retirement, provenance, and restore evidence.
- Bound compromise response across affected material, containment, revocation, replacement, recovery, re-protection, and preserved evidence.
- Gate destruction and deprecation on dependency, decryptability, recovery, algorithm, key, ciphertext, library, protocol, and consumer inventories.

## Anti-Patterns

- Nonce handling violates the selected construction's uniqueness, reuse, or misuse-resistance contract.
- An unauthenticated mode permits undetected modification.
- Wrong AAD or context accepts data across boundaries.
- Key and data versions mismatch.
- Rotation removes the only decrypt path.
- Recovery material is inaccessible when required.
- A revoked key remains usable or retained unexpectedly.
- Destruction causes irreversible data loss.
- Algorithm deprecation leaves an unknown consumer.

## Execution Checklist

- Test valid decrypt and altered ciphertext, tag, AAD, nonce, key identity, and version.
- Fault the applicable nonce allocation or reuse policy and rotation across concurrency, restart, rollback, and mixed versions.
- Rehearse recovery, compromise, revocation, destruction safeguards, re-protection, and deprecation migration.

## Stop Conditions

- Stop without authoritative policy or qualified cryptographic review.
- Stop on an unproved applicable nonce policy, including uniqueness where required, unsupported primitives, unknown decrypt inventory, unsafe recovery, or destruction authority.
- Stop compliance claims and provider guarantees not established by their owners.

## Output Contract

- cryptographic lifecycle decision with policy, construction, applicable nonce policy, identity, envelope, rotation, recovery, compromise, destruction, agility, evidence limits, and owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [primitives nonces and envelopes](references/primitives-nonces-and-envelopes.md) | targeted | Algorithm mode AEAD AAD nonce IV key wrapping or ciphertext envelope remains unresolved | Current approved construction and complete envelope contract are already fixed | analysis-agent, task-agent, review-agent | selected-approach, boundary-decision, proof-limit |
| [rotation versioning and recovery](references/rotation-versioning-and-recovery.md) | targeted | Key versions rotation rewrap re-encryption decrypt compatibility backup recovery or escrow changes | No key transition or decryptability boundary changes | analysis-agent, task-agent, review-agent | boundary-decision, validation-plan, proof-limit |
| [compromise destruction and agility](references/compromise-destruction-and-agility.md) | targeted | Compromise revocation destruction cryptographic erasure deprecation or migration changes | No incident destructive or algorithm-transition decision changes | analysis-agent, task-agent, review-agent | failure-decision, boundary-decision, residual-risk |
