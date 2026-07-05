# Threat Modeling Benchmarks And Patterns

Use this reference when `threat-modeling` needs benchmark-backed threat enumeration, control mapping, residual-risk review, or anti-pattern detail beyond the compact `SKILL.md` body. Keep the main body focused on routing, output, evidence, and quality gates.

## Benchmark Anchors

- STRIDE for systematic enumeration across spoofing, tampering, repudiation, information disclosure, denial of service, and elevation of privilege.
- PASTA for business-impact sequencing: business objective, technical scope, application decomposition, threat analysis, weakness analysis, attack modeling, and risk treatment.
- OWASP Threat Modeling Cheat Sheet for asset identification, trust zones, data-flow diagrams, abuse cases, and mitigation tracking.
- OWASP ASVS and API Security Top 10 for concrete controls on authentication, session, access control, input validation, logging, API object authorization, and security configuration.
- NIST SP 800-30 for likelihood, impact, risk level, and residual-risk acceptance language.
- CWE/CVSS for vulnerability classification and severity calibration when a threat maps to an implementation weakness.
- GDPR DPIA criteria when processing is high-risk, large-scale, systematic, or involves sensitive personal data.

## Threat-To-Control Matrix

| Threat shape | Required control evidence | Add when | Do not accept |
| --- | --- | --- | --- |
| Spoofed identity, token, service account, or callback source | Authenticator/session/token validation, issuer/audience/source proof, replay protection, and negative test. | `authentication-security` for lifecycle depth. | "Authenticated route" as the only control. |
| Object, tenant, role, admin, or support privilege abuse | Function-level and object-level authorization, server-derived tenant/owner scope, denial semantics, and audit signal. | `permission-boundary-modeling` for matrix depth. | Client-supplied tenant/owner/role as policy input. |
| User-controlled input reaches query, shell, template, URL fetch, file path, parser, prompt, queue, or serializer | Validation/encoding/allowlist at the sink, malicious-input test, safe diagnostics, and same-pattern scan. | `input-validation` or `web-security` for exploit-class depth. | Generic "sanitize input" mitigation. |
| Secret, key, token, certificate, or credential can leak or be replayed | Secret store, scope, rotation, redaction, access audit, and compromise response. | `secret-configuration-security` for lifecycle depth. | Secret in source/config/logs or no rotation owner. |
| Third-party API, webhook, queue, worker, or file exchange crosses trust boundary | Source verification, idempotency/replay defense, timeout/failure contract, DLQ/reconciliation, and monitoring. | `integration-change-builder` or reliability gate for operations depth. | Mock-only success path as integration proof. |
| Regulated, multi-tenant, payment, health, credential, admin, or irreversible workflow remains partially mitigated | Security-owner acceptance, compensating control, review date, expiry, release condition, and rollback/containment. | Delivery/release gate for ship decision. | "Accepted for now" without owner and expiry. |

## Residual-Risk Review Pattern

| Required field | Standard |
| --- | --- |
| Threat and asset | Names the actor, entry point, protected asset, and trust boundary. |
| Severity | States likelihood, impact, and Critical/High/Medium/Low rationale. |
| Mitigation status | Designed, implemented, tested, monitored, deferred, or accepted. |
| Compensating control | Existing control that actually reduces the named risk. |
| Owner and expiry | Role/team owner plus review date or explicit release gate. |
| Reopen trigger | New route, new caller, incident, scanner finding, data class change, or architecture change. |

## Anti-Patterns To Reject

| Anti-pattern | Failure | Correction |
| --- | --- | --- |
| Threat model copied from an earlier design without graph check. | New routes, workers, tenants, or generated artifacts can bypass old assumptions. | Compare current repository graph and validation freshness before accepting memory. |
| Mitigation says "add auth", "validate input", or "encrypt data" with no location. | Control cannot be implemented or tested reliably. | Name boundary, control owner, code/config location, test, and monitoring signal. |
| Only external attackers are modeled. | Support/admin/service-account abuse and tenant escalation are missed. | Include legitimate-user abuse, insider, service account, webhook, and worker actors. |
| Scanner pass closes the model. | Scanners rarely prove object authorization, business abuse, rollback, or monitoring. | Map each Critical/High threat to targeted test/review and detection evidence. |
| Critical residual risk ships as a TODO. | Risk becomes permanent and unaccountable. | Block or require owner sign-off, compensating control, expiry, and release condition. |

## Efficiency Guardrail

Do not load this reference for a low-risk edit with no protected asset, actor, entry point, data flow, or trust boundary change. Load it when selecting threat frameworks, mapping threats to controls, reviewing residual risk, or rejecting paper mitigations.
