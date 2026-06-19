# Public Benchmark Summary

This generated summary reports local deterministic ChangeForge evidence. Skill efficacy and executor adapter fixtures are structural/local evidence, not live pass-rate or empirical before/after agent-performance proof. It does not claim external popularity, marketplace availability, or market adoption.

## Repository

- Repository: `machenjie/rd-skills`
- Version: `0.1.0`
- Source commit: `provided by release artifact / CI metadata`

## Status Counts

- `pass`: 12
- `partial`: 2
- `fail`: 0
- `unknown`: 0
- `not_collected`: 4

## Evidence Levels

| Evidence | Status | Meaning |
| --- | --- | --- |
| live pass-rate | `not_collected` | Measured real-task success rate. |
| promoted golden case | `pass` | Human-reviewed case admitted to regression coverage. |
| runtime telemetry sample | `pass` | Sanitized bounded runtime fact sample; may still require human review. |
| structural fixture | `pass` | Local deterministic structure sample passed; not evidence of live task success. |
| token overhead | `not_collected` | Measured additional token cost. |
| turn overhead | `not_collected` | Measured additional turn cost. |

## Evidence

| Area | Status | Evidence Level | Source | Detail | Refresh Command |
| --- | --- | --- | --- | --- | --- |
| Routing coverage | `pass` | structural fixture | reports/professionalism-release-readiness.json | {"cases_checked": 118, "cases_without_forbidden": 0, "hidden_risks_checked": 91, "hidden_risks_needing_manual_review": 0, "hidden_risks_strongly_covered": 87, "l1_anti_over_routing_count": 9} | `python3 scripts/validate-professional-routing-coverage.py` |
| Professional skill coverage | `partial` | structural fixture | reports/professionalism-release-readiness.json | {"count": 19, "statuses": {"sample-grade": 19}} | `python3 scripts/eval-skill-professionalism.py` |
| Foundation capability coverage | `partial` | structural fixture | reports/professionalism-release-readiness.json | {"count": 40, "statuses": {"acceptable": 29, "needs-review": 10, "sample-grade": 1}} | `python3 scripts/eval-skill-professionalism.py --coverage-matrix` |
| Strict regression | `pass` | promoted golden case | reports/professionalism-release-readiness.json | strict_regression_status=pass | `python3 scripts/validate-professionalism-regression.py --strict` |
| Skill professionalism report | `pass` | structural fixture | reports/skill-professionalism-eval.json | average_score=41.66 | `python3 scripts/eval-skill-professionalism.py` |
| Professional coverage matrix | `pass` | structural fixture | reports/professional-coverage-matrix.json | rows=59 | `python3 scripts/eval-skill-professionalism.py --coverage-matrix` |
| Profile build: recommended | `pass` | structural fixture | dist/universal/skills/recommended/.changeforge-build-manifest.json | top_level=19, expected=19 | `python3 scripts/build.py --profile recommended` |
| Profile build: full | `pass` | structural fixture | dist/universal/skills/full/.changeforge-build-manifest.json | top_level=26, expected=26 | `python3 scripts/build.py --profile full` |
| Profile build: dev | `pass` | structural fixture | dist/universal/skills/dev/.changeforge-build-manifest.json | top_level=153, expected=153 | `python3 scripts/build.py --profile dev` |
| Installation validation | `not_collected` | structural fixture | scripts/validate-installation.py | validator does not emit a committed machine-readable report | `python3 scripts/validate-installation.py` |
| Skill efficacy structural fixtures | `pass` | structural fixture | reports/professional-scorecard.json | {"candidate_fixtures_ignored": 0, "evidence_boundary": "structural/local fixtures only; no empirical before/after agent performance", "evidence_levels": {"live pass-rate": "not_collected", "promoted golden case": "not_collected", "runtime telemetry sample": "not_collected", "structural fixture": 3, "token overhead": "not_collected", "turn overhead": "not_collected"}, "fixtures": 3, "live_pass_rate": "not_collected", "token_overhead": "not_collected", "turn_overhead": "not_collected", "verdicts": {"structural_pass": 3}} | `python3 scripts/validate-skill-efficacy-benchmarks.py` |
| Runtime governance structural fixtures | `pass` | structural fixture | reports/professional-scorecard.json | {"candidate_fixtures_ignored": 0, "evidence_boundary": "structural/local fixtures only; no live empirical pass-rate or runtime overhead evidence", "evidence_levels": {"live pass-rate": "not_collected", "promoted golden case": "not_collected", "runtime telemetry sample": "not_collected", "structural fixture": 15, "token overhead": "not_collected", "turn overhead": "not_collected"}, "suites": {"executor-adapters": {"candidate_fixtures_ignored": 0, "fixtures": 3, "required_capability": "executor-adapter-protocol", "required_capability_hits": 3}, "project-memory": {"candidate_fixtures_ignored": 0, "fixtures": 3, "required_capability": "project-memory-governance", "required_capability_hits": 3}, "repository-intelligence": {"candidate_fixtures_ignored": 0, "fixtures": 3, "required_capability": "repository-graph-analysis", "required_capability_hits": 3}, "trajectory": {"candidate_fixtures_ignored": 0, "fixtures": 3, "required_capability": "execution-trajectory-analysis", "required_capability_hits": 3}, "validation-broker": {"candidate_fixtures_ignored": 0, "fixtures": 3, "required_capability": "validation-broker", "required_capability_hits": 3}}, "total_fixtures": 15} | `python3 scripts/validate-professional-routing-coverage.py` |
| Executor adapter structural fixtures | `pass` | structural fixture | reports/professional-scorecard.json | {"case_count": 15, "coverage_targets": ["closure_verdict", "command_risk", "degradation", "event_recognition", "path_normalization", "permission_decision", "privacy_redaction", "tool_category", "validation_freshness_after_edits", "validation_outcome"], "evidence_boundary": "deterministic local fixtures only; no live runtime pass-rate or overhead measurement", "failed": 0, "live_pass_rate": "not_collected", "passed": 15, "pressure_cases": ["absolute_user_path", "claude_post_tool_failure", "codex_destructive_permission_request", "copilot_unsupported_pre_tool", "edit_after_validation", "failed_validation", "full_command_output_field", "large_path_list_cap", "repair_without_rereview", "review_finding_without_repair", "secret_like_payload_field", "unknown_event", "unsupported_runtime_event"], "token_overhead": "not_collected", "turn_overhead": "not_collected"} | `python3 scripts/eval-executor-adapters.py` |
| Runtime telemetry sample | `pass` | runtime telemetry sample | reports/professional-scorecard.json | {"degraded_event_count": 4, "event_count": 15, "privacy_redaction_count": 9, "runtime": "mixed-fixture-runtime-sample", "source": "deterministic-fixture-bounded-facts", "token_overhead": "not_collected", "turn_overhead": "not_collected"} | `python3 scripts/eval-executor-adapters.py` |
| Executor adapter live pass-rate | `not_collected` | live pass-rate | reports/professional-scorecard.json | deterministic local fixtures do not measure real-task success rate | `python3 scripts/eval-executor-adapters.py` |
| Executor adapter token overhead | `not_collected` | token overhead | reports/professional-scorecard.json | deterministic local fixture run does not measure token overhead | `python3 scripts/eval-executor-adapters.py` |
| Executor adapter turn overhead | `not_collected` | turn overhead | reports/professional-scorecard.json | deterministic local fixture run does not measure turn overhead | `python3 scripts/eval-executor-adapters.py` |
| Marketplace index validation | `pass` | structural fixture | reports/professional-scorecard.json | recommended, full, and dev marketplace indexes validate | `python3 scripts/validate-marketplace-index.py --profile recommended && python3 scripts/validate-marketplace-index.py --profile full && python3 scripts/validate-marketplace-index.py --profile dev` |

## Known Unknowns / Not Collected

- Installation validation
- Executor adapter live pass-rate
- Executor adapter token overhead
- Executor adapter turn overhead

## Refresh Commands

```bash
python3 scripts/eval-routing.py
python3 scripts/eval-skill-professionalism.py
python3 scripts/eval-skill-professionalism.py --coverage-matrix
python3 scripts/eval-professional-benchmarks.py
python3 scripts/validate-skill-efficacy-benchmarks.py
python3 scripts/eval-executor-adapters.py
python3 scripts/validate-professionalism-regression.py --strict
python3 scripts/validate-professional-routing-coverage.py
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
python3 scripts/validate-runtime-reference-links.py
python3 scripts/validate-installation.py
python3 scripts/validate-marketplace-index.py --profile recommended
python3 scripts/validate-marketplace-index.py --profile full
python3 scripts/validate-marketplace-index.py --profile dev
python3 scripts/generate-public-benchmark-summary.py --out reports/public-benchmark-summary.md --json-out reports/public-benchmark-summary.json
```
