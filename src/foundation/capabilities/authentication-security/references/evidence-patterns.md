# Authentication Security Evidence Patterns

Use this reference when authentication closure depends on current source, prior claims, validation freshness, changed-surface mapping, or tool boundaries. Include only triggered claims; mark accepted unexecuted checks `planned`/`not_run` with reason.

## Claim Evidence

| Claim | Minimum current evidence | Proof limit |
| --- | --- | --- |
| Login and session lifecycle | Issuer, session store, cookie writer, regeneration point, logout/revocation handler, fixation test, and command/report path | Covers the inspected flow, not uninspected clients, browsers, subdomains, or middleware |
| JWT or opaque token validation | Format and verifier path. JWT: configured algorithm allowlist bound to expected key types/keys, issuer/audience/time checks, trusted `kid`, and negatives for header-selected algorithm/key changes. Opaque/reference: provider introspection with active/client/resource/scope/time, cache, and failure behavior | Does not prove other consumers/providers share policy or introspection availability |
| Refresh rotation and reuse | Token-family store, atomic consume/issue, reuse-detection test, family revocation, and notification owner | Does not prove production races, clock skew, or untested device bindings |
| MFA and recovery | Assurance/freshness, factor or recovery state, fallback/invalidation, callback binding/replay defense, denied/bypass tests, and notification; validate OIDC `acr`/`auth_time` when applicable | Does not prove social/helpdesk resistance or untested protocols |
| Federation and account linking | Provider/protocol config, redirect allowlist, anti-forgery, request/callback and identity/account binding, replay defense, linking rule, key/cert evidence, and negatives; use state/nonce/PKCE only for applicable OAuth/OIDC | Does not prove provider-console state, untested initiation, or all tenants |
| Leakage and redaction | Source/log/config/analytics/crash/referrer/artifact scan, redaction rule, rotation/revocation evidence, and residual owner | Does not prove third-party processors, extensions, or historical logs are clean |

## Freshness And Invalidation

- Treat repository inspection, prior tasks/incidents, old threat models, audit samples, and action sequences as discovery until current source, config, tests, and validation confirm them.
- Revalidate after issuer, verifier, session, cookie, token store, password/MFA/recovery, provider config, logging/analytics/crash, generated config, report, build, or validator changes.
- For each triggered claim record current path/artifact, `planned`/`ran`/`not_run`, result or reason, owner, freshness, proof limits, and residual risk.

## Live Action Boundary

- Live IdP, session-store, revocation, or key actions require authorized target/owner, stop condition, rollback or forward fix, and redacted evidence.
- Authentication fixtures and generated artifacts name cleanup and exclude credentials, tokens, and session material from retained output.

## Handoff Record

Record profile, inspected surface/path/evidence/freshness, prior-claim verdict, validation status/result/reason/proves/limits, mutation authority/recovery/cleanup/redaction, residual risk, and next owner or gate.
