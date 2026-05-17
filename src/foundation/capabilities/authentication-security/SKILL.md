---
name: authentication-security
description: Reviews authentication token lifecycle, refresh, rotation, revocation, session fixation, MFA, cookie flags, and credential storage.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "55"
changeforge_version: 0.1.0
---

# Mission

Secure authentication flows and session material across **issuance, transport, storage, refresh, rotation, revocation, fixation prevention, multi-factor controls, account recovery, device trust, federation, and audit** — so that credentials and tokens cannot silently outlive their intended lifecycle, be replayed after compromise, or escalate privilege through recovery paths.

# When To Use

Use this capability when a change touches: login, logout, sessions, cookies, access/refresh/id tokens, OAuth 2.0 / OIDC / SAML flows, password creation or change, password reset, magic-link, passkey/WebAuthn, MFA enrollment or verification, step-up authentication, account recovery, device trust / remembered devices, service credentials (API keys, mTLS, signed JWTs), identity provider integration, social login linking, session timeout, concurrent session limits, or any flow that issues, refreshes, or revokes authentication material.

# Do Not Use When

Do not use this capability to treat a successful login as authorization for every action — that is `authentication-authorization`. Do not use it to design RBAC/ABAC policy or object-level access — also `authentication-authorization`. Do not use it for application secret storage (database passwords, third-party API keys not user-bound) — use `secret-configuration-security`.

# Non-Negotiable Rules

- **Password storage** uses a memory-hard, salted KDF: **Argon2id (preferred)**, **scrypt**, or **bcrypt (cost ≥ 12)**. SHA-256/MD5/PBKDF2-SHA1 are insufficient for new systems. Never roll your own.
- **Passwords**: minimum length ≥ 8 (NIST 800-63B-3 §5.1.1.2), no composition rules, screen against **breached-password lists (Have I Been Pwned k-anonymity API)** at set/change time, allow up to 64+ characters, allow all printable Unicode.
- **MFA**: required for admin, payment, account-security changes, and account recovery. Prefer **WebAuthn / passkeys (FIDO2)** over TOTP; TOTP over SMS; **SMS only as fallback** (SS7-vulnerable, sim-swap). Disallow MFA = email-OTP for anything > medium risk.
- **Session id / token regeneration** is mandatory after: successful login, privilege elevation, MFA step-up, password change. Reusing the pre-login session id = **session fixation**.
- **Access tokens**: short-lived (typically 5–30 min), signed (asymmetric preferred — RS256/ES256/EdDSA), **never `alg: none`**, key id (`kid`) required, validate issuer/audience/expiry/notBefore.
- **Refresh tokens**: **rotated on every use** (one-time use); stolen-token detection on re-use of consumed refresh token → invalidate the entire token family + alert.
- **Logout** must revoke server-side session/refresh-token; client-side cookie clear alone is not logout.
- **Cookies** carrying session/auth: `HttpOnly`, `Secure`, `SameSite=Lax` minimum (`Strict` where flow allows), explicit `Path`, narrow `Domain`, **no `Domain` attribute** unless cross-subdomain is required (broader scope = bigger leak), `__Host-` prefix preferred.
- **Tokens MUST NOT appear** in URLs (logged everywhere), query strings, browser history, `Referer` headers, analytics payloads, error reports, or build artifacts.
- **Account recovery** = high-risk authentication flow: same rate limits, audit, notification, MFA-where-enrolled, and session invalidation as login.
- **Password reset** invalidates: existing sessions (configurable, default yes for security-sensitive products), refresh tokens, remembered devices, and current MFA recovery codes (regenerate).
- **Brute force protection**: per-account + per-IP + global rate limiting; exponential backoff; CAPTCHA or proof-of-work after threshold; **never** silent denial that allows enumeration timing.
- **Username enumeration**: identical response time and message for "user not found" vs "wrong password" vs "account locked".
- **Auditable events**: login success, login failure (with category), MFA success/failure, password change, password reset request, password reset completion, MFA enrollment/removal, recovery code use, session creation, session revocation, suspicious activity. **Never log secrets or reusable tokens**; hash for correlation (`sha256(token)[:16]`).
- **Notify users** of: new device login (geo/UA), password change, MFA change, email change, new active session, recovery initiated. Provide a "revoke" action.
- **Token signing keys** rotated regularly (≤ 90 days) with key set (JWKS) published for verifiers; old key kept until max token lifetime expires.

