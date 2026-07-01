# Codex Live Benchmark P0/P1 Fix Notes

This note records the evidence reviewed before changing benchmark, process-trace,
and hook guidance. It is not replacement benchmark evidence and does not refresh
`reports/codex-live-benchmark-summary.*`.

## Source Evidence Reviewed

- Canonical live summary: `reports/codex-live-benchmark-summary.json` and `.md`
  for run `ablation-core-auth-borrowed-20260701-013224`.
- Public summaries and benchmark docs: `reports/public-benchmark-summary.*` and
  `docs/BENCHMARKS.md`.
- Live registry and capability matrix: `evals/codex-live/cases.yaml` and
  `evals/codex-live/capability-matrix.yaml`.
- Live runner/report/validator code: `scripts/run-codex-live-benchmarks.py`,
  `scripts/generate-codex-live-summary.py`,
  `scripts/validate-codex-live-benchmark-reports.py`,
  `scripts/codex_live_benchmark_lib.py`, and
  `scripts/validate-process-traces.py`.
- Professional skill source: `development-process-orchestrator`,
  `change-forge-router`, `task-dag-planner`, `quality-test-gate`, and
  `ai-code-review-refactor`.
- Foundation capability source: `code-element-professionalism`,
  `domain-object-identification`, `design-pattern-selection`,
  `repository-graph-analysis`, `project-memory-governance`, and
  `validation-broker`.
- Hook runtime source: `changeforge-route-preflight.md`,
  `changeforge_runtime_route_resolver.py`, and
  `changeforge_user_prompt_route_reminder.py`.

## Current Live Evidence State

- Process traces collected: 144.
- PDD/DDD/TDD present rate: 1.0.
- SDD present rate: 0.7847.
- SDD degraded rate: 0.2153.
- Registered publishable assertion live cases: 23.
- Actual run publishable assertion live cases: 16.
- Registered-but-not-run publishable assertion cases:
  - `data-api/backward-compatible-api-field`
  - `data-middleware/kafka-consumer-offset-dlq`
  - `devex/bugfix-same-pattern-scan`
  - `frontend/accessible-form-error-state`
  - `integration/webhook-hmac-raw-body`
  - `performance/event-loop-blocking-async-path`
  - `performance/lock-held-across-io`

## Strict Process Trace Failures

The strict failures are concentrated in SDD design-choice evidence, not in
PDD, DDD, or TDD presence.

Observed failing patterns:

- Missing required decision-point fields:
  - `SDD.design_decision_points[*].id must be non-empty`
  - `SDD.design_decision_points[*].trigger must be non-empty`
  - `SDD.design_decision_points[*].decision must be non-empty`
  - `SDD.design_decision_points[*].user_choice_status must be one of ...`
  - `SDD.design_decision_points[*].why_user_choice_is_needed must be non-empty`
- Invalid or incomplete choice-gate fields:
  - `blocking` missing or not a boolean.
  - `options` missing, empty, or too short for required/blocking choices.
  - `recommended_option` missing for material choices.
  - `resolution_evidence` missing for `resolved` choices.
- Weak no-choice rationale:
  - material triggers such as public API, adapter, cache, migration, rollback,
    abstraction, permission, auth, and security appear in SDD facts.
  - the rationale says no choice was required but does not cite prompt,
    fixture, explicit user instruction, repository convention, existing code
    pattern, or reuse evidence.

Representative affected live cases include:

- `injection/professional-route-manifest-activation`
- `injection/stage-specific-reference-loading`
- `repo-intel/caller-callee-test-impact-map`
- `process/full-pdd-ddd-sdd-tdd-review-repair`
- `validation/stale-validation-after-edit`
- `devex/minimal-correct-native-reuse`
- `pressure/professional-boundary-under-user-pressure`
- `review/repair-rereview-required`
- `logging/redacted-structured-log-design`
- `compact/context-retention-after-compaction`

## Hook Regression Evidence

`structure/object-method-encapsulation-placement` is the only case where
`skills_with_hooks_clean` is below `skills_only_clean`:

- `skills_only_clean`: 1.0 pass rate.
- `skills_with_hooks_clean`: 0.6667 pass rate.
- Delta: -0.3333.

The failing hook run path is:

`reports/codex-live-runs/ablation-core-auth-borrowed-20260701-013224/cases/structure__object-method-encapsulation-placement/skills_with_hooks_clean/run-01`

Specific failure path:

- The grading assertion
  `test_object_method_decision_classifies_candidates` did not find
  `Object-Method Encapsulation Decision` or `object candidates` in candidate
  text.
- Hook guidance did not consistently force the object/method ownership decision
  into candidate-visible artifacts even though the prompt required an
  Implementation Structure Plan.
- A later hook run also had SDD degraded because its decision point lacked
  strict fields such as `trigger`, boolean `blocking`, `options`,
  `recommended_option`, and `why_user_choice_is_needed`.

Likely hook interference path:

- Current fixed UserPromptSubmit reminder is broad and route-oriented.
- Runtime route resolver currently emits a short `structure_focus` line, but it
  does not explicitly reject shared utility/helper drift, require object owner
  reuse first, or require candidate-visible object-method evidence when the
  prompt asks for it.
- This can allow structure/object tasks to drift toward generic implementation
  guidance instead of object-boundary cohesion and benchmark-visible evidence.

## Core Capability Coverage Partials

Current core capability status: 11 core capabilities, 2 pass, 9 partial.

Partial reasons from the canonical summary:

- `professional_injection_activation`: `skills_only_clean` strict process trace
  validation failed.
- `staged_injection_precision`: `skills_only_clean` strict process trace
  validation failed.
- `repository_graph_context_pack`: both `skills_only_clean` and
  `skills_with_hooks_clean` strict process trace validation failed.
- `validation_broker_freshness`: `skills_with_hooks_clean` strict process trace
  validation failed.
- `pdd_ddd_sdd_tdd_review_flow`: `skills_with_hooks_clean` strict process trace
  validation failed.
- `minimal_correct_implementation_ladder`: `skills_only_clean` strict process
  trace validation failed.
- `pua_or_pressure_resistance`: both `skills_only_clean` and
  `skills_with_hooks_clean` strict process trace validation failed.
- `execution_trajectory_review`: `skills_with_hooks_clean` strict process trace
  validation failed.
- `professional_logging_decision`: both `skills_only_clean` and
  `skills_with_hooks_clean` strict process trace validation failed.

Root cause across these partials: capability assertions are blocked by strict
process trace invalidity, especially SDD choice-gate evidence. No capability is
promoted from partial to pass by changing the summary; the fix must make future
live artifacts emit valid route/process evidence.

## Coverage Mechanism Gap

`scripts/run-codex-live-benchmarks.py` currently supports `--tier core`,
`--tier level1`, and `--tier experimental`, but not a clear
`--tier all` selector for all publishable assertion cases. Omitting `--tier`
selects all enabled cases, including the telemetry-only experimental case,
which is not the same as a full publishable assertion run.

The summary JSON already separates registered and actual run coverage fields,
but the markdown and report validator should make the distinction harder to
misread:

- manifest total cases
- registered live cases
- registered publishable assertion cases
- actual run cases
- actual run publishable assertion cases
- registered-but-not-run publishable assertion cases

## P2 Cost Boundary

Cost telemetry and caveats were inspected. This fix does not target token/cost
overhead, does not add a cost gate, and does not remove existing cost telemetry.
