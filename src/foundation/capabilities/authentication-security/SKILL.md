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

# Stage Fit

Use during planning when a login, MFA, account recovery, identity-provider, cookie, service credential, or token lifecycle decision is being designed; during coding when issuance, refresh, revocation, storage, or step-up implementation is changed; during code-review when a patch can weaken credential lifecycle, session fixation prevention, token validation, or recovery controls; during testing when replay, enumeration, brute-force, JWT confusion, recovery hijack, or MFA bypass evidence is required; and during release when key rotation, session invalidation, user notification, audit-event, or federated logout behavior must be handed off. Skip this capability for pure authorization policy matrices, general web exploit review, or non-user-bound secret storage unless those surfaces also change authentication material.

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

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| New or changed login/session flow | Login, logout, cookie, session store, passwordless, magic link, or remember-me change. | Lifecycle design: issuance, storage, fixation prevention, idle/absolute timeout, logout, and revocation. | Flow map, cookie/session attributes, regeneration points, revocation behavior, negative tests. | `web-security`, `logging-error-handling`, `quality-test-gate` | Authorization policy matrix work. |
| Token lifecycle and JWT validation | Access/refresh/id token, JWKS, `kid`, audience, issuer, token exchange, or introspection change. | Short lifetime, rotation, reuse detection, algorithm pinning, audience binding, revocation latency. | Token claims, lifetime table, signing algorithm, key rotation plan, replay/JWT-confusion tests. | `secret-configuration-security`, `integration-change-builder` | Treating token claims as permission design. |
| MFA, step-up, and recovery | MFA enrollment/removal, recovery code, password reset, email change, device trust, high-risk action. | Prevent account takeover through weaker recovery or stale authentication. | AAL target, factor hierarchy, `auth_time`/`acr` rule, notification, recovery invalidation, bypass tests. | `threat-modeling`, `frontend-testing` | UX-only MFA prompts with no server enforcement. |
| Federation or client integration | OAuth/OIDC/SAML, social login, SSO logout, public client, redirect URI, PKCE, account linking. | Preserve IdP trust boundaries and prevent code/token replay, open redirect, stale email linking, and SAML assertion abuse. | Client type, exact redirect list, state/nonce, PKCE, linking rules, cert/key pinning, provider test. | `web-security`, `threat-modeling` | Broad IdP migration without threat model. |
| Credential compromise or security repair | Stolen session, leaked token, refresh-token reuse, brute force, enumeration, account takeover report. | Verify cause, revoke affected material, scan same patterns, add regression evidence, notify/audit. | Incident scope, same-pattern search, rotation/revocation proof, alert/user notice, regression command and exit code. | `security-privacy-gate`, `agent-execution-discipline` | Local patch without family invalidation or scan. |

# Industry Benchmarks

Anchor against NIST SP 800-63B AAL1/2/3, OWASP Authentication and Session Management guidance, OWASP ASVS V2/V3/V6, FIDO2/WebAuthn, OAuth 2.0 Security BCP, OIDC Core and Session Management, JWT BCP, RFC 7009 token revocation, RFC 8693 token exchange, and regulated authentication expectations such as PCI-DSS v4 section 8, HIPAA technical safeguards, and GDPR Article 32. Keep this body focused on routing, lifecycle decisions, evidence, and closure; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for MFA method ranking, session/token strategy matrices, refresh-token rotation logic, cookie attributes, federation traps, and detailed anti-patterns. Load [references/evidence-patterns.md](references/evidence-patterns.md) when closure depends on repository graph, project memory, execution trajectory, validation freshness, or tool permission boundaries.

# Selection Rules

Select this capability when **identity proof or session material** is primary. Adjacent routing:

- Prefer `authentication-authorization` for action permission enforcement after identity is proven.
- Prefer `web-security` for browser-specific controls (CORS, CSRF, CSP, clickjacking, headers).
- Prefer `secret-configuration-security` for application secrets not bound to user identity.
- Prefer `threat-modeling` for broader account-takeover threat surface analysis.
- Use **with** `input-validation` for credential input handling and `logging-error-handling` for audit-safe diagnostics.

