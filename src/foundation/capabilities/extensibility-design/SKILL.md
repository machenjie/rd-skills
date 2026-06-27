---
name: extensibility-design
description: Designs extension points only from proven variation, ownership, compatibility contracts, validation boundaries, deprecation paths, and security scope while rejecting speculative abstraction and unmanaged customization.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "24"
changeforge_version: 0.1.0
---

# Mission

Design extension points **only where proven variation, explicit ownership, defined compatibility contracts, and bounded security scope justify the added abstraction** — rejecting speculative generalization and ensuring every variation mechanism has a narrow contract, validation boundary, deprecation path, and operational owner.

# When To Use

Use this capability when a change introduces: plugin interfaces or plugin registries; hook systems (pre/post hooks, middleware chains); strategy pattern implementations for interchangeable algorithms; configuration-driven behavior selection (feature flags, provider selection, policy injection); template or protocol extension points for third-party customization; provider abstractions over interchangeable integrations; custom field or metadata extension schemas; or webhook/callback systems for external party integrations.

Also use this capability when repository graph evidence, project memory, execution traces, tests, generated code, configuration, or prior design notes show speculative abstractions, unmanaged variation, stale extension contracts, unclear owners, or compatibility/security obligations that are not validated.

# Do Not Use When

Do not use this capability to generalize a single concrete implementation in hopes that a second use case will emerge later. Generalization without proven variation is speculative abstraction — it adds indirection without reducing real duplication, makes code harder to read, and creates support obligations without delivering value. Do not use it when a direct product decision (choose this provider, implement this algorithm) is simpler and just as maintainable for the known scope.

# Stage Fit

- **Planning:** prove real variation, owner, contract, lifecycle, invariant boundary, compatibility class, security boundary, and rejected simpler alternative before accepting an extension point.
- **Read/review:** inspect current implementations, callers, generated artifacts, config schemas, tests, docs, existing extension users, and prior compatibility decisions before judging extensibility need.
- **Edit/implementation:** keep the contract narrow, versioned, validated, observable, and unable to bypass invariants; avoid generic managers or strategy bags without concrete variation.
- **Test/release:** require compatibility tests, malformed input tests, invariant-bypass tests, failure isolation, performance budget, migration/deprecation evidence, and owner acceptance.
- **Cleanup/repair:** remove speculative extension points when variation did not materialize, or route breaking contract changes through versioning and deprecation rather than silent mutation.

Use this capability during coding, bug-fix, debugging, code-review, refactoring, testing, release, and handoff whenever an extension mechanism or compatibility claim can outlive the local implementation.

# Non-Negotiable Rules

- **Extension points require proven variation, not hoped-for variation.** "We might need this later" is not justification. Required evidence: (1) at least two concrete known variation cases currently needed; (2) the variation is owned by different teams, tenants, or external parties; OR (3) the variation is explicitly documented in product roadmap with a committed delivery date.
- **Invariants must not be bypassable by extensions.** Extensions must not circumvent: input validation, authorization checks, rate limiting, audit logging, financial calculation rules, regulatory constraints, or tenant isolation. Any extension that bypasses an invariant must be rejected at design time.
- **The extension contract is a compatibility commitment.** Once an extension interface (plugin interface, hook signature, configuration schema) is exposed to external parties or across team boundaries, changing it is a breaking change. The contract must be versioned. Deprecation requires a minimum notice period (2 sprints internal, 1 release cycle external).
- **Security boundary is explicit.** An extension that executes third-party code, receives tenant-supplied data, or calls external services must be sandboxed. Define: what resources the extension can access (filesystem: no; network: limited to allowlisted hosts; database: via service API only, not direct SQL). Extensions that need elevated privilege must be explicitly authorized, not implicitly granted.
- **Validation of extension-supplied data is mandatory.** Configuration provided by extension implementers, tenant-supplied plugin parameters, and webhook payloads must be validated against a strict schema before use. Never pass raw extension-supplied data to database queries, template engines, or shell commands.
- **Every extension point has an owner and lifecycle.** Who maintains the interface? Who approves new implementers? Who is on-call when an extension causes a production incident? Who decides when the extension point is deprecated? These must be answered before the extension point is implemented.
- **Observability per extension.** When an extension executes, its execution must be traceable: which extension ran, how long it took, whether it succeeded or failed, and what the input/output was (with PII redacted). Without this, extension-caused failures are undiagnosable in production.
- **No extensibility claim is valid without current evidence.** Prior memory, roadmap notes, or generated plans can motivate discovery, but the final design must cite current graph reachability, concrete implementers, contract surface, tests, compatibility/deprecation evidence, and security validation or mark the gap as not verified.

