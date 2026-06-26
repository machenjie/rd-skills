---
name: threat-modeling
description: Requires explicit threat models for high-risk changes by identifying assets, actors, boundaries, entry points, abuse cases, mitigations, and residual risk.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "52"
changeforge_version: 0.1.0
---

# Mission

**Identify security and abuse risks before implementation by constructing an explicit threat model that enumerates assets, actors (legitimate and adversarial), trust boundaries, entry points, data flows, abuse cases, mitigations, and residual risk** — so that every high-impact threat has a concrete implemented control, test, and monitoring signal, rather than a design note that gets implemented "later" and never does.

# When To Use

Use this capability when: a change adds a new public API endpoint, authentication mechanism, authorization rule, file upload handler, payment integration, or external service integration; a change accesses, stores, transmits, or processes sensitive data (PII, payment card data, credentials, health records, financial transactions); a change introduces administrative actions, tenant management, privilege escalation paths, or cross-tenant data access; a change modifies infrastructure boundaries (new VPC, new DNS record, new CDN configuration, new IAM policy); or an architecture review has flagged a security concern that must be formally modeled before the change proceeds.

Also use this capability when repository graph evidence, project memory, execution traces, previous design notes, generated artifacts, or validation results show an unclear trust boundary, stale threat assumption, unverified mitigation, or newly reachable abuse path.

# Do Not Use When

Do not use this capability as a substitute for implementing concrete security controls — a threat model that lists mitigations without implemented code, configuration, and tests is a paper document, not a defense. Do not use for purely cosmetic changes or internal refactors that do not touch trust boundaries, data access, or behavioral authorization logic.

# Stage Fit

- **Planning:** require the threat model before choosing an architecture for new sensitive surfaces, cross-boundary data flows, admin actions, integrations, uploads, AI/tool paths, or regulated processing.
- **Read/code-review:** verify the current repository graph, actual entry points, actors, assets, data flows, trust boundaries, prior threat notes, and known mitigations before judging risk.
- **Coding/refactoring:** ensure every selected mitigation has an owner, implementation location, fallback behavior, test, and monitoring signal while preserving existing controls.
- **Testing/release:** require current validation evidence for Critical and High threats, plus release owner acceptance for residual risk, monitoring, and rollback limits.
- **Debugging/bug-fix/incident:** update the model from the verified exploit path, scan for same-pattern abuse cases, and keep mitigations tied to regression tests and detection signals.

# Non-Negotiable Rules

- **Enumerate assets explicitly.** An asset is any value the system must protect: user data (names, emails, addresses, health records), credentials (passwords, API keys, session tokens, OAuth codes), financial data (card numbers, bank accounts, transaction records), business confidential records (pricing, trade secrets, source code), system integrity (code execution, configuration, cryptographic keys). Every asset must have a classification: what category of data, who owns it, what regulation applies (GDPR, PCI-DSS, HIPAA, SOC 2).
- **Model both external attackers and legitimate users abusing allowed workflows.** A threat model that covers only "an external attacker tries to break in" misses the most common real-world incidents: a legitimate user who discovers that changing a URL parameter exposes another user's order; an internal employee who downloads all customer records because there is no rate limit or export audit; a partner API key that is shared across environments and inadvertently has production access. Insider threats and authorization abuse cases must be explicitly modeled.
- **Trust boundaries must be drawn at every layer where assumptions change.** A trust boundary exists wherever data moves from a less-trusted to a more-trusted context, or vice versa. Required boundaries to draw: (1) browser/mobile client → API gateway (public internet — no trust); (2) API gateway → backend service (internal network — partial trust, but validate input); (3) backend service → database (application layer — trust, but principle of least privilege); (4) backend service → third-party API (external — validate responses, handle failures); (5) admin UI → admin API (elevated privilege boundary — require re-authentication). Any call that crosses a trust boundary must be validated, authenticated, and authorized.
- **Every abuse case must map to a concrete mitigation with owner, implementation location, test, and monitoring signal.** A threat listed as "attacker may brute-force the login form" with mitigation "add rate limiting" is incomplete unless it specifies: which rate limiting implementation (e.g., token bucket at the API gateway layer, limit 10 attempts per 15 minutes per IP + per account), how it is configured (fail-open vs. fail-closed), how it is tested (automated test that simulates 11 rapid attempts and asserts 429 response), and what alert fires when the rate limit is triggered in production.
- **Residual risks must be accepted explicitly with owner, rationale, review date, and escalation trigger.** A risk that is accepted silently — by shipping without addressing it — is a liability. Every residual risk must have: the threat it represents, the likelihood and impact rating, the reason it is accepted (mitigating control is proportionate; threat is out-of-scope for the current change; compensating control exists elsewhere), the owner who accepted it (role, not individual), and a review date (residual risk acceptance expires; it must be re-evaluated if the threat landscape changes).
- **High-impact threats must have verification evidence before merge or release.** A "Critical" severity threat with a listed mitigation has zero value if the mitigation has not been implemented and tested. The threat model must track: mitigation status (designed/implemented/tested/monitoring deployed), the specific test that proves the control works (test ID or test case description), and the monitoring signal that will detect exploitation attempts in production.
- **No threat status is valid without current design evidence.** Prior project memory, architecture notes, or earlier threat models can seed the review, but final conclusions must be grounded in current repository graph inspection, data-flow evidence, execution artifacts, test results, monitoring configuration, or explicit owner confirmation.

