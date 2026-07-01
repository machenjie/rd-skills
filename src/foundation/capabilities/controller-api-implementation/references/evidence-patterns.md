# Controller Evidence Patterns

Use this reference when controller closure depends on repository graph, project memory, generated code, execution trajectory, validation freshness, or tool permission boundaries. Treat graph and memory as selectors until current source and validation evidence confirm them.

## Controller Claim To Evidence Map

| Controller claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Controller is thin | Current call graph from handler to service, no repository/provider/domain mutator calls, and forbidden-call scan | The inspected handler delegates non-transport work | Every route in the application is thin |
| Route matches contract | Current route registration, OpenAPI/proto operation, response sample, and status/header map | The inspected operation matches the named contract surface | Unknown clients, undocumented behavior, or service semantics are compatible |
| Input is validated before service call | Validator/schema path, invalid payload case, unknown-field policy, and service-not-called assertion | The inspected request path fails closed before business execution | All alternate entry points or generated clients enforce the same rule |
| Auth context is trusted | Middleware/auth path, token/session source, context extraction code, and body identity rejection | The inspected controller derives identity from trusted context | Authorization policy or object ownership is complete |
| Object authorization is not controller-only | Service/policy boundary, resource lookup owner, denied-case test owner, and no stale controller ownership check | Controller does not become the sole BOLA control | All jobs, imports, and internal calls enforce object authorization |
| Response DTO is explicit | Mapper/serializer path, allowlisted response fields, schema sample, and sensitive-field exclusion | The inspected response avoids internal model leakage | Domain, persistence, or provider internals never change elsewhere |
| Error response is client-safe | Error type map, Problem Details shape, redaction check, trace id, and negative response fixture | The inspected errors are stable and non-leaking | All localization, gateway, SDK, or log sinks preserve the behavior |
| Idempotency header is transport-handled | Header syntax rule, forwarded key/fingerprint, service dedupe owner, duplicate/retry case owner | Controller handles only transport validation and forwarding | Dedupe store, TTL, replay behavior, or side effects are correct |
| Metadata and limits are bounded | Correlation id, content type, page/size limits, rate-limit headers, and log field decision | The inspected route has safe transport metadata and bounds | Production SLOs, load behavior, or all payload sizes are proven |
| Validation is fresh | Final source edit timestamp or diff, rerun command/report, exit code, and not-run disclosures | Evidence was produced after the final relevant edit | Future edits or untested routes remain covered |

## Graph, Memory, And Execution Reconciliation

- Accept repository graph only when it includes handlers, middleware/auth extraction, validators, mappers, service boundaries, tests, specs, generated artifacts, and route registration after the final edit.
- Use project memory, old API docs, generated examples, previous reviews, and compaction summaries only as selectors; verify every accepted claim against current source, contract, and command output.
- Mark controller evidence stale after edits to route registration, middleware, auth context, validators, DTOs, error catalog, mappers, service signatures, generated files, examples, tests, or validation reports.
- Record skipped boundaries explicitly: alternate routes, jobs, internal RPC, admin/support tools, generated clients, gateway transformations, logs, telemetry, and unknown consumers.
- Map final confidence to current artifacts: source path, graph result, spec path, generated diff, test command, validator report, fixture, owner review, or explicit residual risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Source reads, route graph search, registry search, same-pattern scan, and report inspection | Read-only local shell action; cite paths/patterns and avoid large raw output dumps |
| Local validators, unit/contract/security tests, generated diff, and synthetic invalid payload fixtures | State-mutating only for reports, caches, temp fixtures, or generated artifacts; cite command, exit code, artifact path, sandbox, and cleanup |
| API sandbox request, gateway test, telemetry query, or production-like fixture replay | Data-reading or network-sensitive action; record target, dataset, timeout, redaction, owner, and no-secret handling |
| Deploy, rollback, gateway config, IAM/auth policy, or secret-bearing operation | High-risk write/release action; require explicit permission, dry-run when available, rollback or forward-fix path, owner, and redaction rule |

## Handoff Evidence Shape

```yaml
controller_evidence_closure:
  inspected_boundaries:
    - boundary: ""
      source_or_artifact: ""
      finding: ""
  accepted_graph_memory_execution_claims:
    - claim: ""
      current_evidence: ""
      freshness: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  controller_to_validation_map:
    - responsibility: ""
      proof: ""
      command_or_artifact: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      owner: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  residual_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
