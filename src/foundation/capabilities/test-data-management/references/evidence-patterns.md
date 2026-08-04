# Test Data Management Evidence Patterns

Use this reference when test-data closure depends on fixture-to-validation mapping, cleanup proof, privacy or secret scan evidence, deterministic rerun proof, parallel-safety proof, stale fixture memory, or proof limits. Keep it as an evidence map, not another fixture strategy catalog.

## Test Data Surface-To-Validation Map

| Test-data claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Fixture or factory is owned | Fixture/factory path, consumer tests, asserted fields, default/trait rule, and update/deletion owner | Inspected data artifact has a bounded owner and purpose | Future schema or hidden consumers are covered |
| Persistent side effects are isolated | Side-effect inventory, namespace/transaction/container strategy, cleanup command, and parallel-safety review | Inspected DB/cache/file/queue/email/sandbox state has a reset path | All CI shards, external sandboxes, or delayed jobs are clean |
| Data is privacy-safe | Data category, synthetic/sanitized rule, secret/PII scan or manual review, and retention owner | Inspected fixtures avoid selected sensitive patterns | Every real-world identifier, free-text leak, or historic artifact is absent |
| Determinism is controlled | Clock/random/UUID/locale/timezone/order control, seed, rerun command, and failure signature | Inspected tests can reproduce named generated values | Every asynchronous or environment-specific flake is solved |
| Volume/parallel data is partitioned | Worker/VU namespace, dataset slice rule, collision check, cleanup/retention, and quota note | Inspected parallel or load data avoids named collisions | Production scale, all quotas, or long-term retention are proven |
| Prior fixture evidence is fresh | Current schema/fixture/test/CI paths, accepted/rejected memory, validator/report, and final-edit freshness | Reused test-data pattern still matches inspected source | Later schema, runner, cleanup, or sandbox edits remain covered |

## Evidence Quality Labels

- **Strong evidence**: current tests/fixtures/factories/seeds/schema/cleanup/CI paths inspected, command or review artifact named, exit code or status recorded, final-edit freshness stated, and proof limits named.
- **Weak evidence**: prior green CI, global fixture convention, unscoped factory reuse, old memory, or cleanup review without side-effect inventory.
- **Missing evidence**: no fixture owner, no cleanup command, no privacy classification, no deterministic seed, no parallel-safety statement, or no owner for inaccessible sandbox state.
- **Invalid evidence**: real secret or PII in fixture, global destructive cleanup in shared environment without guard, unseeded asserted randomness, or stale fixture memory accepted as current proof.

## Tool Permission Boundary

- Truncate, drop, flush, purge, and external sandbox reset actions require an isolated namespace, dry-run or staging proof, stop condition, and restore or reseed path.
- Production-like exports and regulated-data scans require an approved source, minimization and redaction rules, retention/deletion evidence, and proof that parallel tests cannot cross namespaces.

## Handoff Evidence Shape

```yaml
test_data_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  test_data_surface_to_validation_map:
    - surface: ""
      risk: ownership | cleanup | privacy | determinism | parallel | freshness
      validator_or_artifact: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      owner: ""
  tool_permission_boundary:
    action_class: ""
    state_mutation: ""
    redaction: ""
  residual_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
