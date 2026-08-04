# Error Code Design Industry Benchmarks

Load this reference only when public API/SDK error semantics, retryability, authorization disclosure, catalog compatibility, or release documentation changes. RFC 9457/HTTP/gRPC conventions are anchors, not substitutes for the current contract.

## Error Semantics Matrix

| Situation | Contract decision | Guardrail |
| --- | --- | --- |
| Malformed input | Syntax/shape error distinct from semantic/domain rejection. | Stable code/type and safe field violations; never map parser failure to server fault. |
| Authentication/authorization | Distinguish missing/invalid identity from denied action; choose revealing or non-revealing absence from the threat model. | Cross-user/tenant tests prove no existence or policy leak. |
| Missing/conflict/precondition | State whether absent, filtered, deleted, duplicate, version conflict, or failed precondition differs. | Caller action and idempotent replay behavior are explicit. |
| Rate/quota pressure | Return the local rate-limit contract and provider delay when trustworthy. | Retry guidance does not amplify overload or expose quota internals. |
| Dependency/server failure | Translate provider/internal errors to stable opaque categories. | Do not leak body, stack, SQL, secret, policy, topology, or raw exception names. |
| Timeout/unknown outcome | State whether the operation may have committed and how to reconcile. | Retry only after idempotency/side-effect safety is proven. |
| Validation/business denial | Preserve machine code and safe remediation independently of localized message text. | When a public API or SDK client selects behavior from the error, it branches on a stable machine code or problem type; prose remains human guidance that may be localized or revised. |

## Catalog And Response Contract

- A stable catalog entry names namespace/code or problem `type`, transport mapping, owner, retryability, idempotency requirement, consumer action, support action, redaction, and compatibility status.
- Separate stable machine fields from occurrence details and correlation identifiers in client-visible problem details or the local envelope.
- Allowlist field-violation paths and echoed values according to the disclosure policy.
- Keep code values and meanings stable while allowing localized user messages and internal diagnostic templates to evolve. Retire a code through consumer inventory, bridge/version/deprecation, and current usage evidence.
- HTTP/gRPC/status mappings follow the current platform contract and information-disclosure policy; this reference does not prescribe one universal status for every business failure.

## Retryability And Validation

| Change | Required proof |
| --- | --- |
| Code/type/status mapping | Catalog lint, API example/contract test, and affected client branch. |
| Authorization posture | Wrong-user/tenant denied path and explicit 403/404-style disclosure decision. |
| Retryability | Failure-class fixture, provider guidance, retry/deadline budget, idempotency or duplicate-side-effect proof, and terminal owner. |
| Validation violation | Field path/code and rejected-value redaction fixture. |
| Generated SDK/docs | Fresh generated diff/compile or named residual-risk owner. |
| Raw/internal translation | Negative response/log assertion excludes provider body, stack, SQL, secrets, and policy names. |

Inspect current controllers/mappers, schemas, generated clients, SDK/frontend/mobile handling, form maps, docs, tests, and support workflows. Repository search cannot prove unknown external consumers; name that risk and owner. Re-run evidence after the final code/status/retryability or generated-artifact edit.

Route input violation design to `input-validation`, compatibility/deprecation to `version-compatibility`, consumer behavior to `consumer-impact-analysis`, retry/side-effect safety to `idempotency-retry-design`, and sensitive disclosure to `security-privacy-gate`.

Reject codes copied from exception names, prose-only branching, universal retry by 4xx/5xx family, and fixed backoff without operation/provider evidence. Also reject raw error pass-through, stale “no consumers” claims, and catalog entries without an owner and remediation.
