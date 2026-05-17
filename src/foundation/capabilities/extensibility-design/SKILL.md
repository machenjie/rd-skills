---
name: extensibility-design
description: Designs extension points from known variation while rejecting speculative abstraction and unmanaged customization.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "24"
changeforge_version: 0.1.0
---

# Mission

Design extension points **only where proven variation, explicit ownership, defined compatibility contracts, and bounded security scope justify the added abstraction** — rejecting speculative generalization and ensuring every variation mechanism has a narrow contract, validation boundary, deprecation path, and operational owner.

# When To Use

Use this capability when a change introduces: plugin interfaces or plugin registries; hook systems (pre/post hooks, middleware chains); strategy pattern implementations for interchangeable algorithms; configuration-driven behavior selection (feature flags, provider selection, policy injection); template or protocol extension points for third-party customization; provider abstractions over interchangeable integrations; custom field or metadata extension schemas; or webhook/callback systems for external party integrations.

# Do Not Use When

Do not use this capability to generalize a single concrete implementation in hopes that a second use case will emerge later. Generalization without proven variation is speculative abstraction — it adds indirection without reducing real duplication, makes code harder to read, and creates support obligations without delivering value. Do not use it when a direct product decision (choose this provider, implement this algorithm) is simpler and just as maintainable for the known scope.

# Non-Negotiable Rules

- **Extension points require proven variation, not hoped-for variation.** "We might need this later" is not justification. Required evidence: (1) at least two concrete known variation cases currently needed; (2) the variation is owned by different teams, tenants, or external parties; OR (3) the variation is explicitly documented in product roadmap with a committed delivery date.
- **Invariants must not be bypassable by extensions.** Extensions must not circumvent: input validation, authorization checks, rate limiting, audit logging, financial calculation rules, regulatory constraints, or tenant isolation. Any extension that bypasses an invariant must be rejected at design time.
- **The extension contract is a compatibility commitment.** Once an extension interface (plugin interface, hook signature, configuration schema) is exposed to external parties or across team boundaries, changing it is a breaking change. The contract must be versioned. Deprecation requires a minimum notice period (2 sprints internal, 1 release cycle external).
- **Security boundary is explicit.** An extension that executes third-party code, receives tenant-supplied data, or calls external services must be sandboxed. Define: what resources the extension can access (filesystem: no; network: limited to allowlisted hosts; database: via service API only, not direct SQL). Extensions that need elevated privilege must be explicitly authorized, not implicitly granted.
- **Validation of extension-supplied data is mandatory.** Configuration provided by extension implementers, tenant-supplied plugin parameters, and webhook payloads must be validated against a strict schema before use. Never pass raw extension-supplied data to database queries, template engines, or shell commands.
- **Every extension point has an owner and lifecycle.** Who maintains the interface? Who approves new implementers? Who is on-call when an extension causes a production incident? Who decides when the extension point is deprecated? These must be answered before the extension point is implemented.
- **Observability per extension.** When an extension executes, its execution must be traceable: which extension ran, how long it took, whether it succeeded or failed, and what the input/output was (with PII redacted). Without this, extension-caused failures are undiagnosable in production.

# Industry Benchmarks

