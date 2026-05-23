---
name: secret-configuration-security
description: Prevents secrets and risky configuration from being committed, logged, exposed to frontend, embedded in images, copied into docs, or changed without production-risk review.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "56"
changeforge_version: 0.1.0
---

# Mission

**Prevent secrets and production-sensitive configuration from being exposed at any point in the software supply chain** — including source control, build artifacts, container images, CI/CD logs, frontend bundles, documentation, and support tooling — and ensure that rotation, revocation, access scope, redaction, and deployment-risk review are explicitly planned before any change that touches secrets, credentials, or production-sensitive configuration ships.

# When To Use

Use this capability when: a change introduces new environment variables, API keys, database credentials, service account keys, signing keys, encryption keys, KMS keys, certificates, HMAC secrets, OAuth client secrets, or any value that grants privileged access to a system; an existing secret or key needs rotation, scope reduction, or revocation; configuration values control security behavior (feature flags for authentication bypass, rate limiting, TLS enforcement, content security policy, CORS origin allowlist, WAF, DNS/CDN/gateway exposure); CI/CD pipeline variables or secrets are being modified; a container image or build artifact needs to be verified for embedded secrets; or documentation, code examples, or README files include operational configuration values that could be real.

# Do Not Use When

Do not use this capability to design the authentication and authorization model (use `authentication-authorization` and `authentication-security`); audit web-facing exposure paths for frontend vulnerabilities (use `web-security`); analyze package supply chain risk (use `dependency-vulnerability-scanning`); or coordinate the deployment rollout after secrets rotation is designed (use `delivery-release-gate`).

# Non-Negotiable Rules

- **Secrets must never appear in source control, even in a "temporary" or "test" commit.** A secret committed to a Git repository — even in a branch, even if immediately deleted, even in a private repository — is compromised. It exists in Git history, in CI/CD build logs, in developer laptops that have cloned the repository, and potentially in GitHub's own internal backups. Rotation is the only remediation. `git revert` does not remove the secret from history. Use `git filter-repo` (not `git filter-branch`) for history rewriting, but assume the secret is compromised.
- **Build images must not contain runtime secrets at build time.** Secrets injected during `docker build` (via `ARG`, `ENV`, or `COPY`) persist in the image layer history even if later overwritten with `RUN unset`. Use multi-stage builds; pass secrets at runtime via environment variables, secret mounts (`--secret` in BuildKit), or a secrets manager sidecar. Verify with `docker history --no-trunc` that no secret layer is present.
- **Secrets must not be logged, traced, or emitted as metrics.** Authorization headers (`Authorization: Bearer <token>`), signed URLs, database connection strings, and API keys must be explicitly redacted from: application logs, structured log records (JSON fields like `"password": "[REDACTED]"`), distributed traces (OpenTelemetry span attributes), error reports (Sentry, Datadog errors), and support tooling (admin panels, debug UIs). Redaction must be a positive allowlist of safe fields, not a blocklist of known-bad fields (a new secret field name bypasses a blocklist automatically).
- **Configuration changes can be production-risk changes and must be reviewed as such.** A configuration value that disables TLS verification, expands a CORS origin allowlist, reduces a rate limit from 100 to 10,000, or changes a feature flag from `false` to `true` is a security-posture change. It must be reviewed by a security-aware engineer before deployment — not treated as a safe "non-code" change.
- **Secret access must follow least privilege: named service, named environment, named purpose.** "Engineering team has access to the production database password" is not an access policy. An access policy is: "Service `order-processor` in environment `production` has read access to secret `db/production/order-processor/password`; access expires in 90 days; emergency break-glass access requires two-person approval." Access must be revocable per service, per environment, without revoking all consumers.
- **Secret rotation must include all consumers before revocation of the old secret.** Rotating a secret and immediately revoking the old version while some consumers still hold the old version in memory or in their local config cache causes a production incident. Rotation procedure: (1) Create new secret version in secrets manager. (2) Update all consumers to read the new version (rolling deploy or dynamic config reload). (3) Verify all consumers are using the new version (audit log check). (4) Revoke old version.
- **Documentation and code examples must use placeholders, not real values.** `API_KEY=your-api-key-here`, `DATABASE_PASSWORD=<replace-with-real-value>`, `SIGNING_SECRET=EXAMPLE_DO_NOT_USE_IN_PRODUCTION` are safe placeholders. Any value that looks like a real API key, UUID, or base64 string in documentation or a `.env.example` file must be verified to be a non-functional placeholder (by attempting to use it against the real service and confirming it fails).
- **KMS and secret-manager policy changes require least-privilege review.** Key policy, cross-account grants, decrypt permissions, rotation schedule, deletion windows, and service identity bindings must be reviewed as security controls, not only configuration.