# Industry Benchmarks

Anchor against: **NIST SP 800-63B Rev. 3 / 4-draft** (Authenticator Assurance Levels AAL1/2/3, password rules, MFA requirements), **OWASP Authentication Cheat Sheet**, **OWASP Session Management Cheat Sheet**, **OWASP ASVS v4** chapters V2 (Authentication), V3 (Session Management), V6 (Cryptography); **FIDO2 / WebAuthn Level 2/3** for phishing-resistant auth (now the gold standard for high-assurance consumer and workforce auth — Apple/Google/Microsoft passkey rollout); **OAuth 2.0 Security BCP (RFC 9700)** — note its explicit prohibitions: no implicit flow, PKCE for all clients, exact redirect URI matching; **OIDC Core 1.0** + **OIDC Session Management**; **JWT BCP (RFC 8725)** — algorithm pinning, audience binding, no `alg: none`; **RFC 7009** Token Revocation; **RFC 8693** Token Exchange (for delegation); **RFC 7591/7592** Dynamic Client Registration if used; **PCI-DSS v4 §8** (authentication for cardholder-data systems); **HIPAA §164.312(a)(2)(i)** for healthcare; **GDPR Art. 32** for personal data; **BSI TR-02102** for crypto choice (EU). For breached-password screening: **Have I Been Pwned Pwned Passwords v3 API (k-anonymity)**. For MFA strength ranking: **NIST 800-63B Table 6-1** (phishing resistance, replay resistance, verifier impersonation resistance).

### MFA Method Selection

| Method | Phishing resistant | Replay resistant | UX | Recommendation |
| --- | --- | --- | --- | --- |
| **Passkeys / WebAuthn (platform or roaming)** | ✓ (origin-bound) | ✓ | Best | **Default for new systems** |
| **Hardware security key (FIDO2)** | ✓ | ✓ | Good | Admin / high-risk |
| **TOTP (Authenticator app, RFC 6238)** | ✗ (phishable) | ✓ | Good | Acceptable second factor |
| **Push notification (with number matching)** | Partial | ✓ | Best | Acceptable; require number matching to defeat MFA fatigue |
| **Push notification (tap-to-approve)** | ✗ | ✓ | Best | **Deprecated** — MFA fatigue attacks |
| **SMS OTP** | ✗ | ✓ | OK | **Fallback only**; sim-swap + SS7 risk |
| **Email OTP** | ✗ | ✓ | OK | **Low assurance**; email is often the recovery vector |
| **Security questions** | ✗ | ✗ | Poor | **Banned by NIST 800-63B**; do not use |

### Session vs Token Strategy Matrix

| Strategy | Storage | Revocation | Scaling | Pick when |
| --- | --- | --- | --- | --- |
| **Server-side opaque session id** in HttpOnly cookie | Server DB / Redis | Immediate (delete row) | Requires shared session store | Browser apps, monolith, need immediate revocation |
| **Stateless JWT access token** (short-lived) + opaque refresh in HttpOnly cookie | Client-held JWT; refresh in DB | Access: wait for expiry (5–30 min). Refresh: revoke in DB | Stateless API, no shared session | API + SPA / mobile; accept short revocation window |
| **JWT + revocation list (denylist)** | DB cache of revoked `jti` | Immediate | Adds a check per request | Need both stateless and immediate revocation |
| **Token introspection (RFC 7662)** | Authorization server | Immediate | Adds network call per request | Multi-service with central auth |
| **Sender-constrained tokens (DPoP RFC 9449 / mTLS RFC 8705)** | Bound to client key | Immediate via revocation | More client complexity | High-value APIs (open banking, payments) |

