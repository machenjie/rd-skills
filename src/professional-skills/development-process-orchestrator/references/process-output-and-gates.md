# Process Output And Gates

Load this reference when `development-process-orchestrator` needs the full output field list, detailed closure gate, or handoff routing table. Keep the main skill body compact.

## Output Contract

Return a compact process orchestration result with:

- **Mode selected**: compact code-change trace, missing process evidence repair, logging-sensitive trace, or coverage/reporting trace audit.
- **Boundaries inspected**: final.md, process-trace.json, hook telemetry, run.log, case metadata, prompt wrapper, validator output, reports, registry coverage, and skipped artifacts with reasons.
- **Evidence source map**: each PDD, DDD, SDD, and TDD field mapped to final trace, telemetry, explicit artifact, grading evidence, inferred fallback, or unavailable source.
- **Phase status**: `present`, `inferred`, `degraded`, `missing`, or `not_applicable` for PDD, DDD, SDD, and TDD.
- **PDD facts**: problem, impact, observable acceptance, constraints, non-goals, risk surfaces, validation signal, and behaviors preserved.
- **DDD facts**: domain terms, entities/value objects/services/adapters when relevant, ownership decision, invariants, side-effect boundaries, and existing code owner.
- **SDD facts**: modules/files, public API, data flow, error contract, failure modes, logging decision, metrics/traces/alerts, compatibility, rollback, recovery, and placement rationale.
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
2. `present` is used only for evidence-backed trace content, telemetry, explicit artifacts, or grading evidence.
3. Inferred metadata fallback is visible and cannot count as completed professional process evidence.
4. PDD acceptance maps to TDD tests or validation commands.
5. DDD invariants map to tests or code constraints.
6. SDD public API maps to tests or importable/public behavior evidence.
7. SDD failure modes map to failure tests or accepted residual risk.
8. Logging decisions map to log/security tests or explicit no-log rationale.
9. Generic process facts, booleans, and placeholder mappings are rejected.
10. Registered, dry-run, promoted, and actual live-run coverage are separated.
11. Validation evidence is fresh against the final trace and report artifacts.
12. Residual risk names owner and next gate.

## Handoff

- **quality-test-gate**: PDD acceptance, DDD invariants, SDD public API, failure modes, or validation commands do not map to tests.
- **logging-design-gate**: SDD logging is present but type, fields, redaction, correlation, cardinality, or tests are incomplete.
- **ai-code-review-refactor**: generated or agent-assisted traces may contain generic facts, hallucinated API names, or synthetic evidence.
- **change-documentation-gate**: benchmark summaries, release notes, or reports overstate actual run coverage.
- **delivery-release-gate**: release readiness depends on process trace, validation, rollback, or coverage evidence.
- **agent-execution-discipline**: completion is claimed without validation evidence, route/stage state, repair/re-review, or residual risk.
