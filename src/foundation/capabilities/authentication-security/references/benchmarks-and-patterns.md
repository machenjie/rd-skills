# Authentication Security Benchmarks And Patterns

Use this reference when an authentication-security output needs more detail than the `SKILL.md` body can carry efficiently. Keep the main skill body focused on routing, lifecycle decisions, evidence obligations, and quality gates.

## Benchmark Anchors

- NIST SP 800-63B for Authenticator Assurance Levels, password rules, authenticator lifecycle, replay resistance, verifier impersonation resistance, and phishing resistance.
- OWASP Authentication Cheat Sheet and Session Management Cheat Sheet for password storage, enumeration defense, session fixation, cookie attributes, and logout/revocation controls.
- OWASP ASVS V2, V3, and V6 for authentication, session management, and cryptographic verification requirements.
- FIDO2 and WebAuthn for origin-bound phishing-resistant authentication, especially passkeys and hardware security keys.
- OAuth 2.0 Security BCP, PKCE, OIDC Core, OIDC Session Management, JWT BCP, token revocation, and token exchange for delegated and federated identity flows.
- PCI-DSS v4 section 8, HIPAA technical safeguards, GDPR Article 32, and BSI TR-02102 when authentication controls protect regulated or high-value data.
- Have I Been Pwned Pwned Passwords k-anonymity API for breached-password screening without exposing full password material.

## MFA Method Selection

| Method | Phishing resistant | Replay resistant | Operational use | Recommendation |
| --- | --- | --- | --- | --- |
| Passkeys / WebAuthn platform authenticator | Yes, origin-bound | Yes | Broad consumer or workforce login | Default for new high-assurance flows. |
| FIDO2 hardware security key | Yes, origin-bound | Yes | Admin, privileged workforce, break-glass | Require for high-risk admin where feasible. |
| TOTP authenticator app | No | Mostly | General second factor | Acceptable fallback when passkeys are not available. |
| Push with number matching | Partial | Yes | Workforce and mobile-first flows | Acceptable; rate-limit prompts and log fatigue signals. |
| Push tap-to-approve | No | Yes | Legacy MFA | Replace or wrap with number matching; vulnerable to fatigue. |
| SMS OTP | No | Mostly | Account recovery or low-assurance fallback | Fallback only; sim-swap and SS7 risks. |
| Email OTP | No | Mostly | Low-risk verification | Low assurance; email is often the recovery vector. |
| Security questions | No | No | Legacy recovery | Do not use; answers are guessable and often public. |

## Session And Token Strategy Matrix

| Strategy | Storage | Revocation behavior | Scaling tradeoff | Pick when |
| --- | --- | --- | --- | --- |
| Server-side opaque session id in HttpOnly cookie | Server DB or Redis | Immediate by deleting session row | Requires shared session store | Browser apps, monoliths, and products needing immediate revocation. |
| Short-lived JWT access token plus opaque refresh token | Access token client-held; refresh token server row | Access valid until expiry; refresh revoked server-side | Scales API reads but accepts short revocation window | SPA/mobile APIs when refresh-token controls are strong. |
| JWT with revocation or denylist | Client-held JWT plus revoked `jti` cache | Immediate after denylist check | Adds lookup per request | High-risk systems needing fast revocation and distributed verification. |
| Token introspection | Authorization server is source of truth | Immediate at introspection point | Network dependency and cache decision | Multi-service systems with central auth and clear latency budget. |
| Sender-constrained tokens using DPoP or mTLS | Token bound to client key | Revocation plus proof-of-possession limits replay | More client complexity | High-value APIs, open banking, payments, and machine clients. |

## Refresh Token Rotation Pattern

```text
If refresh tokens are issued:
1. Store only a hashed token value with token family, subject, client, device, creation, consumed, and expiry metadata.
2. On refresh, atomically mark the old token consumed and issue a new access token plus a new refresh token.
3. If a consumed token is presented, treat it as theft: invalidate the whole family, force re-authentication, alert, and notify the user.
4. Enforce idle lifetime and absolute lifetime; sliding renewal cannot exceed the absolute cap.
5. Bind refresh token to client_id and, where risk justifies, device signal or sender-constrained key.
```

Reject static long-lived refresh tokens unless the risk is explicitly accepted by a security owner with compensating controls and expiry.

## Cookie Attribute Decisions