### Decision Tree: Refresh Token Strategy

```
Are refresh tokens issued?
├─ No → Re-auth at each access-token expiry (acceptable for high-security / short-session products).
└─ Yes →
    Are refresh tokens single-use (rotated)?
    ├─ No  → REJECT design. Long-lived static refresh = persistent compromise.
    └─ Yes →
        On every refresh:
          1. Issue new access + new refresh.
          2. Mark old refresh consumed.
          3. If a CONSUMED refresh is presented again → token theft signal:
             - Invalidate the entire refresh token family for that subject.
             - Force re-authentication.
             - Notify user + audit.
        Refresh token absolute lifetime: ≤ 30–90 days; sliding renewal allowed within absolute cap.
        Bind refresh token to: client_id, optionally device fingerprint, optionally DPoP key.
```

### Cookie Attribute Decision

| Flow | Recommended attributes |
| --- | --- |
| Same-origin SPA + API | `__Host-session=...; HttpOnly; Secure; SameSite=Lax; Path=/` |
| Cross-site embed (allowed) | `SameSite=None; Secure; HttpOnly; Partitioned` (CHIPS) |
| OAuth/OIDC callback cookies | Short-lived (`Max-Age` minutes), `HttpOnly`, `Secure`, `SameSite=Lax` |
| Remember-me token | Separate cookie, longer-lived, **bound to a server-side row**, single-use rotation |

# Selection Rules

Select this capability when **identity proof or session material** is primary. Adjacent routing:

- Prefer `authentication-authorization` for action permission enforcement after identity is proven.
- Prefer `web-security` for browser-specific controls (CORS, CSRF, CSP, clickjacking, headers).
- Prefer `secret-configuration-security` for application secrets not bound to user identity.
- Prefer `threat-modeling` for broader account-takeover threat surface analysis.
- Use **with** `input-validation` for credential input handling and `logging-error-handling` for audit-safe diagnostics.

# Risk Escalation Rules

Escalate when authentication affects: admin access, payment actions, regulated data (PII/PHI/PCI), social-login account linking (account takeover via stale email reclaim), account recovery (often the weakest link), long-lived tokens (> 24h), device trust persistence, service accounts with elevated scopes, cross-domain or cross-subdomain cookies, federated identity (SAML/OIDC IdP trust changes), or any deviation from MFA on sensitive flows. Escalate any new authentication flow that does not have a security review and threat model.

# Critical Details

Authentication security is **lifecycle control**. Issuing a token safely is not enough if refresh, logout, revocation, storage, or privilege changes leave old credentials valid. Apply these refinements:

