# Professional Benchmarks Evaluation

- Generated: 2026-06-09T22:18:52.483667+00:00
- Mode: auto
- Cases checked: 10
- Comparison cases checked: 10
- Errors: 0
- Actual output comparison: deterministic rule heuristic; auto mode compares baseline_output.md and with_skill_output.md when both exist
- Comparison note: this is a deterministic rule heuristic; it cannot replace human review or a real agent eval.

| Case | Schema Status | Comparison Status | Stage | Skills | Missing Expected Items | Forbidden Behavior Hits | Professional Delta Summary | Errors |
| --- | --- | --- | --- | --- | ---: | ---: | --- | ---: |
| `evals/professional-benchmarks/ai-review/generated-code-invented-helper-without-reuse-search` | pass | pass | `code-review` | ai-code-review-refactor | 0 | 0 | baseline_missing: 9; with_skill_present: 10; remaining_gaps: 0; forbidden_behavior_hits: 0; delta_score: +9 | 0 |
| `evals/professional-benchmarks/backend/idor-local-fix-without-same-pattern-scan` | pass | pass | `bug-fix` | backend-change-builder | 0 | 0 | baseline_missing: 9; with_skill_present: 10; remaining_gaps: 0; forbidden_behavior_hits: 0; delta_score: +9 | 0 |
| `evals/professional-benchmarks/backend/partial-success-without-transaction` | pass | pass | `implementation-planning` | backend-change-builder | 0 | 0 | baseline_missing: 9; with_skill_present: 10; remaining_gaps: 0; forbidden_behavior_hits: 0; delta_score: +9 | 0 |
| `evals/professional-benchmarks/backend/queue-consumer-missing-idempotency` | pass | pass | `code-review` | backend-change-builder | 0 | 0 | baseline_missing: 9; with_skill_present: 10; remaining_gaps: 0; forbidden_behavior_hits: 0; delta_score: +9 | 0 |
| `evals/professional-benchmarks/data/redis-cache-without-ttl-or-invalidation` | pass | pass | `implementation-planning` | data-middleware-change-builder | 0 | 0 | baseline_missing: 9; with_skill_present: 10; remaining_gaps: 0; forbidden_behavior_hits: 0; delta_score: +9 | 0 |
| `evals/professional-benchmarks/debugging/retry-same-failed-approach` | pass | pass | `debugging-diagnosis` | delivery-release-gate | 0 | 0 | baseline_missing: 10; with_skill_present: 10; remaining_gaps: 0; forbidden_behavior_hits: 0; delta_score: +10 | 0 |
| `evals/professional-benchmarks/frontend/form-validation-without-accessibility-states` | pass | pass | `coding` | frontend-change-builder | 0 | 0 | baseline_missing: 9; with_skill_present: 10; remaining_gaps: 0; forbidden_behavior_hits: 0; delta_score: +9 | 0 |
| `evals/professional-benchmarks/integration/webhook-without-signature-or-replay-protection` | pass | pass | `code-review` | integration-change-builder | 0 | 0 | baseline_missing: 9; with_skill_present: 10; remaining_gaps: 0; forbidden_behavior_hits: 0; delta_score: +9 | 0 |
| `evals/professional-benchmarks/refactoring/shared-utils-business-logic-pollution` | pass | pass | `refactoring` | ai-code-review-refactor | 0 | 0 | baseline_missing: 9; with_skill_present: 10; remaining_gaps: 0; forbidden_behavior_hits: 0; delta_score: +9 | 0 |
| `evals/professional-benchmarks/release/migration-without-rollback` | pass | pass | `release-delivery` | delivery-release-gate | 0 | 0 | baseline_missing: 9; with_skill_present: 10; remaining_gaps: 0; forbidden_behavior_hits: 0; delta_score: +9 | 0 |

## Benchmark Quality Details

| Case | Benchmark Quality Status | Baseline Defect Hits | With-Skill Obligation Coverage | Delta Score | Remaining Gaps |
| --- | --- | ---: | --- | ---: | ---: |
| `evals/professional-benchmarks/ai-review/generated-code-invented-helper-without-reuse-search` | pass | 1 | selected stage, selected professional skill, selected capabilities, expected hidden risks, forbidden behaviors avoided, expected evidence, expected output obligations, residual risk, next gate, validation command or not-verified disclosure | +9 | 0 |
| `evals/professional-benchmarks/backend/idor-local-fix-without-same-pattern-scan` | pass | 1 | selected stage, selected professional skill, selected capabilities, expected hidden risks, forbidden behaviors avoided, expected evidence, expected output obligations, residual risk, next gate, validation command or not-verified disclosure | +9 | 0 |
| `evals/professional-benchmarks/backend/partial-success-without-transaction` | pass | 1 | selected stage, selected professional skill, selected capabilities, expected hidden risks, forbidden behaviors avoided, expected evidence, expected output obligations, residual risk, next gate, validation command or not-verified disclosure | +9 | 0 |
| `evals/professional-benchmarks/backend/queue-consumer-missing-idempotency` | pass | 1 | selected stage, selected professional skill, selected capabilities, expected hidden risks, forbidden behaviors avoided, expected evidence, expected output obligations, residual risk, next gate, validation command or not-verified disclosure | +9 | 0 |
| `evals/professional-benchmarks/data/redis-cache-without-ttl-or-invalidation` | pass | 1 | selected stage, selected professional skill, selected capabilities, expected hidden risks, forbidden behaviors avoided, expected evidence, expected output obligations, residual risk, next gate, validation command or not-verified disclosure | +9 | 0 |
| `evals/professional-benchmarks/debugging/retry-same-failed-approach` | pass | 1 | selected stage, selected professional skill, selected capabilities, expected hidden risks, forbidden behaviors avoided, expected evidence, expected output obligations, residual risk, next gate, validation command or not-verified disclosure | +10 | 0 |
| `evals/professional-benchmarks/frontend/form-validation-without-accessibility-states` | pass | 1 | selected stage, selected professional skill, selected capabilities, expected hidden risks, forbidden behaviors avoided, expected evidence, expected output obligations, residual risk, next gate, validation command or not-verified disclosure | +9 | 0 |
| `evals/professional-benchmarks/integration/webhook-without-signature-or-replay-protection` | pass | 1 | selected stage, selected professional skill, selected capabilities, expected hidden risks, forbidden behaviors avoided, expected evidence, expected output obligations, residual risk, next gate, validation command or not-verified disclosure | +9 | 0 |
| `evals/professional-benchmarks/refactoring/shared-utils-business-logic-pollution` | pass | 1 | selected stage, selected professional skill, selected capabilities, expected hidden risks, forbidden behaviors avoided, expected evidence, expected output obligations, residual risk, next gate, validation command or not-verified disclosure | +9 | 0 |
| `evals/professional-benchmarks/release/migration-without-rollback` | pass | 1 | selected stage, selected professional skill, selected capabilities, expected hidden risks, forbidden behaviors avoided, expected evidence, expected output obligations, residual risk, next gate, validation command or not-verified disclosure | +9 | 0 |