# Industry Benchmarks

Anchor against Open-Closed Principle only when variation is proven, GoF Strategy/Template Method when the contract is narrow, plugin registry patterns for implementer discovery and lifecycle, webhook design for signed/retried external callbacks, JSON Schema/Avro/Protobuf for extension configuration contracts, OWASP SSRF and CWE-20 for extension-supplied input, and event-driven or strangler patterns when extension paths must be isolated from critical flows.

Use these benchmarks as gates, not decoration:

- **Justification:** prove two current variations or a dated roadmap commitment; name owner, on-call, lifecycle, rejected direct implementation, invariants, sandbox, observability, and deprecation policy.
- **Compatibility:** optional methods/config with defaults can be minor-version changes; removed methods, signature changes, type/semantic changes, removed config, or new required config are breaking and need migration/deprecation.
- **Boundary governance:** config needs a bounded schema; in-process plugins get interface-limited access; out-of-process plugins require process isolation and no direct DB/FS access; webhooks require SSRF denial, signatures, retries, versioned payloads, and reconciliation.
- **Flag governance:** release/experiment flags need owner, rollout target, cleanup date, cached evaluation, and tests; long-lived ops/permission flags require explicit configuration governance.

# Selection Rules

Select this capability when a **variation mechanism is being introduced or modified**. Adjacent routing:

- Prefer `architecture-tradeoff-analysis` when choosing between broad structural alternatives (e.g., plugin system vs. configuration vs. service-per-tenant).
- Prefer `api-contract-design` when the extension point is an external API contract consumed by third parties.
- Prefer `version-compatibility` when managing breaking changes to existing extension contracts.
- Prefer `security-privacy-gate` when the extension could execute privileged code, handle PII, or affect tenant isolation.
- Prefer `delivery-release-gate` when runtime configuration governance (not code extension) is the primary concern.
- Use **with** `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker` when the decision depends on current caller graph, prior compatibility memory, generated artifacts, test evidence, or stale validation.

# Proactive Professional Triggers

Use this capability proactively, even when the request does not ask for extensibility design:

- **Signal:** a new interface, strategy, plugin, hook, provider registry, callback, config switch, metadata schema, or "generic" manager appears with only one known implementation. **Hidden risk:** speculative abstraction creates permanent compatibility and support burden without reducing real variation. **Required professional action:** demand proven variation, owner, rejected simpler path, and deletion/cleanup decision. **Route to:** `extensibility-design`, `implementation-structure-design`, and `minimal-correct-implementation`. **Evidence required:** known variation list, roadmap/date if applicable, rejected direct implementation, and residual risk.
- **Signal:** extension code can influence authorization, tenant data, pricing, financial calculations, validation, audit, retries, or state transitions. **Hidden risk:** extensions bypass invariants or mutate core domain state. **Required professional action:** define read-only views, invariant guardrails, sandbox/access policy, and invariant-bypass tests. **Route to:** this capability plus `security-privacy-gate`, `business-rule-extraction`, and `quality-test-gate`. **Evidence required:** invariant list, access boundary, bypass test, and owner acceptance.
- **Signal:** extension contracts, plugin APIs, config schemas, generated extension artifacts, or callback payloads change. **Hidden risk:** existing implementers or generated clients break silently. **Required professional action:** classify compatibility, version contract, migration/deprecation path, and consumer validation. **Route to:** `version-compatibility`, `api-contract-design`, `consumer-impact-analysis`, and this capability. **Evidence required:** contract diff, implementer inventory, migration guide, compatibility tests, and not-verified consumers.
- **Signal:** extension-supplied URLs, config values, templates, scripts, payloads, or metadata reach HTTP clients, parsers, renderers, SQL, shell, queues, or external APIs. **Hidden risk:** SSRF, injection, resource abuse, or exfiltration through extension input. **Required professional action:** require schema validation, allowlists, sandboxing, redaction, and failure isolation. **Route to:** `input-validation`, `agent-tool-permission-sandbox`, `secret-configuration-security`, and this capability. **Evidence required:** validation schema, deny tests, sandbox policy, redaction fields, and failure mode tests.
- **Signal:** project memory, old roadmap promises, prior plugin users, previous tests, or generated docs are reused to justify extension support. **Hidden risk:** stale memory can preserve an unused extension point or miss active implementers. **Required professional action:** verify current graph and execution evidence before preserving or changing the extension contract. **Route to:** `project-memory-governance`, `repository-graph-analysis`, `execution-trajectory-analysis`, and this capability. **Evidence required:** accepted/rejected memory, caller/implementer graph, validation freshness, and explicit unknowns.