- **Session fixation.** Always regenerate session id after authentication; otherwise attacker pre-sets a known id, victim authenticates, attacker uses it. OWASP A07:2021.
- **Recovery flow = authentication flow** with often weaker controls. Most account takeovers happen via recovery, not login. Apply login-grade rate limits, audit, MFA-where-enrolled, and out-of-band notification.
- **Email change is a privileged action.** Confirm via both old and new email; rate limit; require step-up; treat as identity transfer.
- **Social login account linking** is dangerous: a stale email at the OAuth provider reclaimed by an attacker → "Continue with Google" → account takeover. Require explicit linking, verified email at link time, and protective UX.
- **Magic links** must be: single-use, short-lived (≤ 10 min), tied to the originating browser session (cookie or query nonce), invalidated on use, and never sent to a different email than the request.
- **Passwordless / OTP** does not eliminate phishing; passkeys do (origin binding). Prefer passkeys; if OTP, add additional context.
- **Concurrent session policy.** Decide and document: unlimited, per-device, single (force logout others on new login)? Most consumer products: unlimited with visibility + remote-revoke; banking: typically single.
- **Remember-me tokens** are long-lived bearer credentials. Bind to a database row; rotate on use; revoke on password change; never use the same value as the session id.
- **Token compromise detection.** Re-use of consumed refresh tokens, simultaneous use from impossibly distant geos, sudden change in user-agent fingerprint — these are signals; alert and force re-auth.
- **Step-up authentication.** Sensitive actions require MFA within the last N minutes (typically 5–15). Carry an `auth_time` claim; enforce `acr` (Authentication Context Class Reference) per action.
- **MFA fatigue attack** (push bombing): mitigate with number matching (Microsoft, Okta, Duo all support); rate-limit push prompts.
- **SSO and IdP-initiated SAML** carries known XSW (XML Signature Wrapping) risk; use a hardened library and pin signing cert.
- **OAuth client_secret** is not a secret in a public client (SPA, mobile). Use PKCE only; never embed client_secret in distributable code.
- **Open redirect** in OAuth `redirect_uri` is a token-theft vector; require exact-match (no wildcard, no path-prefix match).
- **State / nonce** parameters are not optional in OAuth/OIDC; without `state` you have CSRF in the auth flow; without `nonce` you have id-token replay.
- **Token introspection cache.** If introspecting on every request, cache briefly (seconds) with respect for revocation latency.
- **Service account credentials** are bearer tokens with no human in the loop; rotate quarterly, audit usage, alert on unusual scope.
- **Crypto agility.** JWS `kid` + JWKS endpoint; multiple active keys during rotation; signed-by-old verified by both during rollover.
- **Algorithm pinning.** Verify the `alg` is the **expected** algorithm — not what the token claims. RS256 verifier must not be tricked into HS256 verification with the public key as HMAC secret (classic JWT bug).
- **Audience binding.** Always validate `aud` claim. A token issued for service A must not be accepted by service B.
- **Clock skew.** Allow ≤ 60 s skew for `exp`/`nbf`; do not allow more — gives replay window.
- **MFA recovery codes** are bearer credentials; store hashed; show once; rotate on use; do not allow infinite generations.
- **Federated logout (OIDC RP-initiated logout / front-channel / back-channel)** is non-trivial; without it, logging out of the app does not log out of the IdP, and the next "Sign in with X" silently re-authenticates.
- **Crash reports, analytics, CI logs, browser extensions** are token leakage surfaces. Redact known token shapes; review SDKs.

# Failure Modes

- Refresh tokens never rotate and remain usable after theft.
- Logout clears the browser cookie but does not revoke server-side session/refresh.
- Session id is not regenerated after login or privilege elevation → session fixation.
- Cookies lack `Secure`, `HttpOnly`, or appropriate `SameSite` → XSS exfil or CSRF.
- Password reset grants access without invalidating old sessions; attacker holding stolen session remains in.
- Tokens appear in logs, URLs, query strings, analytics, crash reports, `Referer` headers.
- Password storage uses SHA-256, MD5, unsalted, or low-cost bcrypt → cracking on breach is hours.
- "User not found" vs "wrong password" differ in response or timing → username enumeration.
- Brute force protection per-IP only → attacker rotates IPs; per-account only → distributed credential stuffing succeeds.
- MFA is offered but not enforced for sensitive actions; bypassable via recovery flow.
- SMS OTP used as primary MFA; sim-swap takes over high-value accounts.
- Social login automatically links accounts by email without verification → takeover via email reclaim.
- Magic link sent to wrong email or reused; token leaks via mail forwarder.
- JWT verifier accepts `alg: none` or HS256-with-RSA-public-key (classic).
- `aud` claim not validated → token issued for service A accepted by service B.
- Refresh token absolute lifetime never enforced → token issued in 2022 still valid.
- Service account credentials never rotated; embedded in code; leaked in public repo.
- OAuth `redirect_uri` allows path-prefix or wildcard → token exfil via open redirect.
- IdP-initiated SAML without signature validation hardening → assertion forgery.
- Logout endpoint reachable via `GET` and CSRF-able → forced-logout DoS.
- Concurrent session policy undefined → leaked credential remains usable indefinitely.