# Industry Benchmarks

Anchor against: **STRIDE (Microsoft)** — Spoofing identity, Tampering with data, Repudiation, Information disclosure, Denial of service, Elevation of privilege — systematic threat enumeration per component and data flow. **PASTA (Process for Attack Simulation and Threat Analysis)** — risk-centric; business impact → technical risk mapping; attacker motivation analysis. **OWASP Threat Modeling Cheat Sheet** — asset identification, trust zones, data flow diagrams, abuse cases, STRIDE per element. **OWASP Top 10 (2021)** — A01 Broken Access Control, A02 Cryptographic Failures, A03 Injection, A04 Insecure Design, A05 Security Misconfiguration, A06 Vulnerable Components, A07 Identification and Authentication Failures, A08 Software and Data Integrity Failures, A09 Security Logging and Monitoring Failures, A10 SSRF. **OWASP ASVS (Application Security Verification Standard)** — L1/L2/L3 verification requirements for authentication, session, access control, input validation, cryptography. **NIST SP 800-30 (Risk Assessment)** — likelihood × impact threat rating methodology. **CWE/CVSS** — vulnerability scoring and categorization. **Microsoft SDL (Security Development Lifecycle)** — threat model as required artifact in design phase. **GDPR Article 32 and 35 (DPIA)** — Data Protection Impact Assessment for high-risk processing; systematic description of processing; necessity and proportionality assessment; risk management.

### STRIDE Threat Enumeration Matrix

