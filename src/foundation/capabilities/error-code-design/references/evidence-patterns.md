# Error Code Design Evidence Patterns

Use this reference when closure depends on proving a client-visible error contract, safe diagnostic separation, compatibility, retryability, authorization posture, or graph/memory claim. Keep the main capability body for routing and output shape; load this file only for concrete evidence mapping.

## Claim To Evidence Map

| Claim | Strong evidence | Weak or invalid evidence | Residual risk if absent |
| --- | --- | --- | --- |
| Error code is stable and branchable | Catalog/spec entry plus test or generated-client fixture that branches on `code` or `type` | Human-readable message text only | Client logic breaks on copy/localization changes |
| Transport status is correct | HTTP/gRPC/GraphQL mapping test or contract fixture | Controller convention with no negative case | Caches, metrics, retries, and SDKs misclassify failure |
| Raw internals are suppressed | Negative test or reviewed translation path for stack, SQL, provider, secret, token, PII, tenant, and policy detail | Logger redaction only; happy-path error response | CWE-209 information exposure or provider/secret leak |
| Authorization posture avoids enumeration | 401/403/404 resource-class decision plus denied-case proof | Single generic auth test | User, tenant, object, or account existence leak |
| Validation errors are actionable | Field path, violation code, safe echo policy, and invalid-input fixture | One generic `invalid input` message | Forms, SDKs, and clients cannot repair input safely |
| Retryability is safe | Retry matrix, `Retry-After` or backoff, idempotency requirement, duplicate-side-effect proof | Marking 503/429 as retryable with no idempotency review | Retry storm or duplicate payment/order/state change |
| Generated clients and docs are fresh | OpenAPI/proto/docs generator command, diff, and compile/contract result | Generated artifact timestamp or memory claim | Public SDK/docs diverge from runtime behavior |
| Diagnostics remain traceable | Response trace/request id plus log/metric linkage with bounded labels | Screenshot-only support workflow | Support cannot correlate failures or metrics explode |

## Evidence Labels

- **Strong**: current source path, status/code map, negative fixture or contract test, command, exit code, and artifact after final edits.
- **Weak**: stale docs, manual statement, graph-only caller list, one happy-path example, or a test that does not hit the changed error.
- **Missing**: no translation boundary inspected, no raw-detail test/review, no consumer check, no retry/idempotency decision, or no trace behavior.
- **Invalid**: branch behavior based on localized message, evidence from a different error surface, stale generated clients after catalog edit, or raw provider body treated as public contract.

## Changed Error To Validation Map

For each changed code, status, message key, retryability rule, authorization posture, validation violation, provider mapping, generated artifact, and support path, record:

```yaml
error_validation_map:
  surface: ""
  code_or_type: ""
  change_kind: new | rename | status | message | retryability | auth_posture | validation_shape | provider_mapping | generated
  compatibility_class: compatible | conditional | breaking | unknown
  source_paths: []
  consumers_checked: []
  validation:
    command: ""
    exit_code: null
    artifact_or_log: ""
    proves: ""
    does_not_prove: ""
  diagnostic_separation: ""
  residual_risk:
    owner: ""
    reason: ""
```

## Closure Checks

- Reject closure if a public code/status/retryability changed without compatibility classification and consumer or generated-client evidence.
- Reject closure if raw exception, SQL, provider, secret, token, PII, tenant, prompt, or internal policy detail can reach the client response.
- Reject closure if 401/403/404 behavior can expose existence and no resource-class posture or denied proof exists.
- Reject closure if retryable write errors lack idempotency or duplicate-side-effect evidence.
- Downgrade memory, graph, trajectory, and stale report claims unless current source paths and fresh validation confirm them.