# Industry Benchmarks

Anchor against: **OWASP Top 10 — A02:2021 Cryptographic Failures** (previously "Sensitive Data Exposure") — secrets in transit and at rest; key management; encryption key rotation. **OWASP ASVS Section 6 (Stored Cryptography) and Section 2 (Authentication)** — credential storage requirements; API key entropy and lifecycle. **NIST SP 800-57 (Key Management)** — key lifecycle phases: generation, distribution, storage, use, rotation, revocation, destruction. **CIS Benchmark for Docker** — Layer inspection for secrets; runtime secret injection; least-privilege container runtime. **HashiCorp Vault / AWS Secrets Manager / GCP Secret Manager / Azure Key Vault** — secret versioning; dynamic secrets (database credentials generated per-connection); lease expiry; audit logging. **SLSA (Supply-chain Levels for Software Artifacts)** — build provenance; hermetic builds; no secret injection into build-time layers. **GitLeaks / TruffleHog / detect-secrets** — pre-commit hooks and CI checks for secret pattern detection. **GDPR Article 32** — appropriate technical measures to protect personal data, including credentials that grant access to systems processing personal data. **SOC 2 Type II** — audit trail requirements for secret access and rotation; access review frequency.

### Secret Storage Selection Matrix

| Secret Type | Approved Storage | Not Acceptable | Rotation Frequency |
| --- | --- | --- | --- |
| Database credentials | Secrets manager (dynamic preferred) | `.env` files in source, Docker ENV | 90 days or on breach |
| API keys (third-party) | Secrets manager | Hardcoded in source, CI env vars visible in logs | 90 days or on personnel change |
| Signing / HMAC secrets | Secrets manager with versioning | Constants in source, config files | 180 days or on breach |
| TLS certificates / private keys | Secrets manager or certificate manager | Container image, build artifact | At expiry or on breach |
| OAuth client secrets | Secrets manager | Frontend code, public config | 180 days or on breach |
| CI/CD pipeline secrets | CI secret store (masked, not exposed) | Pipeline YAML as plaintext, log output | 90 days |
| Service-to-service tokens | Short-lived JWT or dynamic credentials | Long-lived static tokens | Per-request or < 1 hour |
| Encryption keys (data at rest) | KMS (cloud-managed or HSM) | Application code, config files | Per KMS policy (annual minimum) |

### Secret Exposure Risk Decision Tree

```
Is the value a credential, key, token, or certificate?
  YES → Continue
  NO  → Not a secret (but check if it's a sensitive config value below)

Does the value appear in any of these locations?
  - Source file, config file, .env file committed to Git → CRITICAL: rotate immediately; audit access
  - Docker image layer (check `docker history --no-trunc`) → CRITICAL: rebuild without secret; rotate
  - CI/CD log output → HIGH: mask in CI config; rotate if leaked to external system
  - Application log / trace / error report → HIGH: implement redaction; rotate
  - Frontend bundle (JS, HTML, inline config) → CRITICAL: frontend secrets are public; rotate
  - Documentation or README → MEDIUM: replace with placeholder; verify placeholder is non-functional; rotate if real

Does the config value control a security behavior?
  (TLS enforcement, CORS allowlist, rate limit, auth bypass flag, MFA requirement)
  YES → Treat as production-risk change; requires security-aware review before deploy
  NO  → Standard configuration change review applies
```