| Threat Category | STRIDE Code | Examples for Web/API Systems | Default Mitigation Direction |
| --- | --- | --- | --- |
| Spoofing | S | Forged JWT/session token; credential theft; API key impersonation | Authentication (JWT signature verification, MFA, short-lived tokens) |
| Tampering | T | SQL injection; mass assignment; CSRF; parameter manipulation | Input validation; parameterized queries; CSRF tokens; HMAC integrity |
| Repudiation | R | No audit log for admin action; log deletion by attacker | Immutable audit log; tamper-evident logging; digital signature for critical actions |
| Information Disclosure | I | IDOR (insecure direct object reference); verbose error messages; API returning excess fields | Authorization checks per resource; minimal error disclosure; field-level filtering |
| Denial of Service | D | Brute force; resource exhaustion; ReDoS; large file upload | Rate limiting; input size limits; regex safety; resource quotas |
| Elevation of Privilege | E | Horizontal privilege escalation (user A sees user B's data); vertical escalation (user becomes admin) | RBAC enforcement; ownership checks; re-authentication for privilege operations |

### Threat Model Record Minimum Fields

Each threat record must include `threat_id`, component, entry point, actor, asset, trust boundary, STRIDE category, abuse path, likelihood, impact, mitigation owner, implementation location, mitigation status, test or review evidence, monitoring signal, residual risk owner, review date, and escalation trigger.

# Selection Rules

Select this capability when **the security risk shape of a change is unclear or known to be high impact**. Route to `web-security` for specific browser exploit classes (XSS, CSRF, CSP, clickjacking); `authentication-security` for identity lifecycle hardening (MFA, token rotation, account takeover); `input-validation` for boundary validation design; `secret-configuration-security` for secret exposure risk; `permission-boundary-modeling` for authorization model design.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities / gates | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| New sensitive surface | New endpoint, webhook, upload, admin action, AI/tool action, external integration, IAM/policy boundary, regulated processing, or data export. | Enumerate assets, actors, data flows, trust boundaries, STRIDE threats, mitigations, tests, monitoring, and residual-risk owner before implementation. | Route/entry-point list, data-flow map, trust-boundary inventory, protected-asset classification, severity rationale, validation plan. | `security-privacy-gate`, `input-validation`, `permission-boundary-modeling` | Cosmetic or internal-only refactor with no protected asset, actor, entry point, or boundary change. |
| Existing model refresh | Project memory, prior threat model, architecture note, generated report, or graph evidence claims a boundary is already safe. | Treat memory as a lead, compare it to current source reachability, accept/reject assumptions, and update stale threats. | Memory date/scope, current graph delta, unchanged-boundary proof, inspected paths, unknowns. | `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis` | Reusing old diagrams as proof without current graph inspection. |
| Mitigation validation | Threat record names a control, owner, or release gate but lacks implementation, test, monitoring, or rollback evidence. | Convert paper mitigations into code/config locations, abuse-case validation, detection signal, release condition, and residual-risk decision. | `threat_to_validation_map`, command/report output, test ID, exit code or manual review artifact, alert source, owner. | `validation-broker`, `quality-test-gate`, `reliability-observability-gate` | Marking Critical/High mitigated because the design says it will be fixed later. |
| Debugging or incident repair | A bug-fix, incident, pen-test finding, scanner result, or support escalation reveals an exploit path or unmodeled actor. | Rebuild the threat path from verified evidence, scan for same-pattern exposure, and bind remediation to regression tests and monitoring. | Incident/scanner artifact, affected graph paths, exploit precondition, same-pattern scan, regression test, detection rule. | `failure-diagnosis`, `web-security`, `security-privacy-gate` | Treating the single failing route as isolated without reachability review. |
| Release or residual-risk acceptance | Critical/High threat, regulated data, cross-tenant exposure, credential/private-key path, payment/trading workflow, or irreversible action remains partially unmitigated. | Block or explicitly accept residual risk with owner, rationale, expiry, compensating control, rollback and next gate. | Security-owner approval, severity record, compensating-control evidence, review date, release gate, rollback note. | `delivery-release-gate`, `security-privacy-gate`, `agent-tool-permission-sandbox` | Shipping unresolved Critical exposure without explicit owner sign-off and expiry. |

# Proactive Professional Triggers

Use this capability proactively, even when the request does not ask for threat modeling:

- **Signal:** a diff or design adds an endpoint, webhook, callback, file upload, admin action, AI/tool action, background worker, external integration, public gateway, IAM/policy change, or data export.
  **Hidden risk:** a missing entry-point model can hide a data leak, wrong-boundary privilege path, or unverified abuse path not covered by existing controls.
  **Required professional action:** enumerate assets, actors, data flows, boundaries, STRIDE threats, mitigations, tests, and monitoring before implementation approval.
  **Route to:** `threat-modeling`, `security-privacy-gate`, and the domain capability for the changed boundary.
  **Evidence required:** graph paths, entry point list, data-flow map, trust boundary list, and validation plan.
- **Signal:** project memory, old architecture notes, a previous threat model, or generated summary claims an area is already safe.
  **Hidden risk:** stale design memory can miss new callers, permissions, data flows, or deployment exposure.
  **Required professional action:** compare memory against current repository graph and execution evidence, then record accepted/rejected assumptions.
  **Route to:** `project-memory-governance`, `repository-graph-analysis`, `execution-trajectory-analysis`, and this capability.
  **Evidence required:** memory source date, current graph delta, unchanged boundary proof, and explicit unknowns.
- **Signal:** a mitigation is named without an implementation location, test, monitoring signal, owner, or release gate.
  **Hidden risk:** an unverified paper mitigation is mistaken for an implemented control, leaving the threat silently open.
  **Required professional action:** map the threat to concrete code/config, verification, alerting, rollback, and residual-risk acceptance.
  **Route to:** `validation-broker`, `quality-test-gate`, `reliability-observability-gate`, and this capability.
  **Evidence required:** `threat_to_validation_map`, passing evidence, monitoring source, and owner.
- **Signal:** a user-controlled value reaches a parser, renderer, query, shell, prompt, path, URL fetch, serializer, queue, file store, or third-party API.
  **Hidden risk:** injection, SSRF, prompt injection, tampering, data leak, or privilege escalation can cross the wrong untrusted boundary.
  **Required professional action:** model the boundary and route to the exact control capability rather than leaving a generic threat note.
  **Route to:** `input-validation`, `web-security`, `permission-boundary-modeling`, `agent-tool-permission-sandbox`, and this capability.
  **Evidence required:** malicious-input tests, allowlist/encoding/control location, and same-pattern scan.
- **Signal:** residual risk is accepted for Critical/High exposure, regulated data, multi-tenant access, payments, credentials, private keys, infrastructure privilege, or irreversible operations.
  **Hidden risk:** the release can silently ship unresolved material risk without accountable approval.
  **Required professional action:** block Critical unmitigated threats unless explicit owner sign-off exists, define compensating controls, review date, and escalation trigger.
  **Route to:** `security-privacy-gate`, `delivery-release-gate`, and this capability.
  **Evidence required:** owner, rationale, severity, compensating control, expiry, and release condition.

# Reference Loading Policy

- **L1:** Use only this `SKILL.md` for routing when the change clearly has no trust boundary, protected asset, actor, entry point, or security behavior change.
- **L2:** Load [references/checklist.md](references/checklist.md) for any actual threat model, security review, design review, incident repair, or release decision involving new or changed assets, actors, data flows, boundaries, mitigations, or residual risk.
- **L3:** Load [examples/example-output.md](examples/example-output.md) when producing a handoff, evaluation fixture, user-facing threat model, or structured mitigation plan.
- **L4:** Pair with `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker` when the threat model depends on current code reachability, prior decision freshness, command output, generated artifacts, or validation evidence.
- **L5:** Pair with `agent-tool-permission-sandbox` before tool runs that can read sensitive code/config, print secrets, mutate security state, call external connectors, or generate evidence from untrusted output.

# Risk Escalation Rules

Escalate immediately when: a threat is rated Critical (high likelihood × high impact) and no mitigation is implemented or planned; a threat can expose regulated personal data (GDPR Article 83 penalties); a threat can affect multiple tenants in a multi-tenant system (blast radius is all tenants); a threat involves a cryptographic failure (broken algorithm, key exposure, certificate misconfiguration); a threat enables server-side code execution or infrastructure privilege escalation; or a DPIA (Data Protection Impact Assessment) is required by GDPR Article 35 (new processing of biometric data, large-scale monitoring, systematic profiling).

# Critical Details

- **The most dangerous gap in threat modeling: missing insider and abuse-of-trust threats.** The assumption that threat actors are always external attackers misses: a customer support agent who can search all customer records without audit logging; a developer who can read production database credentials from the CI/CD system; a batch job with an overly broad IAM role that can access unrelated S3 buckets. Insider threat modeling requires examining every "trusted" actor that has elevated access and verifying that access is audited, minimal, time-bounded, and monitored.
- **Trust boundary crossings are where most injection vulnerabilities originate.** SQL injection, command injection, LDAP injection, XPath injection, and SSRF all originate at a trust boundary crossing where attacker-controlled input is used in a context (SQL query, shell command, network request) without proper validation or parameterization. Every trust boundary crossing must have explicit input validation design, and the design must specify the validation technique (parameterized queries — not input sanitization — for SQL; allowlist for network targets — not URL validation — for SSRF).
- **Threat model must be updated when the design changes.** A threat model completed at the start of a feature that is then significantly redesigned may no longer reflect the actual trust boundaries and attack surfaces. The threat model is a living artifact — it must be revised when: a new integration is added; a new actor is introduced; a new data flow crosses a trust boundary; or a "temporary" workaround becomes permanent.
- **Mitigations without tests do not exist.** A rate limiting control that is designed but not tested may be incorrectly configured (limit is 1000 per second instead of 10 per 15 minutes); may be applied to the wrong endpoint; or may be bypassed by a different request path. Every Critical and High severity mitigation must have a passing automated test before the threat is considered mitigated.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| Threat model lists "encrypt sensitive data" without specifying algorithm, key management, or scope | Implemented with MD5 (broken); no key rotation; encrypts only 3 of 10 sensitive fields | Specify: AES-256-GCM; key stored in Vault; rotation every 90 days; field list explicit |
| Admin endpoint added with auth check: "users must be logged in" | Any authenticated user can invoke admin action (missing role/permission check) | RBAC check: `requireRole('admin')`; audit log on every call; re-auth for destructive actions |
| IDOR not modeled because "users are expected to know their own IDs" | User A discovers that changing `?orderId=123` to `?orderId=124` returns User B's order | Ownership check: `assert order.userId === request.user.id` before every resource return |
| Residual risk accepted as "we'll fix it in the next sprint" with no owner or date | Risk never reviewed; becomes permanent; discovered in penetration test 18 months later | Formal acceptance: owner = security-lead; review date = 30 days; JIRA ticket filed |
| Trust boundary not drawn at backend → third-party API | Third-party API returns malicious payload that is directly rendered in UI (XSS via API) | Validate and sanitize third-party API responses; treat as untrusted input |
| Threat model completed at design phase; not updated after architecture change | New file upload endpoint added; no threat model for upload attack surface | Threat model updated on each PR that adds entry points or trust boundary crossings |

# Failure Modes

- **IDOR in new API endpoint:** user ID in URL parameter not checked against session; data leak to any authenticated user.
- **Admin action added with authentication but no authorization:** any user can invoke admin endpoint.
- **File upload without MIME validation:** malicious file uploaded; served to other users.
- **Rate limiting designed but not configured correctly:** 10,000 brute-force attempts succeed overnight.
- **JWT secret committed to repository:** all sessions can be forged; all users compromised.
- **SSRF via user-supplied URL:** attacker reads AWS metadata endpoint; obtains EC2 instance credentials.
- **Stale model after architecture change:** new callback, worker, or storage path is added after design review and ships outside the threat inventory.
- **Mitigation without observability:** control is implemented but no audit, alert, metric, log, or runbook proves exploitation attempts would be detected.
- **Old memory accepted as current proof:** prior review says the boundary is safe, but current graph exposes a new caller, tenant path, generated artifact, or deployment route.

# Output Contract

Return `threat_model_review` with:

- `assets` (name, classification, owner, applicable regulation)
- `actors` (external attacker / insider / legitimate user abusing workflow / automated system)
- `trust_boundaries` (every boundary with incoming/outgoing trust levels)
- `entry_points` (every API endpoint, file upload, webhook, admin action, third-party callback)
- `data_flows` (data flow diagram with trust boundary crossings marked)
- `threats` (per threat: STRIDE category, description, actor, entry point, assets at risk, likelihood, impact, CVSS score if applicable)
- `mitigations` (per threat: control, implementation location, status, test ID)
- `monitoring` (per threat: detection signal, alert, incident response)
- `residual_risks` (per accepted risk: rationale, owner, review date, escalation trigger)
- `verification_evidence` (per Critical/High threat: test ID, passing status, monitoring deployed)
- `graph_memory_execution_validation` (repository paths and generated artifacts inspected, project-memory claims accepted or rejected, execution evidence used, validation freshness, and unknowns)
- `threat_to_validation_map` (each Critical/High and selected Medium threat mapped to required control, owner, test/review artifact, monitoring signal, and release gate)
- `reuse_and_placement_rationale` (existing security control, policy module, validator, monitor, fixture, reference, and skill source reused or rejected; why no duplicated control or speculative abstraction was introduced)
- `behavior_preservation` (legitimate old access, existing mitigations, expected denials, audit behavior, rollout and rollback behavior preserved or intentionally changed)
- `validation_evidence` (command, validator, test, scanner, report, output, exit code, artifact, screenshot when relevant, and freshness after final edit)
- `evidence_limits` (uninspected entry points, missing logs, stale architecture notes, unrun tests, unavailable environments, and residual uncertainty owners)

# Evidence Contract

Close a threat model only when these answers are concrete:

- **Boundary basis and boundaries inspected:** selected mode, protected assets, actors, entry points, data flows, trust boundaries, source/config paths, generated artifacts, tests, monitoring definitions, registry/project memory, and skipped boundaries with reason.
- **Reuse / placement rationale:** existing control, policy module, validator, secret store, gateway, service boundary, monitor, fixture, or reference reused; duplicated controls, client-only checks, paper mitigations, and speculative abstractions rejected.
- **Validation evidence:** each Critical/High threat maps to command, validator, test, scanner, report, output, exit code, manual review artifact, monitoring signal, owner, and evidence freshness after the final change.
- **What evidence proves:** the inspected source path, test, alert, or review demonstrates the named mitigation for the named threat, actor, asset, and boundary.
- **What evidence does not prove:** scanner passes, stale diagrams, old project memory, generated summaries, or partial tests do not prove uninspected routes, environments, tenants, integrations, or future architecture changes.
- **Behavior preservation:** legitimate old access, existing security controls, expected denials, audit events, monitoring, rollout, and rollback behavior are preserved or intentionally changed with release approval.
- **Residual risk and next gate:** every remaining Critical/High risk has owner, rationale, expiry, compensating control, escalation trigger, and next gate such as `security-privacy-gate`, `quality-test-gate`, `delivery-release-gate`, or incident follow-up.

# Benchmark Coverage

Use STRIDE for systematic enumeration, PASTA for business-impact sequencing, OWASP ASVS/Top 10/API Top 10 for control requirements, NIST SP 800-30 for likelihood and impact calibration, CWE/CVSS for vulnerability severity, SDL for lifecycle placement, and GDPR DPIA criteria for high-risk personal-data processing. Benchmark references must drive threat selection, severity, mitigation, or evidence; do not cite frameworks without a decision they changed.

# Routing Coverage

- Pair with `permission-boundary-modeling` and `authentication-security` when abuse paths involve identity, role, tenant, object, or privilege boundaries.
- Pair with `input-validation`, `web-security`, and `secret-configuration-security` when threats involve injection, XSS/CSRF/SSRF, upload abuse, token exposure, credentials, or cryptography.
- Pair with `dependency-vulnerability-scanning`, `kubernetes-gateway`, and `delivery-release-gate` when the attack surface comes from packages, cloud/IaC, ingress, IAM, KMS, release sequencing, or rollout.
- Pair with `reliability-observability-gate` and `logging-error-handling` when mitigation depends on monitoring, audit logs, alerting, rate limits, abuse detection, or incident visibility.
- Pair with `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker` whenever the model depends on graph reachability, remembered prior state, command evidence, or validation freshness.

# Quality Gate

The threat model is complete only when:

1. All assets are classified with applicable regulation.
2. Both external attacker and insider/abuse-of-trust actors are modeled.
3. Every trust boundary is drawn and all crossings have validation design.
4. All threats have STRIDE category, likelihood, and impact rating.
5. All Critical and High threats have an implemented, tested mitigation.
6. All mitigations have test IDs with passing status.
7. All production entry points have a monitoring/detection signal.
8. All residual risks have owner, rationale, and review date.
9. DPIA flag is set if GDPR Article 35 processing applies.
10. Threat model is current with the final design (updated after any architecture change).
11. Repository graph inspection covers current entry points, callers, external integrations, generated artifacts, and deploy/IaC exposure or explicitly marks each unavailable.
12. Project memory and previous threat models are dated, scope-checked, and rejected as proof when stale.
13. Every Critical/High threat appears in `threat_to_validation_map` with an implementation location, owner, test or review artifact, monitoring signal, and release gate.
14. No Critical unmitigated threat is accepted without explicit security-owner approval and expiry.
15. Tool, connector, scanner, or agent execution used to gather evidence has permission, sandbox, redaction, and rollback classification.

# Used By

- security-privacy-gate
- architecture-impact-reviewer

# Handoff

Hand off to `web-security` for browser exploit classes; `authentication-security` for identity lifecycle hardening; `input-validation` for boundary validation design; `secret-configuration-security` for secret exposure; `permission-boundary-modeling` for authorization model; `dependency-vulnerability-scanning` for third-party risk.

# Completion Criteria

The capability is complete when **every high-impact threat has a concrete implemented and tested mitigation or a formally accepted residual risk with owner and review date — and no Critical severity threat is accepted without explicit security-lead sign-off**.
