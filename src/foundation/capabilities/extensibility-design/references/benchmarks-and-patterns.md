# Extensibility Benchmarks And Patterns

Use this reference when an extensibility-design output needs pattern choice, benchmark detail, compatibility classification, or anti-pattern correction beyond the compact `SKILL.md` body. Keep it bounded to decisions that change extension shape, validation depth, owner, or release compatibility.

## Pattern Selection Matrix

| Variation shape | Use when | Required guardrails | Reject when |
| --- | --- | --- | --- |
| Direct implementation | One concrete behavior is known and change is local. | Revisit trigger, owner, and deletion path for speculative interface proposals. | Two or more current implementers need different behavior behind the same contract. |
| Strategy interface | Multiple in-process algorithms share a narrow input/output contract. | Contract tests, invariant guard, typed errors, owner, and default behavior. | Consumers need lifecycle, discovery, isolation, or third-party ownership. |
| Template method | A core lifecycle is fixed and only bounded steps vary. | Non-overridable invariant steps, final validation, and documented hook order. | Extensions need to reorder core workflow or touch privileged state. |
| Plugin registry | Implementers are discovered or enabled dynamically across teams or packages. | Registration owner, compatibility version, capability metadata, sandbox class, and per-plugin observability. | Only one implementer exists or registry order changes semantics. |
| Webhook/callback | External parties receive events or call back asynchronously. | Signed payloads, retry/DLQ/reconciliation, SSRF denial, versioned payload, timeout, and idempotency. | Caller needs synchronous core-domain authorization, pricing, or transaction mutation. |
| Provider abstraction | Multiple vendors supply equivalent capability behind a stable domain contract. | Provider contract tests, timeout/fallback policy, error taxonomy, cost/latency budget, and migration plan. | Vendor differences leak into every caller or only one provider is planned. |
| Configuration variation | Behavior differs by typed policy, flag, tenant, or environment. | Schema validation, bounded values, defaults, owner, expiry/cleanup, and not-present test. | Config becomes arbitrary logic, expressions, SQL, templates, or unbounded JSON. |
| Metadata/custom fields | Tenants or consumers need additional data shape without changing core schema. | Type constraints, storage limits, indexing rules, validation, privacy class, and query/report semantics. | Core invariants or authorization depend on arbitrary metadata. |

## Compatibility Classification

| Change | Class | Required evidence |
| --- | --- | --- |
| Add optional method, config field, event field, or provider capability with default behavior | Minor-compatible | Old implementer test, new default behavior test, docs/changelog, and generated artifact diff when applicable. |
| Add required method, required config, required event field, stricter validation, or changed default | Breaking | Implementer inventory, migration guide, deprecation window, old/new compatibility test, release/rollback handoff. |
| Remove method, rename type, change semantics, narrow accepted values, or remove config | Breaking | Consumer impact, version bump, deprecation notice, rollback/yank path, and owner approval. |
| Tighten sandbox, deny network/FS/DB access, or change timeout/retry semantics | Compatibility-sensitive | Security rationale, known extension impact, failure-mode test, and release communication. |
| Remove unused extension point or flag | Cleanup | Current graph search, telemetry or not-present evidence, rollback/removal path, and owner/date. |

## Boundary Patterns

- **Core-owned invariants:** authorization, validation, pricing, accounting, audit, tenant isolation, retry/idempotency, and state transitions stay outside extension control. Extensions may receive read-only views or produce candidate outputs that core logic validates.
- **Typed contract first:** prefer explicit method signatures, schema fields, error types, and lifecycle states over generic maps, string commands, or reflection.
- **Least privilege by extension class:** in-process strategy gets no filesystem/network access; out-of-process plugins use allowlisted network and service APIs; webhooks receive signed bounded payloads; tenant config cannot invoke code.
- **Observability per implementer:** include extension ID, version, tenant or owner, invocation path, duration, result, error class, and redacted input/output summary.
- **Lifecycle ownership:** each extension point has interface owner, implementer approval owner, on-call escalation, deprecation owner, support window, and cleanup trigger.

## Anti-Pattern Corrections

| Anti-pattern | Required correction |
| --- | --- |
| One implementation hidden behind provider or plugin interface | Keep direct implementation; record the second-use trigger and deletion/revisit owner. |
| Generic `execute(context)` or `run(payload)` contract | Replace with typed inputs, bounded outputs, error taxonomy, and invariant guard. |
| Extension mutates core domain object directly | Pass read-only snapshot; core applies validated command/result after invariant checks. |
| Arbitrary JSON, expressions, SQL, template fragments, or shell snippets as config | Replace with schema-defined fields, bounded enums, validation, and negative tests. |
| Registry order changes business semantics | Make priority/order explicit, deterministic, owned, tested, and observable. |
| Webhook URL accepts private/internal addresses | Deny private ranges and metadata hosts; require allowlist, signing, timeout, retry, and reconciliation. |
| Feature flag lives after rollout with no owner | Convert to durable config with governance or schedule cleanup with not-present validation. |

## Efficiency Guardrail

Do not load this reference for simple routing, a local one-off implementation, or a speculative abstraction rejection already covered by `SKILL.md`. Load it only when the selected pattern, compatibility class, sandbox shape, or anti-pattern correction changes the plan.