# Risk Escalation Rules

Escalate when authentication affects: admin access, payment actions, regulated data (PII/PHI/PCI), social-login account linking (account takeover via stale email reclaim), account recovery (often the weakest link), long-lived tokens (> 24h), device trust persistence, service accounts with elevated scopes, cross-domain or cross-subdomain cookies, federated identity (SAML/OIDC IdP trust changes), or any deviation from MFA on sensitive flows. Escalate any new authentication flow that does not have a security review and threat model.

# Proactive Professional Triggers

- **Signal:** Refresh tokens are long-lived, reusable, or stored without family identifiers. **Hidden risk:** one stolen token becomes persistent account access even after normal logout. **Required professional action:** require single-use rotation, consumed-token reuse detection, family invalidation, audit, and user notification. **Route to:** `authentication-security`, `security-privacy-gate`, `quality-test-gate`. **Evidence required:** refresh-token lifecycle table, reuse-detection negative test, revocation proof, and residual revocation-window owner.
- **Signal:** Session id or equivalent bearer credential is preserved through login, MFA, role elevation, password reset, or email change. **Hidden risk:** session fixation or stale authentication lets an attacker inherit a privileged session. **Required professional action:** map every privilege transition and require regeneration or invalidation at each point. **Route to:** `web-security`, `logging-error-handling`. **Evidence required:** transition map, session regeneration test, audit event, and what the test does not prove about all clients.
- **Signal:** MFA is offered only as optional UX, SMS/email is the strongest factor, or recovery bypasses enrolled MFA. **Hidden risk:** sensitive actions remain protected by the weakest recovery path. **Required professional action:** define AAL target, factor hierarchy, step-up freshness, fallback rules, and recovery invalidation. **Route to:** `threat-modeling`, `frontend-testing`. **Evidence required:** MFA policy matrix, bypass/regression tests, user-notification artifact, and accepted fallback risk.
- **Signal:** OAuth/OIDC/SAML integration uses wildcard redirect URIs, missing state/nonce, public client secret, automatic email-based account linking, or unreviewed IdP-initiated SSO. **Hidden risk:** code/token theft, auth-flow CSRF, id-token replay, or account takeover via stale provider email. **Required professional action:** enforce exact redirect matching, PKCE for public clients, state/nonce validation, explicit linking, and hardened library/cert validation. **Route to:** `web-security`, `threat-modeling`, `integration-change-builder`. **Evidence required:** provider config, redirect allowlist, negative callback tests, and certificate/key rotation notes.
- **Signal:** Project memory, repository graph, or previous incident notes claim login, refresh tokens, recovery, MFA, OAuth callbacks, or service credentials are already handled. **Hidden risk:** stale memory hides new clients, rotated keys, unverified callback paths, leaked token logs, or replayable recovery flows. **Required professional action:** inspect current issuers, verifiers, session stores, IdP callbacks, config, tests, audit events, and execution trajectory; compare each prior claim before reuse. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** source path map, validation command or report, freshness limit, accepted/rejected prior evidence, and remaining unknown auth surfaces.

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

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 authentication routing, lifecycle decision, and evidence rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete authentication security plan, when lifecycle coverage is uncertain, or before implementation starts. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when MFA strength, session-vs-token strategy, refresh-token rotation, cookie attributes, OAuth/OIDC/SAML, or anti-pattern detail is needed. Load [references/evidence-patterns.md](references/evidence-patterns.md) when closure depends on repository graph, project memory, execution trajectory, validation freshness, changed-auth-surface mapping, or tool permission boundaries. Use [examples/example-output.md](examples/example-output.md) only when the expected review shape is unclear. Do not load references for pure routing or trivial wording work where the output contract and quality gate are sufficient.

# Failure Modes