Anchor against: **Open-Closed Principle** (SOLID, Martin) — software entities should be open for extension, closed for modification; but OCP must be applied only where variation is real, not preemptively. **Strategy Pattern** (GoF, 1994) — encapsulate interchangeable algorithms; select at runtime via injection; interface defines the contract. **Template Method Pattern** (GoF) — fixed algorithm skeleton with extension points for variable steps; subclasses override steps, not the skeleton. **Plugin Architecture** — Java `ServiceLoader` (JDK 6+): `META-INF/services/` registration for interface implementations; Python entry points (`importlib.metadata`): `[project.entry-points."my.plugin"]` in `pyproject.toml`; VS Code Extension API: contribution points in `package.json`. **OSGi** — modular Java component framework; dynamic plugin lifecycle; used in Eclipse, Jenkins. **Webhook Design (Stripe, GitHub)** — HTTPS POST to consumer-defined URL; HMAC-SHA256 signature for payload verification; retry with exponential backoff; event payload versioned; consumer must return 2xx within 5 seconds. **Feature Flag Systems** — LaunchDarkly, Unleash, GrowthBook; flag types: release toggle, experiment flag, ops flag, permission flag; flag evaluation must not require network call in hot path; stale flag cleanup governance. **Extension Registry Pattern** — central registry of extension implementations; registry validates extension metadata at registration; registry enforces security policy at extension load time. **Configuration Schema Governance** — JSON Schema Draft 2020-12 for configuration validation; Avro/Protobuf for binary config schemas; configuration changes must not break existing installations silently. **OWASP API Security Top 10 — A07:2023 Server-Side Request Forgery (SSRF)** — a webhook/callback URL provided by extension/tenant must be validated against an allowlist; SSRF allows attackers to call internal services. **CWE-20** — Improper Input Validation; extension-supplied data must be validated before use. **Event-Driven Extension Pattern** — extensions subscribe to platform events; platform does not call extensions synchronously in critical paths; decoupled via broker. **Strangler Fig Pattern** — progressively extend a system by routing specific behaviors to new implementations; original behavior remains until extension is fully proven.

### Extension Point Justification Matrix

| Criterion | Required | Evidence format |
| --- | --- | --- |
| ≥ 2 concrete known variations exist now | Yes | List the 2+ concrete cases |
| Variation owned by different teams/tenants/parties | Yes (for multi-tenant/plugin) | Named owners per variation |
| Roadmap commitment for variation | Yes (if not current) | Linked roadmap item with date |
| Invariant safety confirmed | Yes | List invariants that extension cannot bypass |
| Security sandbox defined | Yes | Access policy: filesystem, network, DB |
| Owner assigned | Yes | Named team and on-call |
| Deprecation policy defined | Yes | Notice period; migration guide |
| Observable: trace, log, metrics per invocation | Yes | Instrumentation spec |
| Approved alternative considered and rejected | Yes | Why simpler direct implementation rejected |

### Extension Contract Versioning

| Change type | Compatible? | Required action |
| --- | --- | --- |
| Add optional method to interface with default | ✅ Backward-compatible (if language supports) | Minor version bump; document |
| Add optional config field with default | ✅ Backward-compatible | Minor version bump; update schema |
| Remove interface method | ❌ Breaking | New major version; deprecation period |
| Change method signature | ❌ Breaking | New major version; migration guide |
| Change config field type | ❌ Breaking | New major version |
| Change config field semantics | ❌ Breaking — silent corruption risk | New field name; deprecate old |
| Remove config field | ❌ Breaking | New major version; migration |
| Add required config field | ❌ Breaking for existing implementers | New major version |

### Security Boundary Rules per Extension Type

| Extension type | Network access | FS access | DB access | External API | Sandbox |
| --- | --- | --- | --- | --- | --- |
| Configuration-driven behavior | None | None | Via service API only | Allowlisted only | Policy enforcement |
| In-process plugin (same JVM/process) | Restricted | None | Via repository interface only | None by default | Interface contract |
| Out-of-process plugin (subprocess) | Allowlisted hosts | Read-only temp dir | None (no direct DB) | Allowlisted only | Process isolation |
| Webhook to external party | N/A (outbound) | N/A | N/A | External party receives event | SSRF validation on URL |
| Tenant-supplied script (low-code) | None | None | None | None | Sandboxed interpreter (Lua, Deno, Wasm) |
| Third-party integration (OAuth app) | Via API only | None | None | API rate-limited | OAuth scopes |

### Feature Flag Governance

