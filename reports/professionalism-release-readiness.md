# Professionalism Release Readiness

- Generated: 2026-06-26T23:38:46.654490+00:00
- Status: strict-release-ready
- Authoring ready: ready
- Release ready: ready
- Strict release ready: ready
- Release-blocking professionalism warnings: 0
- Release review required warnings: 0
- Release review decision: accepted
- Release review reason: No release-review-required warnings are present.
- Regression status: pass
- Default regression status: pass
- Strict regression status: pass
- Promoted agent samples strict status: pass

## Professional Skill Coverage Summary

- Count: 21; Statuses: sample-grade: 21

## Key Foundation Capability Coverage Summary

- Count: 40; Statuses: acceptable: 1, sample-grade: 39

## Release Checklist

| Checklist Item | Status | Evidence Source | Blocking? | Notes |
| --- | --- | --- | --- | --- |
| default regression | pass | `reports/professionalism-regression-report.json` | true | status=pass |
| strict regression | pass | `internal strict comparison equivalent to python3 scripts/validate-professionalism-regression.py --strict` | true | blockers=0 |
| professional benchmarks | pass | `reports/professional-benchmarks-report.json` | true | errors=0; quality_failures=0; empty_baseline_cases=0 |
| routing coverage | pass | `reports/professional-routing-coverage.json` | true | needs_manual_review=0 |
| promoted agent samples strict | pass | `reports/professional-agent-samples-report.json from python3 scripts/eval-professional-agent-samples.py --promoted-only --strict` | true | returncode=0; failures=0 |
| content bloat exceptions | pass | `config/skill-content-exceptions.yaml and reports/skill-content-audit.json` | true | - classifications: {'KEEP_AS_IS': 156}; - domain_extensions: 7; - foundation_capabilities: 128; - heavy_domain: 0; - heavy_foundation: 0; - heavy_professional: 0; - low_professionalism: 0; - move_to_reference: 0; - professional_skills: 21; - split_candidates: 0 |
| known warnings budget | pass | `config/professionalism-baseline.yaml global_thresholds.max_known_warnings` | true | budget_blockers=0 |
| baseline update drift | pass | `reports/professionalism-regression-report.json baseline_changes` | false | baseline_changes=0 |

## Benchmark Coverage Summary

- cases_checked: 30
- comparison_cases_checked: 30
- empty_baseline_cases: 0
- quality_failures: 0

## Routing Coverage Summary

- cases_checked: 123
- cases_without_forbidden: 0
- hidden_risks_checked: 91
- hidden_risks_needing_manual_review: 0
- hidden_risks_strongly_covered: 87
- l1_anti_over_routing_count: 10

## Known Accepted Warnings

- None

## Skill Professionalism Warning Reconciliation

- accepted_known_warnings: 0
- enhanced_foundation_review_warnings: 0
- key_foundation_follow_up_warnings: 0
- new_unaccepted_release_warnings: 0
- non_key_foundation_advisory_warnings: 0
- policy: Professional skill warnings block release. Enhanced foundation warnings require release review. Key foundation warnings are follow-up unless evidence or reference precision is weak. Non-key foundation warnings are advisory-only.
- release_blocking_warnings: 0
- release_review_required_warnings: 0
- total_skill_professionalism_warnings: 0
- tracked_release_warnings: 0

| Warning | Scope | Release Relevance | Reason | Follow-up |
| --- | --- | --- | --- | --- |
| None | - | - | - | - |

## Release Review Decisions

- accepted_for_current_release: 0
- blocks_release: 0
- defer_to_followup: 0
- missing: 0
- stale: 0

- Decision: accepted
- Reason: No release-review-required warnings are present.
- Config: `config/professionalism-release-review.yaml`

| Target | Warning | Decision | Reason | Follow-up | Review After |
| --- | --- | --- | --- | --- | --- |
| None | - | - | - | - | - |

## Content Bloat Status

- heavy_domain: 0
- heavy_foundation: 0
- heavy_professional: 0
- low_professionalism: 0
- split_candidates: 0

## Required Validation Commands

- `python3 scripts/eval-skill-professionalism.py`
- `python3 scripts/eval-skill-professionalism.py --coverage-matrix`
- `python3 scripts/eval-professional-benchmarks.py`
- `python3 scripts/validate-professionalism-regression.py`
- `python3 scripts/validate-professionalism-regression.py --strict`
- `python3 scripts/validate-professional-routing-coverage.py`
- `python3 scripts/eval-professional-agent-samples.py`
- `python3 scripts/eval-professional-agent-samples.py --promoted-only --strict`

## Latest Results Available

- benchmark_errors: 0
- coverage_rows_checked: 61
- professional_agent_sample_warnings: 0
- professional_agent_samples_checked: 5
- promoted_agent_sample_strict_warnings: 0
- promoted_agent_samples_strict_checked: 5
- release_blocking_professionalism_warnings: 0
- skill_professionalism_average_score: 55.62
- skill_professionalism_warnings: 0

## Release Blockers

- None

## Non-Blocking Follow-Ups

- None