- **Refresh replay:** refresh tokens never rotate and remain usable after theft.
- **Partial logout:** logout clears the browser cookie but does not revoke server-side session/refresh.
- **Session fixation:** session id is not regenerated after login or privilege elevation.
- **Cookie exposure:** cookies lack `Secure`, `HttpOnly`, or appropriate `SameSite`, enabling XSS exfiltration or CSRF.
- **Recovery persistence:** password reset grants access without invalidating old sessions; attacker holding stolen session remains in.
- **Token leakage:** tokens appear in logs, URLs, query strings, analytics, crash reports, or `Referer` headers.
- **Weak password storage:** password storage uses SHA-256, MD5, unsalted, or low-cost bcrypt, making breach cracking fast.
- **Enumeration:** "user not found" vs "wrong password" differ in response or timing.
- **Credential stuffing gap:** brute force protection is per-IP only or per-account only, so distributed attacks still succeed.
- **MFA bypass:** MFA is offered but not enforced for sensitive actions or is bypassable through recovery.
- **Weak factor default:** SMS OTP is used as primary MFA; sim-swap takes over high-value accounts.
- **Unsafe social linking:** social login automatically links accounts by email without verification, enabling takeover via email reclaim.
- **Magic-link replay:** magic link is sent to the wrong email, reused, or leaked via mail forwarder.
- **JWT confusion:** verifier accepts `alg: none` or HS256-with-RSA-public-key.
- **Audience drift:** `aud` claim is not validated, so a token issued for service A is accepted by service B.
- **Unbounded token life:** refresh token absolute lifetime is never enforced.
- **Machine credential staleness:** service account credentials never rotate, are embedded in code, or leak in a public repo.
- **Redirect token theft:** OAuth `redirect_uri` allows path-prefix or wildcard matching.
- **SAML assertion forgery:** IdP-initiated SAML lacks signature validation hardening.
- **Logout CSRF:** logout endpoint is reachable via `GET` and CSRF-able.
- **Undefined concurrency:** concurrent session policy is undefined, so leaked credentials remain usable indefinitely.

# Output Contract

Return an authentication security review with:

- `mode_selected` (new/changed login flow, token lifecycle, MFA/recovery, federation/client integration, or compromise repair)
- `boundaries_inspected` (login, logout, refresh, revocation, recovery, MFA, cookies, IdP callbacks, service credentials, logs, configs, and tests inspected or skipped with reason)
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
- `changed_auth_surface_to_validation_map` (each flow, token, cookie, key, recovery path, or notification change mapped to validator command, test output, report artifact, or named residual risk)
- `validation_evidence` (commands, exit codes, relevant output, artifacts, what evidence proves, and what evidence does not prove)
- `handoff_boundaries` (authorization, web security, secret configuration, logging, frontend testing, delivery, or incident response work that belongs elsewhere)
- `evidence_limits` (clients, IdPs, environments, browsers, telemetry, or production data not verified)
- `residual_risks` and `owner`

# Evidence Contract

Close an authentication-security review only when these answers are concrete:

- **Basis:** selected mode, risk class, AAL or policy target, and benchmark/control basis used for the judgment.
- **Boundaries inspected:** current login/session/token/recovery/MFA/federation/source/config/test paths inspected, plus repository graph, project memory, and execution trajectory evidence accepted or rejected for freshness.
- **Reuse and placement rationale:** why lifecycle controls live at the selected boundary (issuer, verifier, session store, IdP callback, service credential, frontend prompt, audit pipeline) rather than authorization policy, web exploit review, or non-user secret storage.
- **Behavior preservation:** old session, logout, recovery, MFA, IdP, notification, and audit behavior preserved or intentionally changed, including compatibility and rollout risks.
- **Validation evidence:** validator command, test/report artifact, exit code, and changed-auth-surface-to-validation map; state what evidence proves and what it does not prove.
- **Residual risk and next gate:** accepted revocation window, fallback factor, federated logout gap, untested client/IdP, stale telemetry, or manual control with owner, expiry, and next professional gate.

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