```
Flag types and intended lifecycle:
  Release flag:     temporary; feature development; remove within 1 sprint of full rollout
  Experiment flag:  temporary; A/B test; remove after statistical significance reached
  Ops flag:         long-lived; kill switch or config control; requires regular review
  Permission flag:  long-lived; user/tenant entitlement; managed via permission system

Flag lifecycle rules:
  1. Flag created with: owner, purpose, type, target rollout date, removal date (estimate)
  2. Flag evaluation: must not require network call in hot code path (cache flag state)
  3. Stale flag cleanup: flags unused for > 90 days → auto-alert to owner
  4. Flag removal: merged code; deleted from flag system; tests updated

Anti-pattern — permanent flags:
  Never use feature flags as permanent configuration. Configuration belongs in config files.
  A flag that lives for > 6 months without type = ops flag is a config file in disguise.
```

# Selection Rules

Select this capability when a **variation mechanism is being introduced or modified**. Adjacent routing:

- Prefer `architecture-tradeoff-analysis` when choosing between broad structural alternatives (e.g., plugin system vs. configuration vs. service-per-tenant).
- Prefer `api-contract-design` when the extension point is an external API contract consumed by third parties.
- Prefer `version-compatibility` when managing breaking changes to existing extension contracts.
- Prefer `security-privacy-gate` when the extension could execute privileged code, handle PII, or affect tenant isolation.
- Prefer `configuration-management` when runtime configuration governance (not code extension) is the primary concern.

# Risk Escalation Rules

Escalate when: an extension can execute code that modifies financial calculations, authorization decisions, or tenant data boundaries; a webhook URL is provided by a tenant or external party (SSRF risk); extension-supplied configuration is used in SQL queries, template engines, or shell commands without validation; a plugin interface is proposed to be removed or changed with no documented migration path for existing implementers; an extension has no assigned owner and no on-call responsibility.

# Critical Details

Every extension point is a product and operations commitment that outlasts its author. Precision failures:

- **Speculative abstraction.** An engineer adds a `PaymentGatewayProvider` interface "for future providers" when only Stripe is in the roadmap. The interface is never used for a second provider, but every future engineer must understand it, and every test must mock it. The abstraction has no ROI.
- **Bypass of domain invariants.** A hook system allows pre-processing of price before checkout. An implementer's hook modifies the cart total before tax calculation. The tax module sees the modified total; the original total is lost; financial records are inconsistent. Extension points that touch financial or authorization data must receive a read-only view.
- **Unvalidated webhook URL.** A tenant configures a webhook URL: `https://internal-metadata.svc.cluster.local/latest`. The platform calls this URL from inside the cluster. The tenant receives internal AWS/GCP metadata including IAM tokens. SSRF attack via extension-supplied URL. Validate all webhook URLs against an allowlist of allowed hosts; block private IP ranges (RFC 1918: 10.x, 172.16–31.x, 192.168.x).
- **Configuration as untyped programming.** A "flexible configuration" object accepts arbitrary JSON that the system evaluates. Implementers use it to embed logic, conditional expressions, and DSL strings. Configuration has become a programming language with no static analysis, no test coverage, no type safety, and no access control. Every configuration field must have a schema and a bounded set of valid values.
- **Extension without observability.** An in-process plugin hook runs before every API request. One tenant's plugin begins throwing exceptions after an update. All their requests fail. The platform logs a generic error; there is no per-extension trace. Diagnosis takes hours. Every extension invocation must log: plugin ID, duration, success/failure.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| `interface PaymentProvider` with only one known implementer | Speculative abstraction; adds indirection; no ROI |
| Hook modifies `order.totalAmount` before tax calculation | Invariant bypass; tax calculated on wrong amount |
| Webhook URL accepted without SSRF validation | Tenant calls `169.254.169.254` (AWS metadata); IAM token exfiltrated |
| Plugin config accepts arbitrary JSON expressions | Configuration becomes Turing-complete; no schema; no audit |
| Plugin interface changed without version bump or migration | All existing implementers silently broken on upgrade |
| Feature flag `feature_newDashboard` exists for 18 months | Permanent flag; undocumented config; can't be removed safely |
| Extension invocation not traced | Production incident; unknown which plugin caused failure |
| Extension can call `db.query(sql)` directly | SQL injection via plugin; bypass of data access controls |