# Reference Loading Policy

- **L1:** Use only this `SKILL.md` for routing or rejecting a simple speculative abstraction when no concrete extension contract is being designed.
- **L2:** Load `references/checklist.md` for any actual extension point, plugin/hook/provider registry, webhook/callback, config-driven variation, feature flag governance, or compatibility review.
- **L3:** Load `references/benchmarks-and-patterns.md` when selecting plugin, hook, provider, webhook, configuration, or feature-flag patterns; compatibility class; sandbox shape; or anti-pattern correction.
- **L4:** Load `references/evidence-patterns.md` when closure depends on current graph reachability, existing implementers, prior compatibility decisions, generated artifacts, command output, validation artifact, validator result, exit code, or test freshness.
- **L4 output:** Load `examples/example-output.md` when producing a user-facing extensibility plan, evaluation fixture, or structured review table.
- **L5:** Pair with security, reliability, delivery, API/contract, or domain gates only when the extension executes privileged behavior, exposes external contracts, affects release rollout, or crosses regulated/tenant boundaries.

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

- **Speculative provider:** `NotificationProvider` has one Twilio implementation; the second provider never arrives, but the interface constrains tests and removals for years.
- **Invariant bypass:** pre-checkout hook mutates price before tax; tenant can alter financial records outside core validation.
- **Webhook SSRF:** tenant URL points at a private admin or metadata address; platform calls it from a trusted network.
- **Untyped config:** plugin config accepts arbitrary expressions or SQL-like strings; validation, audit, and static review are bypassed.
- **Silent breaking change:** extension interface changes signature or field semantics without version bump, migration, or implementer notification.
- **Permanent flag:** release flag becomes long-lived configuration with no owner, cleanup date, or not-present validation.
- **No extension trace:** plugin latency or failure cannot be attributed to extension ID, version, tenant, or invocation path.
- **Over-privileged sandbox:** out-of-process extension can read sensitive local files or call broad outbound networks.
- **Stale memory proof:** old roadmap or generated docs claim variation exists, but current graph has one implementer.
- **Stale validation proof:** compatibility evidence predates generated contract or config schema changes.

# Output Contract

Return `extensibility_design_plan` with:

- `mode_selected` (create extension point, modify contract, reject abstraction, deprecate/cleanup, or preserve existing extension)
- `extension_decision` (approved, approved with conditions, rejected as speculative, or requires owner/validation before implementation)
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
- `validation_commands` (command or validator, output summary, exit code when runnable, artifact/report path, freshness, what it proves, and what it does not prove)
- `rejected_alternatives` (simpler direct implementations considered; why extension point chosen)
- `owner` (team, on-call rotation, decision authority for new implementers)
- `graph_memory_execution_validation` (callers/implementers/generated artifacts inspected, project-memory claims accepted or rejected, execution evidence, validation freshness, and unknowns)
- `extension_to_validation_map` (extension point -> variation proof, contract compatibility test, invariant/security test, failure/performance test, validator or artifact, exit code, owner, and next gate)
- `evidence_limits` (uninspected implementers, stale roadmap claims, missing consumers, unavailable sandbox evidence, and residual uncertainty owner/date)

# Evidence Contract

Acceptable evidence names:

- **Basis:** selected mode, extension decision, variation mechanism, invariants, compatibility class, security boundary, and rejected simpler alternative.
- **Source evidence:** current source paths, config schemas, generated artifacts, package/API docs, contract diffs, tests, docs, and owner files inspected or explicitly unavailable.
- **Graph evidence:** current callers, implementers, dependency edges, generated consumers, feature flags, webhook consumers, and excluded graph surfaces with reason.
- **Memory evidence:** roadmap notes, prior plugin users, ADRs, incident notes, old validations, and generated summaries accepted, rejected, stale, or not verified with date/scope.
- **Execution evidence:** compatibility tests, schema validation tests, invariant-bypass tests, sandbox/SSRF denial tests, failure-isolation tests, performance evidence, observability checks, or owner approvals with freshness.
- **What evidence proves:** variation is real, the contract is narrow/versioned, invariants remain core-owned, extension input is bounded, and each extension point has owner and lifecycle.
- **What evidence does not prove:** uninspected implementers, production traffic, third-party behavior, future roadmap adoption, unavailable sandbox proof, or compatibility after later generated-artifact changes.
- **Handoff evidence:** next capability/gate, validation artifact, residual unknown, owner, and date for every extension point in the `extension_to_validation_map`.

# Validation Obligations

- Variation proof must be backed by caller/implementer graph, generated artifacts, docs, tests, or a dated roadmap owner; unsupported variation routes to reject/cleanup mode.
- Contract changes require compatibility classification and old/new implementer validation before approval.
- Trust-boundary extensions require schema, sandbox, SSRF/injection denial, redaction, and failure-isolation evidence.
- Validation evidence must name the command, validator, output, exit code, artifact or report, freshness after final edit, what it proves, what it does not prove, and the residual owner.
- Final handoff must state stale/not-run validations and what later source, graph, generated, or config changes would invalidate the evidence.

# Benchmark Coverage

Use OCP only to justify closed-for-modification behavior after variation is proven; use Strategy/Template Method for narrow interchangeable behavior; use plugin registry patterns for discovery/lifecycle; use webhook benchmarks for signed, retried, versioned callbacks; use schema governance for extension input; use OWASP/CWE only when extension input crosses trust boundaries. Benchmark references must change the chosen extension shape, validation depth, compatibility class, or rejection of an abstraction.

# Routing Coverage

- Pair with `architecture-tradeoff-analysis`, `architecture-style-selection`, and `module-boundary-design` when choosing between direct implementation, configuration, plugin, hook, service split, or provider abstraction.
- Pair with `version-compatibility`, `api-contract-design`, and `consumer-impact-analysis` when extension contracts, generated clients, payloads, or external implementers can break.
- Pair with `security-privacy-gate`, `input-validation`, `secret-configuration-security`, and `agent-tool-permission-sandbox` when extensions cross trust boundaries, execute code, receive tenant input, or call external systems.
- Pair with `quality-test-gate`, `validation-broker`, and `reliability-observability-gate` when invariant-bypass, malformed input, failure isolation, performance, or per-extension observability evidence is required.
- Pair with `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `plan-execution-consistency` whenever current graph reachability, prior decisions, command evidence, or plan-to-validation alignment determines whether the extension point should exist.

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
11. Repository graph coverage identifies current callers, implementers, generated artifacts, config schemas, docs, and tests or explicitly marks each unavailable.
12. Project memory, roadmap notes, previous implementer lists, and old validation are dated, scope-checked, and rejected as proof when stale.
13. Every extension point appears in `extension_to_validation_map` with variation proof, compatibility test, invariant/security test, failure/performance test, owner, and next gate.
14. Breaking contract, deprecation, or cleanup decisions include migration, support window, rollback/yank or removal path, and consumer notification evidence.

# Used By

- architecture-impact-reviewer
- ai-code-review-refactor

# Handoff

Hand off to `architecture-tradeoff-analysis` for high-impact structural decisions; `security-privacy-gate` for privileged extension behavior and SSRF validation; `version-compatibility` for extension contract evolution; `api-contract-design` when the extension point is an externally consumed API.

# Completion Criteria

The capability is complete when **every extension point is justified by proven variation, has a narrow versioned contract, cannot bypass domain invariants, is sandboxed commensurate with its privilege level, is fully observable, and has a named owner with a lifecycle and deprecation policy** — with no speculative abstractions, no bypassed invariants, and no unvalidated extension-supplied data.