| Flow | Recommended attributes | Watchout |
| --- | --- | --- |
| Same-origin app and API | `__Host-session=...; HttpOnly; Secure; SameSite=Lax; Path=/` | Avoid `Domain` unless cross-subdomain sharing is required. |
| Sensitive same-site workflow | `HttpOnly; Secure; SameSite=Strict; Path=/` | Strict can break some SSO or cross-site callback flows. |
| OAuth/OIDC callback helper cookie | Short `Max-Age`, `HttpOnly`, `Secure`, `SameSite=Lax` | Callback state/nonce must be validated and one-time. |
| Cross-site embedded app | `SameSite=None; Secure; HttpOnly; Partitioned` when supported | Requires CSRF and framing review. |
| Remember-me token | Separate long-lived cookie, server-side row, single-use rotation | Never reuse the session id value. |

## Federation And Client Integration Checks

- OAuth public clients use PKCE; never embed `client_secret` in SPA or mobile apps.
- Redirect URIs are exact matches; no wildcard, path-prefix, open redirect, or user-controlled `next` target.
- OIDC uses `state` for auth-flow CSRF protection and `nonce` for id-token replay protection.
- JWT verifiers pin the expected algorithm, validate signature, issuer, audience, expiry, not-before, and key id.
- JWKS key rotation keeps old keys until the longest accepted token lifetime expires and rejects unknown algorithms.
- Social login linking is explicit; verified email at the provider is necessary but not sufficient for automatic account linking.
- SAML uses a hardened library, signature wrapping protections, pinned signing certificate, and validated audience/recipient/destination.
- Federated logout behavior is documented; app logout and IdP logout are separate unless SLO/RP-initiated logout is implemented.

## Evidence Patterns

- Login/session flow: flow diagram names issuance, cookie attributes, session regeneration points, timeout caps, logout revocation, and negative fixation test.
- Refresh-token design: lifecycle table names token family, one-time rotation, reuse detection, absolute lifetime, notification, and validator output.
- MFA/step-up: policy matrix maps actions to required `acr`, `auth_time` freshness, allowed factors, recovery fallback, and bypass tests.
- Account recovery: reset token is single-use and short-lived, enrolled MFA is respected, sessions/devices are invalidated, and notification is sent.
- Federation: provider config, redirect allowlist, state/nonce tests, algorithm pinning, and cert/key rotation evidence are all current.
- Compromise repair: same-pattern scan covers all issuers/verifiers/clients, revocation and rotation are proven, and user/security notifications have owners.

## Anti-Patterns To Reject

| Anti-pattern | Why it fails | Required correction |
| --- | --- | --- |
| Refresh token has no rotation and no family invalidation. | Stolen bearer token remains valid until distant expiry. | Rotate on every use and invalidate family on consumed-token reuse. |
| Logout only clears the browser cookie. | Server-side token/session remains valid and can be replayed. | Revoke session or refresh token at the authoritative store. |
| Session id survives login or MFA. | Attacker can fix a known id before victim authenticates. | Regenerate id after login, MFA, and privilege elevation. |
| MFA recovery bypasses enrolled MFA. | Account takeover moves to the weakest recovery channel. | Treat recovery as a high-risk auth flow with step-up, audit, and notification. |
| JWT verifier trusts token `alg`. | Algorithm confusion can accept unsigned or wrongly signed tokens. | Pin allowed algorithm server-side and validate issuer/audience/expiry. |
| OAuth redirect allows wildcard or path prefix. | Open redirect enables code or token theft. | Exact redirect URI matching and negative callback tests. |
| Token appears in URL, analytics, crash report, or log. | Bearer credential leaks through history, referrer, or third-party processors. | Use headers/cookies, redact token shapes, and rotate if leaked. |
| Service account credential never rotates. | A leaked machine credential remains useful indefinitely. | Rotate on schedule, scope to purpose, audit use, and alert on anomalies. |

## Validation Checklist

Before handoff, map every changed authentication surface to evidence:

1. Session and cookie change -> cookie attribute assertion plus fixation/regeneration test.
2. Access token change -> signature, issuer, audience, expiry, not-before, and algorithm-confusion test.
3. Refresh token change -> rotation, reuse detection, family invalidation, and revocation test.
4. Password policy change -> KDF parameter review, breach-screening behavior, enumeration timing/message check.
5. MFA change -> positive factor test, bypass attempt, fatigue/rate-limit check, and recovery fallback review.
6. Account recovery or email change -> single-use token, expiration, step-up, notification, and session invalidation test.
7. Federation change -> redirect allowlist, state/nonce, PKCE, cert/key validation, and provider callback negative test.
8. Service credential change -> scope, storage, rotation, audit, and unusual-use alert evidence.
