# Authentication Security Evidence Patterns

Use this reference when authentication closure depends on current source, prior claims, validation freshness, changed-surface mapping, or tool boundaries. Include only triggered auth claims; mark accepted unexecuted checks `planned`/`not_run` with reason. Keep it as an evidence map.

## Auth Surface To Validation Map

| Auth surface claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Login/session lifecycle is controlled | Current issuer, session store, cookie writer, regeneration point, logout handler, fixation test, and command/report path | The inspected flow regenerates and revokes session material as designed | Every client, browser, subdomain, or future middleware path is covered |
| Access token validation matches its format | Token format and verifier path. For a JWT path: an explicit configured allowed-algorithm set (allowlist) bound to expected key types and verifier keys, issuer/audience/time checks, trusted `kid` resolution, and negative cases rejecting untrusted token-header attempts to select an unconfigured algorithm, switch key types, or select a verifier key. For opaque/reference only: provider/introspection contract, active/client/resource/scope/time checks, and failure/cache behavior | The inspected verifier enforces the selected token format and trust boundary | All consumers/providers share policy or introspection remains available |
| Refresh token rotation works | Token-family schema or store path, atomic consume/issue step, reuse-detection test, revocation artifact, and user/security notification owner | The inspected refresh flow limits stolen-token replay and invalidates the family on reuse | Production race windows, clock skew, or every device binding variant is proven |
| MFA and recovery assurance is enforced | Required assurance/freshness, verified factor or recovery state, fallback/invalidation, callback binding and replay defense when used, denied/bypass tests, and notification owner; for OIDC only when applicable, validate `acr`/`auth_time` | Sensitive actions and recovery paths enforce the inspected protocol's assurance and callback contract | Phishing or social-engineering resistance, every helpdesk path, or untested protocol variants are complete |
| Federation or account linking is bound safely | Provider/protocol config, redirect/callback allowlist, anti-forgery, request-to-callback and identity/account binding, replay defense, linking rule, key/cert evidence, and negative tests; use state/nonce/PKCE only for OAuth/OIDC when applicable | The inspected protocol path preserves provider and account-binding trust boundaries | Provider-console drift, untested initiation modes, or all tenants are covered |
| Token leakage is contained | Source/log/config/analytics/crash-report scan, redaction rule, rotation or revocation proof, and residual exposure owner | Known inspected sinks do not retain reusable authentication material | Uninspected third-party processors, browser extensions, or historical logs are clean |
| Prior source or task evidence claim is still valid | Prior claim source, current source path map, role-permitted evidence, accepted/rejected verdict, and freshness limit | Reused authentication knowledge still matches current issuers, verifiers, callbacks, and tests | Future clients, generated config, or production telemetry changes stay valid |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, previous incidents, old threat models, audit samples, and observable action sequence as discovery inputs until current source, config, tests, and validation output confirm them.
- Accept prior "logout revokes", "MFA covers recovery", "federation callback is hardened", "access-token verifier is shared", or "tokens are redacted" claims only when current authority/verifier/callback/store/log paths and evidence still match.
- Reject or downgrade memory that lacks date, owner, auth surface, source path, changed client/provider scope, role-permitted evidence or `planned`/`not_run` reason, and residual-risk owner.
- Mark evidence stale after edits to issuers, verifiers, sessions, cookies, token stores, password/MFA/recovery flows, IdP provider config, logging sinks, analytics/crash-report wiring, generated config, reports, builds, or validators.
- Map each triggered claim to current source/config or existing artifacts and, when a permitted check ran, its result. Otherwise record `planned`/`not_run`, reason, owner, and residual risk.

## Tool Permission Boundary

- Live IdP, session-store, revocation, or key-rotation actions require an authorized target, owner, stop condition, rollback or forward fix, and redacted evidence.
- Authentication fixtures and generated auth artifacts must name their cleanup path and exclude credentials, tokens, and session material from retained output.

## Handoff Evidence Shape

```yaml
authentication_security_evidence:
  profile: analysis-agent | task-agent | review-agent
  inspected_surfaces:
    - surface: ""
      evidence_and_freshness: ""
  prior_claims:
    - claim: ""
      verdict_and_evidence: ""
  surface_to_validation:
    - surface: ""
      status: planned | ran | not_run
      evidence_or_reason: ""
      proves_and_limits: ""
  mutation:
    action_or_none: ""
    authority_cleanup_redaction: ""
  residual_risk:
    - risk: ""
      owner_or_gate: ""
```
