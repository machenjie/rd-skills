# Authentication Security Evidence Patterns

Use this reference when authentication-security closure depends on repository graph, project memory, execution trajectory, validation freshness, changed-auth-surface mapping, or tool permission boundaries. Keep it as an evidence map, not a second authentication tutorial.

## Auth Surface To Validation Map

| Auth surface claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Login/session lifecycle is controlled | Current issuer, session store, cookie writer, regeneration point, logout handler, fixation test, and command/report path | The inspected flow regenerates and revokes session material as designed | Every client, browser, subdomain, or future middleware path is covered |
| Access token validation is safe | Verifier source path, expected algorithm, issuer/audience/expiry/not-before checks, key id handling, and JWT-confusion negative test | The inspected verifier rejects obvious replay, audience drift, and algorithm confusion | All downstream services or external verifiers share the same policy |
| Refresh token rotation works | Token-family schema or store path, atomic consume/issue step, reuse-detection test, revocation artifact, and user/security notification owner | The inspected refresh flow limits stolen-token replay and invalidates the family on reuse | Production race windows, clock skew, or every device binding variant is proven |
| MFA and recovery cannot bypass policy | Action-to-`acr`/`auth_time` matrix, enrolled-factor state, fallback rule, recovery invalidation, bypass tests, and notification artifact | Sensitive actions and recovery paths have server-enforced factor requirements | Phishing resistance, social-engineering resistance, or every helpdesk path is complete |
| Federation or account linking is current | Provider config, exact redirect allowlist, state/nonce/PKCE checks, linking rule, cert/key evidence, and callback negative tests | The inspected provider path preserves IdP trust boundaries | Provider console drift, IdP-initiated SSO variants, or all tenants are covered |
| Token leakage is contained | Source/log/config/analytics/crash-report scan, redaction rule, rotation or revocation proof, and residual exposure owner | Known inspected sinks do not retain reusable authentication material | Uninspected third-party processors, browser extensions, or historical logs are clean |
| Prior graph or memory claim is still valid | Prior claim source, current source path map, final validation command/report, accepted/rejected verdict, and freshness limit | Reused authentication knowledge still matches current issuers, verifiers, callbacks, and tests | Future clients, generated config, or production telemetry changes stay valid |

## Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, previous incidents, old threat models, audit samples, and execution trajectory as discovery inputs until current source, config, tests, and validation output confirm them.
- Accept prior "logout revokes", "MFA covers recovery", "OAuth callback is hardened", "JWT verifier is shared", or "tokens are redacted" claims only when current issuer/verifier/callback/store/log paths and tests still match.
- Reject or downgrade memory that lacks date, owner, auth surface, source path, changed client/provider scope, validation command, exit code, artifact/report path, or residual-risk owner.
- Mark evidence stale after edits to issuers, verifiers, sessions, cookies, token stores, password/MFA/recovery flows, IdP provider config, logging sinks, analytics/crash-report wiring, generated config, reports, builds, or validators.
- Map every final authentication confidence claim to a current source path, config path, command, test, scanner/report, audit artifact, owner approval, or explicit not-verified residual risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, registry search, graph search, report inspection, and markdown validation | Read-only local shell action; cite searched paths and avoid full command-output dumps. |
| Local validators, tests, builds, generated reports, and fixture refresh | State-mutating only for reports, caches, temp files, dist/build artifacts, or local fixtures; cite log path, command, exit code, and rollback path. |
| Secret scan, dependency scan, IdP config export, security scanner, or generated auth artifact | Security-sensitive development action; record input scope, redaction rule, artifact owner, diff review, and cleanup. |
| Live IdP, production telemetry, cloud console, database/session store, deploy, migration, revocation, or key rotation command | High-risk external or production action; require explicit permission, bounded scope, redaction, stop condition, rollback/forward-fix path, and owner. |

## Handoff Evidence Shape

```yaml
authentication_security_evidence_closure:
  inspected_auth_surfaces:
    - surface: ""
      current_source_or_config: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
      freshness: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_auth_surface_to_validation_map:
    - surface: ""
      source_or_config_path: ""
      validation_command_or_artifact: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      owner: ""
      freshness: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  residual_risks:
    - risk: ""
      owner: ""
      next_gate: ""
```