# Selection Rules

Select this capability when **secrets, credentials, KMS policy, key rotation, or security-sensitive configuration are the primary concern in a change**. Route elsewhere when: the authentication model itself needs design (use `authentication-authorization`); web-facing vulnerabilities like XSS, CSRF, or injection are the concern (use `web-security`); the deployment coordination for the secret rotation needs planning (use `delivery-release-gate`); package dependency vulnerabilities are the concern (use `dependency-vulnerability-scanning`).

# Risk Escalation Rules

Escalate immediately to the security owner when: a real secret has been or may have been committed to source control (assume compromised; rotate before any other action); a container image may have a secret embedded in a layer (pull request blocked until image rebuild is verified); a frontend bundle may contain a server-side secret injected via build-time environment variables (assume public; rotate immediately); a secret has been emitted to an external log aggregator, error tracker, or monitoring service that has broader access than the secret's intended audience; KMS key policy grants broad decrypt, cross-account access, or key deletion without recovery plan; rotation of a shared secret would require a coordinated multi-service deploy and no coordination plan exists; or a CI/CD pipeline secret has been exposed in a build log that is accessible to contributors without production access.

# Critical Details

- **`NEXT_PUBLIC_`, `REACT_APP_`, `VITE_` prefixed variables are public.** Frontend build tools expose any environment variable with the designated public prefix directly into the compiled JavaScript bundle. Any engineer who adds `NEXT_PUBLIC_DATABASE_PASSWORD=...` or `VITE_API_SECRET=...` has published that secret to every user who loads the application. Server-side secrets must never use the public variable prefix, even in development.
- **Docker `ARG` does not prevent secrets from appearing in image history.** `docker build --build-arg API_KEY=secret` stores the value in the image layer metadata (`docker history --no-trunc`). Use BuildKit `--secret` mount (`RUN --mount=type=secret,id=api_key cat /run/secrets/api_key`) so the secret is never baked into any layer.
- **Structured logging can silently include secrets via object serialization.** A log statement like `logger.info("Request received", { body: req.body })` will log the entire request body — including any password, token, or secret field the client submits. Use a per-field allowlist for structured log objects, not a blocklist.
- **Configuration default values control security posture.** A default of `ENFORCE_TLS=false`, `RATE_LIMIT_ENABLED=false`, or `REQUIRE_MFA=false` means that if the environment variable is not set in production (due to a deploy oversight), the secure behavior is disabled. Security-sensitive flags must default to the **more restrictive** value: `ENFORCE_TLS=true`, `RATE_LIMIT_ENABLED=true`, `REQUIRE_MFA=true`. The default must be fail-closed, not fail-open.
- **Key deletion is harder to roll back than key rotation.** Disabling or scheduling deletion of a KMS key can make encrypted data permanently unreadable. Key lifecycle changes require backup, restore, decrypt-impact inventory, and explicit recovery window.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| `DATABASE_URL=postgres://admin:realpassword@prod.db.example.com/app` in `.env.example` committed to Git | Real production credential in public/private repo; assume compromised | Replace with `DATABASE_URL=postgres://user:password@localhost:5432/dbname`; rotate real credential |
| `ENV STRIPE_SECRET_KEY=sk_live_...` in Dockerfile | Secret baked into every image layer; visible in `docker history`; accessible to anyone who pulls the image | Pass at runtime via secrets manager; use BuildKit `--mount=type=secret` for build-time access |
| `NEXT_PUBLIC_STRIPE_SECRET_KEY=sk_live_...` in Next.js | `NEXT_PUBLIC_` prefix embeds value in client bundle; every user of the site can read it | Server-side only; use `STRIPE_SECRET_KEY` (no public prefix); access via API route only |
| `logger.info({ request })` logs full request including Authorization header | Bearer token or API key emitted to log aggregator; potentially accessible to log-viewing users | Allowlist log fields; redact `Authorization`, `password`, `token`, `secret` fields explicitly |
| Security flag `RATE_LIMIT_ENABLED` defaults to `false` | Missing env var in production silently disables rate limiting; DDoS or brute-force protection absent | Default to `true`; require explicit opt-out; alert when rate limiting is disabled |
| Secret rotation revokes old version immediately after creating new | Consumers still holding old version in memory; production 401s; rollback required | Deploy new version; verify all consumers updated via audit log; then revoke old |

