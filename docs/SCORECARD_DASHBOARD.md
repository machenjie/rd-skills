# Scorecard Dashboard

This generated dashboard makes conservative scorecard results easier to scan. Missing evidence remains `unknown` or `not_collected`; it is never rendered as pass.

## Status Summary

- `pass`: 16
- `partial`: 3
- `fail`: 0
- `unknown`: 0
- `not_collected`: 4

## Evidence Levels

| Evidence | Status | Meaning |
| --- | --- | --- |
| live pass-rate | `not_collected` | Measured real-task success rate. |
| live runtime telemetry sample | `not_collected` | Sanitized bounded facts from an actual hook runtime execution. |
| promoted golden case | `pass` | Human-reviewed case admitted to regression coverage. |
| runtime telemetry fixture sample | `pass` | Deterministic executor-adapter fixture-derived bounded facts; not live runtime telemetry. |
| structural fixture | `pass` | Local deterministic structure sample passed; not evidence of live task success. |
| token overhead | `not_collected` | Measured additional token cost. |
| turn overhead | `not_collected` | Measured additional turn cost. |

## Key Statuses

| Evidence | Status | Detail |
| --- | --- | --- |
| Profile build reproducibility | `pass` | {"dev": {"detail": "dev top-level count is 153", "manifest": "dist/universal/skills/dev/.changeforge-build-manifest.json", "status": "pass"}, "full": {"detail": "full top-level count is 26", "manifest": "dist/universal/skills/full/.changeforge-build-manifest.json", "status": "pass"}, "recommended": {"detail": "recommended top-level count is 19", "manifest": "dist/universal/skills/recommended/.changeforge-build-manifest.json", "status": "pass"}} |
| Open-source readiness | `partial` | config_present=True, selected_license_non_null=False, selected_license_allowed=True, license_file=False, pyproject_license_not_proprietary=False, contribution_licensing_confirmed=False, contribution_licensing_evidence=False, security_contact_confirmed=False, security_contact_evidence=False, dist_release_policy_explicit=True, dist_release_policy_valid=True |
| Example coverage | `pass` | showcase examples validate |
| Executor adapter structural fixtures | `pass` | {"case_count": 20, "coverage_targets": ["closure_verdict", "command_risk", "degradation", "event_recognition", "path_normalization", "permission_decision", "privacy_redaction", "tool_category", "validation_freshness_after_edits", "validation_outcome"], "evidence_boundary": "deterministic local fixtures only; no live runtime pass-rate or overhead measurement", "failed": 0, "live_pass_rate": "not_collected", "passed": 20, "pressure_cases": ["absolute_user_path", "claude_post_tool_failure", "codex_destructive_permission_request", "copilot_unsupported_pre_tool", "edit_after_validation", "failed_validation", "full_command_output_field", "large_path_list_cap", "ready_after_rereview", "ready_closure", "repair_without_rereview", "required_unsupported_check_degraded_ready", "review_finding_without_repair", "secret_like_payload_field", "targeted_test_reported_as_full", "unknown_event", "unsupported_runtime_event", "validation_pass_then_file_changed"], "token_overhead": "not_collected", "turn_overhead": "not_collected"} |
| Activation precision benchmark | `pass` | {"error_count": 0, "generated_by": "scripts/eval-activation-precision.py", "summary": {"capability_precision": 1.0, "capability_recall": 1.0, "case_count": 24, "failed": 0, "language_fn_rate": 0.0, "language_fp_rate": 0.0, "metric_definitions": {"language_fn_rate": "Share of cases with at least one missing expected language surface.", "language_fp_rate": "Share of cases with at least one unexpected language surface.", "overroute_rate": "Share of cases with any unexpected exact-set value or any forbidden *_not_contains value.", "precision_recall": "Set precision/recall aggregate true positives, false positives, and false negatives across exact-set cases.", "risk_surface_fn_rate": "Share of cases with at least one missing expected risk surface.", "risk_surface_fp_rate": "Share of cases with at least one unexpected risk surface."}, "overroute_rate": 0.0, "passed": 24, "reference_precision": 1.0, "reference_recall": 1.0, "risk_surface_fn_rate": 0.0, "risk_surface_fp_rate": 0.0, "skill_precision": 1.0, "skill_recall": 1.0, "stage_accuracy": 1.0}} |
| Runtime telemetry fixture sample | `pass` | {"degraded_event_count": 4, "event_count": 20, "evidence_level": "runtime telemetry fixture sample", "privacy_redaction_count": 9, "runtime": "mixed-fixture-runtime-sample", "sample_kind": "runtime_telemetry_fixture_sample", "source": "deterministic-fixture-bounded-facts", "token_overhead": "not_collected", "turn_overhead": "not_collected"} |
| Live runtime telemetry sample | `not_collected` | reports/live-runtime-telemetry-sample.json missing or invalid |
| Marketplace index validation | `pass` | recommended, full, and dev marketplace indexes validate |

