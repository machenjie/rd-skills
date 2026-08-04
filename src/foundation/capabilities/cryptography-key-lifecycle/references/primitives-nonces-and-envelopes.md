# Primitives, Nonces, And Envelopes

**Load when:** Algorithm, mode, AEAD, AAD, nonce/IV, key wrapping, hierarchy, or ciphertext-envelope choices remain unresolved.

**Do not load when:** Authoritative policy and the selected library already fix a complete construction and envelope without changed lifecycle behavior.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `selected-approach`, `boundary-decision`, `proof-limit`

## One Decision

Select one policy-approved construction and self-describing envelope whose authenticity, construction-specific nonce safety, parsing, and key hierarchy survive the supported writer and reader set.

## Decision Matrix

| Boundary | Required decision | Failure signal |
|---|---|---|
| Authority | Current policy, qualified reviewer, approved library/provider, and revision date | Familiarity substitutes for approval |
| Construction | Algorithm, mode, parameters, key purpose, limits, and rejection behavior | Primitive name omits mode or parameters |
| Nonce/IV | Construction and policy requirements; per-key domain, formation, allocator or permitted-reuse rule, concurrency, restart, exhaustion, and misuse-resistance limits | Uniqueness is assumed universally, or permitted reuse is inferred without construction-specific approval |
| AAD | Canonical fields, encoding, purpose, tenant/object binding, and version | Context is mutable or ambiguously encoded |
| Hierarchy | Data key, wrapping key, root boundary, identities, permissions, and separation | One broadly exportable key protects everything |
| Envelope | Format, algorithm/parameter version, key IDs, wrapped key, nonce, tag, AAD contract, and ciphertext | Reader guesses any cryptographic input |
| Decrypt | Parse bounds, key/version resolution, authentication-before-use, and safe failure | Partial plaintext escapes on failure |

## Verification

- Run authoritative library/provider vectors for the exact construction.
- Where uniqueness is required, detect duplicate nonce allocation across concurrency, restart, restore, and retained-key scope; otherwise exercise the construction's approved repeat/reuse cases and documented bounds.
- Modify each envelope field, ciphertext, tag, nonce, AAD field, and key/version identifier.
- Cross-read the supported writer/reader matrix and reject malformed or unsupported envelopes.

## Primary Sources

- [NIST SP 800-38D: GCM and GMAC](https://csrc.nist.gov/pubs/sp/800/38/d/final)
- [NIST SP 800-38F: Key Wrapping](https://csrc.nist.gov/pubs/sp/800/38/f/final)
- [FIPS 197: Advanced Encryption Standard](https://csrc.nist.gov/pubs/fips/197/final)
- [RFC 9771: Properties of AEAD Algorithms](https://www.rfc-editor.org/rfc/rfc9771.html)
- [AWS KMS cryptography essentials](https://docs.aws.amazon.com/kms/latest/developerguide/kms-cryptography.html)

Official sources were accessed on 2026-07-26.

## Proof Limits

Standards do not select an organization's approved construction or prove a library integration. Nonce uniqueness is not a universal requirement across all approved constructions; the selected construction and policy define the required uniqueness, permitted reuse, and misuse-resistance limits. AWS envelope behavior is product-specific. GCM guidance is under revision; use the cited final plus current policy and qualified review, never draft status as approval.
