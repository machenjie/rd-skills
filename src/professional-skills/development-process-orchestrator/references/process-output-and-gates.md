# Process Output And Gates

Load this reference when `development-process-orchestrator` needs the full output field list, detailed closure gate, or handoff routing table. Keep the main skill body compact.

## Output Contract

Return a compact process orchestration result with:

- **Mode selected**: compact code-change trace, missing process evidence repair, logging-sensitive trace, or coverage/reporting trace audit.
- **Boundaries inspected**: final.md, process-trace.json, hook telemetry, run.log, case metadata, prompt wrapper, validator output, reports, registry coverage, and skipped artifacts with reasons.
- **Evidence source map**: each PDD, DDD, SDD, and TDD field mapped to final trace, telemetry, explicit artifact, grading evidence, inferred fallback, or unavailable source.
- **Phase status**: `present`, `inferred`, `degraded`, `missing`, or `not_applicable` for PDD, DDD, SDD, and TDD.
- **Runtime phase ledger**: `process_phase_ledger` status, required phases,
  current phase, artifact digests, review IDs, unresolved material choices,
  validation signal, and adapter degradation. Store digests and bounded facts,
  not raw artifacts.
- **Phase review results**: one independent `phase_review_result` per required
  phase, with verdict, score, matching artifact digest, findings, approved
  scope, unreviewed areas, residual risk, and required next action.
- **Repair/re-review closure**: blocking phase findings mapped by `finding_id`
  to repair events and passing re-review events before closure.
- **PDD facts**: problem, impact, observable acceptance, constraints, non-goals, risk surfaces, validation signal, and behaviors preserved.
- **DDD facts**: domain terms, entities/value objects/services/adapters when relevant, ownership decision, invariants, side-effect boundaries, and existing code owner.
- **SDD facts**: modules/files, public API, data flow, error contract, failure modes, logging decision, design decision points, no-choice rationale when empty, assumption policy, metrics/traces/alerts, compatibility, rollback, recovery, and placement rationale.
- **TDD mappings**: acceptance-to-tests, invariant-to-tests-or-code, public-API-to-tests, failure-mode tests, logging/security tests, validation commands, and red/green/refactor trace when available.
- **Traceability matrix**: PDD fact -> DDD owner/invariant -> SDD file/API/logging decision -> TDD command or residual risk.
- **Generic-fact rejection**: process facts that were rejected as template, metadata-only, non-case-specific, private-helper-only, or boolean-without-mapping.
- **Logging decision status**: log/no-log rationale, type, placement, level, fields, redaction, correlation, cardinality controls, tests, and missing security review when relevant.
- **Coverage and benchmark status**: registered cases, promoted cases, dry-run cases, live-run cases, actual counts, skipped cases, and why registered coverage is not actual run evidence.
- **Validation evidence**: command, exit code, report path, freshness after final edit, what evidence proves, what it does not prove, and not-run disclosure.
- **Behavior preservation**: existing benchmark assertions, report semantics, validation command meaning, coverage semantics, and compatibility expectations preserved or intentionally changed.
- **Residual risk**: unsupported trace formatting, missing artifacts, inferred-only phases, logging/security gaps, stale validation, coverage overclaim risk, and owner.
- **Next gate/handoff**: quality, logging, report consistency, AI review, release, or no-next-gate rationale.

## Quality Gate

1. PDD, DDD, SDD, and TDD are populated with case-specific facts or marked unavailable.
2. Non-trivial engineering implementation is blocked unless PDD, DDD, SDD, and
   TDD are reviewed through independent passing phase review results or
   explicitly not applicable with reasons.
3. `present` is used only for evidence-backed trace content, telemetry, explicit artifacts, or grading evidence.
4. Inferred metadata fallback is visible and cannot count as completed professional process evidence.
5. PDD acceptance maps to TDD tests or validation commands.
6. DDD invariants map to tests or code constraints.
7. SDD public API maps to tests or importable/public behavior evidence.
8. SDD failure modes map to failure tests or accepted residual risk.
9. SDD design decision points are resolved, blocked before implementation, not required with concrete rationale, or safe-assumed only when local, reversible, conventional, and acceptance-neutral.
10. Logging decisions map to log/security tests or explicit no-log rationale.
11. Generic process facts, booleans, and placeholder mappings are rejected.
12. Registered, dry-run, promoted, and actual live-run coverage are separated.
13. Validation evidence is fresh against the final trace and report artifacts.
14. Residual risk names owner and next gate.

## Handoff

- **quality-test-gate**: PDD acceptance, DDD invariants, SDD public API, failure modes, or validation commands do not map to tests.
- **development-process-orchestrator**: SDD design choices are missing, generic, unresolved while blocking, or unsafe assumptions.
- **logging-design-gate**: SDD logging is present but type, fields, redaction, correlation, cardinality, or tests are incomplete.
- **ai-code-review-refactor**: generated or agent-assisted traces may contain generic facts, hallucinated API names, or synthetic evidence.
- **change-documentation-gate**: benchmark summaries, release notes, or reports overstate actual run coverage.
- **delivery-release-gate**: release readiness depends on process trace, validation, rollback, or coverage evidence.
- **agent-execution-discipline**: completion is claimed without validation evidence, route/stage state, repair/re-review, or residual risk.