## Profile Counts

- `dev`: `pass` - dev top-level count is 153
- `full`: `pass` - full top-level count is 26
- `recommended`: `pass` - recommended top-level count is 19

## Release-Only Evidence Not Collected

- Live runtime telemetry sample: reports/live-runtime-telemetry-sample.json
- Executor adapter live pass-rate: reports/executor-adapter-eval.json
- Executor adapter token overhead: reports/executor-adapter-eval.json
- Executor adapter turn overhead: reports/executor-adapter-eval.json

## Repair Hints

### High

- None

### Medium

- `partial` Professional skill coverage: Repair weak professional skill sections without keyword stuffing.
- `partial` Foundation capability coverage: Improve selected capability evidence contracts and references.
- `partial` Open-source readiness: Owner must select an OSI license, update package metadata, confirm contribution licensing, and configure private vulnerability reporting before open-source publication.

### Low

- `not_collected` Live runtime telemetry sample: Collect a real hook-runtime sample before changing this status from not_collected; do not use executor adapter fixtures for this dimension.
- `not_collected` Executor adapter live pass-rate: Collect a real measured run before changing this status from not_collected.
- `not_collected` Executor adapter token overhead: Collect a real measured run before changing this status from not_collected.
- `not_collected` Executor adapter turn overhead: Collect a real measured run before changing this status from not_collected.

## Refresh Commands

```bash
python3 scripts/validate-skills.py
python3 scripts/validate-capabilities.py
python3 scripts/validate-domain-extensions.py
python3 scripts/validate-registry.py
python3 scripts/validate-skill-body-links.py
python3 scripts/validate-skill-content-size.py
python3 scripts/validate-skill-efficacy-benchmarks.py
python3 scripts/eval-executor-adapters.py
python3 scripts/eval-activation-precision.py --mode built --runtime-root dist/codex/project/.codex/hooks
python3 scripts/audit-skill-content.py
python3 scripts/eval-routing.py
python3 scripts/eval-agent-behavior.py
python3 scripts/eval-skill-professionalism.py
python3 scripts/eval-skill-professionalism.py --coverage-matrix
python3 scripts/eval-professional-benchmarks.py
python3 scripts/validate-professionalism-regression.py
python3 scripts/validate-professionalism-regression.py --strict
python3 scripts/validate-professional-routing-coverage.py
python3 scripts/validate-stage-routing-architecture.py
python3 scripts/validate-hooks.py --json-out reports/hook-validation.json --out reports/hook-validation.md
python3 scripts/eval-pressure-behavior.py
python3 -m unittest discover -s tests
python3 scripts/validate-codegen-benchmarks.py
python3 scripts/run-codegen-benchmarks.py --limit 3
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
python3 scripts/validate-runtime-reference-links.py
python3 scripts/validate-installation.py --json-out reports/installation-validation.json --out reports/installation-validation.md
python3 scripts/validate-marketplace-index.py --profile recommended
python3 scripts/validate-marketplace-index.py --profile full
python3 scripts/validate-marketplace-index.py --profile dev
python3 scripts/validate-examples.py
python3 scripts/validate-productization-assets.py
python3 scripts/validate-open-source-readiness.py
python3 scripts/generate-public-benchmark-summary.py --check --out reports/public-benchmark-summary.md --json-out reports/public-benchmark-summary.json
python3 scripts/generate-examples-showcase.py --check --out docs/SHOWCASE.md
python3 scripts/generate-marketplace-catalog.py --profile recommended --check --out docs/MARKETPLACE_CATALOG.md
python3 scripts/render-scorecard-dashboard.py --scorecard reports/professional-scorecard.json --out docs/SCORECARD_DASHBOARD.md --readme README.md --check
python3 scripts/render-scorecard-dashboard.py --scorecard reports/professional-scorecard.json --out docs/SCORECARD_DASHBOARD.md --readme README.md
```