# Failure Modes

- Speculative `NotificationProvider` interface implemented for only Twilio; second provider never materializes; interface maintained for 3 years; removed in v2 breaking all internal tests.
- Pre-checkout hook modifies price field without authorization; tenant exploits to set price to $0.01; financial loss.
- Tenant-supplied webhook URL `http://192.168.1.1/admin`; platform calls it; exposes internal admin panel.
- Plugin config schema not enforced; implementer passes `{"command": "DROP TABLE orders"}` in a template field; SQL injection in template renderer.
- Extension interface `v1.processPayment(amount)` changed to `v1.processPayment(amount, currency)` without version bump; all existing plugins throw `ArgumentError`; production down.
- Feature flag `show_old_nav` never removed; 2 years later, no one knows if removing it is safe; both code paths maintained indefinitely; dead code accumulates.
- Extension invocation not traced; tenant plugin causes 200ms latency spike on every request; found only after 3-week performance investigation.
- Out-of-process plugin granted filesystem read; reads `/etc/secrets/db.password`; exfiltrates credentials via allowed outbound network call.

# Output Contract

Return an extensibility plan with:

- `known_variation_cases` (list ≥ 2 concrete cases; or roadmap reference)
- `invariants` (list of invariants the extension must not bypass; enforcement mechanism)
- `extension_contract` (interface definition, method signatures, config schema, data types)
- `contract_version` (current version; compatibility mode; deprecation policy)
- `allowed_implementers` (named teams, tenants, or external parties; approval process)
- `security_boundary` (network, filesystem, DB, external API access policy per extension type)
- `validation_rules` (schema for extension-supplied data; SSRF validation for URLs; input sanitization)
- `sandbox_mechanism` (in-process interface contract / subprocess isolation / interpreted sandbox)
- `lifecycle_policy` (creation approval, review cycle, deprecation notice period, removal criteria)
- `observability` (per-invocation: extension ID, duration, success/failure, input/output summary)
- `test_matrix` (invariant bypass attempt, malformed extension input, extension failure isolation, perf impact)
- `rejected_alternatives` (simpler direct implementations considered; why extension point chosen)
- `owner` (team, on-call rotation, decision authority for new implementers)

# Quality Gate

The extensibility design is complete only when:

1. ≥ 2 proven concrete variation cases documented; no speculative generalization.
2. All domain invariants listed with enforcement mechanism that extension cannot bypass.
3. Extension contract versioned; breaking vs. non-breaking change classification documented.
4. Security boundary explicit per extension type; SSRF validation for URLs; no direct DB or FS access.
5. Validation schema defined for all extension-supplied configuration and data.
6. Sandbox/isolation mechanism specified and commensurate with extension privilege level.
7. Owner assigned; lifecycle policy (approval, review, deprecation) documented.
8. Per-invocation observability (trace, log, metrics) specified.
9. Simpler alternatives considered and rejection rationale documented.
10. Test matrix covers: invariant bypass attempt, malformed input, extension failure isolation, performance impact.

# Used By

- architecture-impact-reviewer
- ai-code-review-refactor

# Handoff

Hand off to `architecture-tradeoff-analysis` for high-impact structural decisions; `security-privacy-gate` for privileged extension behavior and SSRF validation; `version-compatibility` for extension contract evolution; `api-contract-design` when the extension point is an externally consumed API.

# Completion Criteria

The capability is complete when **every extension point is justified by proven variation, has a narrow versioned contract, cannot bypass domain invariants, is sandboxed commensurate with its privilege level, is fully observable, and has a named owner with a lifecycle and deprecation policy** — with no speculative abstractions, no bypassed invariants, and no unvalidated extension-supplied data.