# Output Contract

Return an authentication security review with:

- `identity_sources` (internal credentials, OIDC/OAuth providers, SAML IdPs, passkey relying-party id)
- `credential_storage` (hash algorithm + parameters; service-account key storage)
- `password_policy` (min length, breach screening source, prohibited substring rules, history)
- `session_or_token_model` (session id vs JWT vs hybrid; lifetimes; absolute caps; sender-constrained?)
- `refresh_strategy` (rotation, family-invalidation-on-reuse, absolute lifetime)
- `mfa_policy` (which actions require MFA, AAL level, accepted methods, fallback hierarchy, number matching)
- `step_up_rules` (per sensitive action: required `acr` and `auth_time` freshness)
- `cookie_attributes` (per cookie: HttpOnly, Secure, SameSite, Path, Domain, prefix, lifetime)
- `session_lifecycle` (fixation regeneration points, idle timeout, absolute timeout, concurrent sessions)
- `logout_behavior` (server-side revocation, federated/SLO, device-wide revoke)
- `recovery_flow` (email/SMS/passkey; rate limits; MFA-during-recovery; notification; session invalidation on completion)
- `email_change_flow` (dual-confirmation, step-up, audit, notification to old address)
- `brute_force_controls` (per-account + per-IP + global limits, lockout policy, CAPTCHA threshold)
- `enumeration_controls` (uniform response and timing across user-found/not-found/locked)
- `compromise_detection` (re-used refresh, impossible-travel, device fingerprint anomaly, MFA fatigue triggers)
- `audit_events` (schema, retention, secret redaction strategy)
- `user_notifications` (channels, events covered, opt-out policy)
- `token_signing_keys` (algorithm, rotation schedule, JWKS endpoint, dual-active window)
- `crypto_choices` (KDF parameters, algorithm pinning, audience validation, clock-skew tolerance)
- `tests` (positive flows + replay, fixation, enumeration, brute force, recovery hijack, JWT confusion, refresh reuse detection, MFA bypass attempts)
- `residual_risks` and `owner`

# Quality Gate

The review passes only when:

1. Credential storage uses an approved memory-hard KDF with documented parameters.
2. Password policy follows NIST 800-63B (length over composition; breach screening).
3. Session id / token is regenerated at every privilege change and after login.
4. Refresh tokens are single-use with reuse-detection and bounded absolute lifetime.
5. Logout revokes server-side; federated logout addressed where applicable.
6. MFA is enforced (not just offered) on sensitive actions; phishing-resistant method available.
7. Recovery flow has login-grade controls and notification.
8. Cookies have correct attributes per flow; tokens never appear in URLs/logs/analytics.
9. Brute force, enumeration, and MFA fatigue are mitigated.
10. JWT verifier pins algorithm, validates audience/issuer/expiry, has clock-skew limit; signing keys rotate.
11. Audit events redact secrets; user notifications cover the canonical sensitive events.
12. Negative-path tests exist (replay, fixation, enumeration, refresh reuse, recovery hijack).

# Used By

- security-privacy-gate
- backend-change-builder

# Handoff

Hand off to `authentication-authorization` for permission decisions after identity is proven; `web-security` for CSRF/CORS/CSP/clickjacking controls; `secret-configuration-security` for non-user secret handling; `logging-error-handling` for audit-safe diagnostics; `threat-modeling` for account-takeover threat enumeration; `frontend-testing` for login/MFA UX flows.

# Completion Criteria

The capability is complete when authentication material **cannot silently outlive its intended lifecycle**, recovery and high-risk identity actions have appropriate verification and audit, compromise is detected and contained, and the documented controls map cleanly to NIST 800-63B AAL targets and OWASP ASVS V2/V3 requirements appropriate to the system's risk class.
