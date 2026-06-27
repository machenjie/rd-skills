# Input Validation Evidence Patterns

Use this reference when input-validation closure depends on repository graph, project memory, execution trajectory, validation freshness, tool permission boundaries, or production evidence limits. Keep it as an evidence map, not a second validation tutorial.

# Changed-Validation-To-Test Map

| Validation claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Boundary is server-enforced | Current route/handler, schema or validator path, direct-call negative test, and client-only path rejected | Inspected caller cannot bypass validation through the named server boundary | Every alternate route, job, import, or partner path is covered |
| Unknown fields are safe | Unknown-field policy, allowlisted mapper, raw binding search, and denied extra-field case | The inspected payload cannot mass-assign unmapped fields | Future DTO fields or generated clients remain compatible |
| Canonicalization happens before checks | Decode/parse/normalize/resolve sequence plus encoded or Unicode/path/URL fixture | The inspected rule evaluates the canonical representation | Every parser library edge case or locale behavior is proven |
| Identifier authority is validated | Trusted subject/tenant source, ownership or visibility query, lifecycle check, and wrong-owner/tenant test | The inspected identifier cannot act as caller-supplied authority | All authorization policy decisions are complete |
| URL/path/fetch input fails closed | Destination or grammar allowlist, private/metadata denial, redirect revalidation, bounds, and redacted error/log sample | The inspected selector rejects obvious SSRF/traversal/open redirect paths before use | Full web exploit coverage or network topology safety is proven |
| File/import intake is bounded | Size limit, magic-byte or structure check, archive traversal case, scan/publish state, and tenant binding | The inspected intake rejects representative unsafe files or records | Malware detection quality or all decompression-bomb variants are proven |
| Webhook/event payload is trusted before use | Raw-body signature, timestamp/replay check, schema version, idempotency key, and tamper/replay tests | The inspected event path verifies authenticity and freshness before side effects | Partner availability, all provider schema variants, or operational retries are proven |
| Error contract is non-leaking | Stable code/type, safe field path, rejected-value echo policy, log redaction assertion, and trace id | The inspected invalid input is actionable without exposing sensitive internals | Every localization, SDK, support, or log sink behavior is safe |
| Compatibility is preserved or staged | Old/new rule diff, old-valid fixture replay, generated-client or consumer check, rollout/rollback note | The inspected clients or fixtures keep expected behavior or have a migration path | Unknown deployed clients or production payload diversity are covered |

# Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, generated docs, old incident notes, prior validation reports, and execution trajectory as discovery inputs until current source and validator evidence confirm them.
- Accept a prior "validation exists", "generated schema enforces this", "frontend prevents it", "webhook is signed", or "unknown fields are ignored" claim only when current routes, validators, mappers, generated artifacts, tests, and reports still match.
- Mark evidence stale after edits to routes, DTOs, validators, parsers, mappers, auth context, schemas/specs, generated clients, fixtures, reports, build outputs, error catalogs, or validation commands.
- Record inspected and skipped boundaries: HTTP body/query/path/header/cookie, file/upload/import, webhook/event/queue, CLI/config/env, server-side fetch/path/template/query/AI/tool selectors, generated clients, tests, logs, and telemetry.
- Map every final validation confidence claim to a current command, test, validator, report, fixture, source path, owner approval, or explicit not-verified residual risk.

# Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, repository graph search, report inspection, and markdown validation | Read-only local shell action; cite searched paths and avoid full output dumps |
| Local validators, tests, builds, generated-client checks, and synthetic malicious fixtures | State-mutating only for reports, caches, temp files, dist/build artifacts, or local test fixtures; cite log path, command, exit code, and cleanup |
| Local parser/fetch/file/webhook proof command | Potentially data-reading or network-sensitive test action; record dataset, network target, sandbox, timeout, cleanup, and absence of production credentials |
| Production payload sample, telemetry export, security scanner, connector write, deploy, or rollback action | High-risk or connector-scoped action; require permission, dry-run when available, stop condition, rollback/forward-fix path, owner, and redaction rule |

# Handoff Evidence Shape

```yaml
input_validation_evidence_closure:
  inspected_boundaries:
    - boundary: ""
      current_source: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_validation_to_test_map:
    - validation_decision: ""
      source_path_or_artifact: ""
      validator_or_test: ""
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
  residual_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
