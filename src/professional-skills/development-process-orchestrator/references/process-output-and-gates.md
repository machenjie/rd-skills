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
  post-implementation validation status, and adapter degradation. Store digests
  and bounded facts, not raw artifacts.
- **Phase artifacts**: optional bounded `process_phase_artifact` entries with
  schema version, route ID, phase, artifact digest, artifact summary, source
  evidence, and traceability. PDD requires problem, impact, acceptance criteria,
  constraints, non-goals, and risk surfaces; DDD requires domain terms, objects,
  ownership, invariants, and side-effect boundaries; SDD requires files/modules,
  data flow, public API/no-public-API decision, failure contract, design decision
  points, logging, compatibility, and rollback; TDD requires acceptance-to-tests,
  invariant-to-tests, failure-mode tests, validation commands, and what tests do
  not prove. If no real artifact digest exists, the process phase gate must emit
  `phase_artifact_required_action`; create the `process_phase_artifact` before
  review.
- **Phase review results**: one independent `phase_review_result` per required
  phase, with verdict, score, artifact digest matching the current capsule or
  phase ledger, findings, approved scope, unreviewed areas, residual risk, and
  required next action. Strong phase review must include provenance
  (`review_source`, `capsule_id`, `expected_artifact_digest`,
  `review_context_strength`, and `reviewer_boundary`) from a subagent,
  parent-independent, or CI review gate. ClosureContract uses the same strong
  validator as `phase_review_passes(..., require_strong_source=True)`, so score
  below 4, same owner/reviewer skill, blocking findings, missing expected
  digest, empty approved scope, or digest mismatch cannot pass. Final handoff
  `phase_reviews` are weak disclosure only.
- **Implementation review results**: separate post-implementation review of the
  actual changed files and reviewed diff digest. This is not satisfied by PDD,
  DDD, SDD, or TDD review. Missing or weak implementation review emits
  `implementation_review_required_action`; reviewed files must cover all changed
  paths and include `reviewed_diff_digest`. Unrelated review targets cannot close
  implementation review, and final handoff prose cannot satisfy it.
- **Repair/re-review closure**: blocking phase findings mapped by `finding_id`
  to repair events and passing re-review events before closure.
- **PDD facts**: problem, impact, observable acceptance, constraints, non-goals, risk surfaces, validation signal, and behaviors preserved.
- **DDD facts**: domain terms, entities/value objects/services/adapters when relevant, ownership decision, invariants, side-effect boundaries, and existing code owner.
- **SDD facts**: modules/files, public API, data flow, error contract, failure modes, logging decision, design decision points, no-choice rationale when empty, assumption policy, metrics/traces/alerts, compatibility, rollback, recovery, and placement rationale.
- **TDD mappings**: acceptance-to-tests, invariant-to-tests-or-code, public-API-to-tests, failure-mode tests, logging/security tests, validation commands, and what tests do not prove. TDD review is a test design review; it is not proof that post-implementation validation already executed.
- **Traceability matrix**: PDD fact -> DDD owner/invariant -> SDD file/API/logging decision -> TDD command or residual risk.
- **Generic-fact rejection**: process facts that were rejected as template, metadata-only, non-case-specific, private-helper-only, or boolean-without-mapping.
- **Logging decision status**: log/no-log rationale, type, placement, level, fields, redaction, correlation, cardinality controls, tests, and missing security review when relevant.
- **Coverage and benchmark status**: registered cases, promoted cases, dry-run cases, live-run cases, actual counts, skipped cases, and why registered coverage is not actual run evidence.
- **Post-implementation validation evidence**: command, exit code, report path, freshness after final edit, what evidence proves, what it does not prove, and not-run disclosure. This belongs to closure/Stop audit, not the TDD phase-reviewed predicate.
- **Behavior preservation**: existing benchmark assertions, report semantics, validation command meaning, coverage semantics, and compatibility expectations preserved or intentionally changed. Timestamp-only report changes under `reports/*.json` or `reports/*.md` are not substantive report evidence and should not be submitted.
- **Residual risk**: unsupported trace formatting, missing artifacts, inferred-only phases, logging/security gaps, stale validation, coverage overclaim risk, and owner.
- **Next gate/handoff**: quality, logging, report consistency, AI review, release, or no-next-gate rationale.

## Quality Gate

1. PDD, DDD, SDD, and TDD are populated with case-specific facts or marked unavailable.
2. Non-trivial engineering implementation is blocked unless PDD, DDD, SDD, and
   TDD are reviewed through independent passing phase review results or
   explicitly not applicable with reasons.
   Passing phase review requires strong provenance and matching artifact digest;
   missing provenance or final handoff disclosure cannot advance the phase.
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
13. Validation evidence is fresh against the final trace and report artifacts; report diffs are not timestamp-only.
14. Residual risk names owner and next gate.
15. `tdd_plan_reviewed=true` can pass before implementation validation runs;
    Stop closure must then report `post_implementation_validation.status` as
    `not_run`, `partial`, or `unknown` with residual risk instead of claiming a
    full pass.
16. SDD material choices that block a phase require user/source choice evidence,
    a repair event tied to `sdd-material-choice`, and a passing re-review event
    before the blocker is resolved.
17. Stop hard blockers preserve closure-surface evidence; repeated advisory
    liveness degradation cannot resolve validation, security/privacy,
    destructive, phase/review, implementation-review, or material-choice
    blockers.

## Handoff

- **quality-test-gate**: PDD acceptance, DDD invariants, SDD public API, failure modes, or validation commands do not map to tests.
- **development-process-orchestrator**: SDD design choices are missing, generic, unresolved while blocking, or unsafe assumptions.
- **logging-design-gate**: SDD logging is present but type, fields, redaction, correlation, cardinality, or tests are incomplete.
- **ai-code-review-refactor**: generated or agent-assisted traces may contain generic facts, hallucinated API names, or synthetic evidence.
- **change-documentation-gate**: benchmark summaries, release notes, or reports overstate actual run coverage.
- **delivery-release-gate**: release readiness depends on process trace, validation, rollback, or coverage evidence.
- **agent-execution-discipline**: completion is claimed without validation evidence, route/stage state, repair/re-review, or residual risk.