# Failure Modes

- Real API key committed to Git in a "test configuration" commit; key used in production; credential extracted by automated scanner within minutes of push.
- Docker build `ARG SECRET=...` approach; secret visible in `docker history`; image pushed to public registry; secret extracted.
- `NEXT_PUBLIC_INTERNAL_API_TOKEN` in React build; token embedded in bundle; token found by security researcher in browser DevTools.
- Log aggregator indexes full request bodies; database password in request body from a legacy migration endpoint; credential visible to 12 engineers without production access.
- `ENFORCE_2FA=false` default; production deployment skips setting the variable; 2FA bypassed for all users for 48 hours before discovery.
- Secret rotation revokes old key at midnight; 6 background workers restart at 00:01 with cached old config; 6 production workers fail for 10 minutes until all restart with new key.

# Output Contract

Return a secret and configuration review with:

- `secret_inventory` (per secret: name, type, current storage location, approved storage, access scope, rotation frequency, revocation plan)
- `exposure_risk_assessment` (per secret: risk classification, exposure vector, remediation if exposed)
- `redaction_controls` (log fields redacted, trace attribute filters, error report scrubbing rules)
- `config_security_flags` (per security-sensitive config: current default, correct fail-closed default, risk if missing)
- `rotation_plan` (per secret: create new → update consumers → verify → revoke old; deployment coordination notes)
- `kms_key_policy` (key owner, allowed principals, decrypt/encrypt grants, cross-account access, rotation schedule, deletion window, recovery plan)
- `secret_manager_scope` (secret path/project/account boundary, service identity binding, access review evidence, audit log source)
- `frontend_exposure_boundary` (which variables are public-prefixed; which must be server-side only)
- `ci_secret_controls` (CI secret store location, masking verification, log visibility)
- `break_glass_procedure` (emergency access escalation for production secrets)
- `residual_risks` (known risks that cannot be fully mitigated with current tooling; compensating controls)

# Quality Gate

The review is complete only when:

1. No real secret appears in source control, build artifacts, or documentation.
2. All secrets are in approved secret manager storage with named access scope.
3. Frontend public-prefix boundary is verified (no server secret uses public prefix).
4. All security-sensitive configuration flags default to fail-closed values.
5. Log, trace, and error redaction covers all known secret fields via allowlist.
6. Rotation plan covers: create → consumer update → verify → revoke sequence.
7. Docker images verified secret-free via `docker history --no-trunc`.
8. CI/CD secrets are masked and not visible in build logs.
9. Break-glass access procedure is documented with two-person approval.
10. Residual risks are documented with compensating controls.
11. KMS key policies and secret-manager access scopes are least-privilege, rotation-aware, audited, and recoverable.

# Used By

- security-privacy-gate
- delivery-release-gate

# Handoff

Hand off to `delivery-release-gate` for rotation deployment coordination; `logging-error-handling` for redaction control implementation; `authentication-security` for credential lifecycle in the authentication system; `threat-modeling` for high-impact exposure scenarios requiring adversarial analysis.

# Completion Criteria

The capability is complete when **no secret is exposed at any supply chain stage, all security-sensitive configuration defaults are fail-closed, rotation covers all consumers before revocation, and every exposure risk has a named remediation or documented compensating control**.
