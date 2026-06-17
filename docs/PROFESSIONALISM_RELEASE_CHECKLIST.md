# Professionalism Release Checklist

## Required Validation Commands

Run before release:

```bash
python3 scripts/eval-skill-professionalism.py
python3 scripts/eval-skill-professionalism.py --coverage-matrix
python3 scripts/eval-professional-benchmarks.py
python3 scripts/validate-professionalism-regression.py
python3 scripts/validate-professionalism-regression.py --strict
python3 scripts/validate-professional-routing-coverage.py
python3 scripts/eval-professional-agent-samples.py
python3 scripts/eval-professional-agent-samples.py --promoted-only --strict
```

`eval-skill-professionalism.py` writes the main professionalism eval and the key foundation
coverage matrix by default. `eval-skill-professionalism.py --coverage-matrix` writes only the
coverage matrix reports for compatibility with release checklists that call it separately.

Also run the repository validation/build suite listed in `AGENTS.md`.

For productization releases, also run:

```bash
python3 scripts/validate-examples.py
python3 scripts/validate-productization-assets.py
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
python3 scripts/validate-runtime-reference-links.py
python3 scripts/validate-installation.py
python3 scripts/export-marketplace-index.py --profile recommended --out /tmp/recommended-marketplace-index.json
python3 scripts/export-marketplace-index.py --profile full --out /tmp/full-marketplace-index.json
python3 scripts/export-marketplace-index.py --profile dev --out /tmp/dev-marketplace-index.json
python3 scripts/validate-marketplace-index.py --profile recommended
python3 scripts/validate-marketplace-index.py --profile full
python3 scripts/validate-marketplace-index.py --profile dev
python3 scripts/generate-professional-scorecard.py --strict-profile-builds --out /tmp/professional-scorecard.md --json-out /tmp/professional-scorecard.json
python3 scripts/render-scorecard-dashboard.py --scorecard /tmp/professional-scorecard.json --out /tmp/scorecard-dashboard.md
python3 scripts/generate-public-benchmark-summary.py --out /tmp/public-benchmark-summary.md --json-out /tmp/public-benchmark-summary.json
python3 scripts/generate-examples-showcase.py --check --out docs/SHOWCASE.md
python3 scripts/generate-marketplace-catalog.py --profile recommended --check --out docs/MARKETPLACE_CATALOG.md
```

## Blocking Conditions

- `validate-professionalism-regression.py` fails in default mode.
- `validate-professionalism-regression.py --strict` fails for release.
- benchmark schema, comparison, or quality status fails.
- professional routing coverage reports uncovered hidden risks.
- promoted professional agent samples fail under `--strict`.
- new content bloat warning appears without a recorded exception.
- `reports/professionalism-release-readiness.json` has `release_ready: blocked`,
  `strict_release_ready: blocked`, or `status: ready-for-authoring / not-release-certified` for a
  release decision.

## Non-Blocking Warnings

- Existing baseline warnings may ship only when unchanged and visible in the regression report.
- Skill professionalism eval warnings outside baseline-tracked release rows are report-only unless
  promoted into the key coverage matrix or baseline release budget, and must be visible in release
  readiness as out-of-scope / non-key advisory warnings.
- Candidate professional samples may warn while under human review.
- Daily development may use `--report-only`; release may not rely on report-only status.

## Release Review Decision Rules

- `release-review-required` warnings must have a matching entry in `config/professionalism-release-review.yaml`.
- Missing or stale release review decisions block strict release.
- `accepted_for_current_release` must include reason, follow-up phase, and review_after.
- Review decisions must not delete or hide the underlying warning.
- Do not update the baseline to silence release-review-required warnings without a release review decision.

## Baseline Update Rules

- Update the baseline only after refreshing reports from the required commands.
- Baseline updates must show added, removed, or changed items in the regression report.
- Do not update the baseline to hide unexplained weak status, new warnings, or content bloat.
- Every known warning entry must include `owner`, `accepted_reason`, `review_after`,
  `target_fix_phase`, and `is_release_blocking`.
- `global_thresholds.max_known_warnings` is typed by warning class. Professional skill warnings for
  missing `what evidence proves` and vague proactive trigger route/evidence are release-blocking by
  default and have budget `0` for strict release.

## Benchmark Promotion Rules

- Promote a benchmark only when the baseline output demonstrates a forbidden behavior.
- The with-skill output must cover selected stage, skill, capabilities, hidden risks, evidence, obligations, residual risk, and next gate.
- The delta must prove behavior improvement, not keyword stuffing.

## Agent Sample Promotion Rules

- Promote only human-reviewed samples with concrete actual output or route manifest.
- Required obligations, inspected boundaries, validation evidence, residual risk, and next gate must be present.
- Forbidden behaviors must be absent under `eval-professional-agent-samples.py --promoted-only --strict`.

## Content Bloat Exceptions

- Exceptions need a path, reason, owner, and review intent.
- Prefer moving long tables, examples, and anti-examples into references with loading hints.
- Do not copy Evidence Contract text across skills to raise scores.

## Routing Coverage Expectations

- High-risk benchmark hidden risks need at least one routing fixture.
- L1 fixtures must guard against over-routing.
- Routing cases should include `forbidden.*` unless there is a documented reason.

## Release Readiness Interpretation

- `authoring_ready: ready` means the default regression check passed for authoring work.
- `release_ready: ready` requires the strict regression result and promoted-agent-sample strict
  result to be present and passing.
- `strict_release_ready: ready` means the strict release gates passed with no release blockers.
- `ready-for-authoring / not-release-certified` means authoring may continue, but release is not
  certified.
- `blocked` means release stops until the listed blockers are fixed or explicitly removed by a
  reviewed baseline update.

`reports/professionalism-release-readiness.{md,json}` must include a checklist table with:

- default regression
- strict regression
- professional benchmarks
- routing coverage
- promoted agent samples strict
- content bloat exceptions
- known warnings budget
- baseline update drift

It must also include an out-of-scope / non-key skill eval warnings section that reconciles total
`skill-professionalism-eval` warnings against tracked release warnings and report-only advisory
warnings.

## What Not To Do

- Do not add keywords to raise scores.
- Do not add section-only fake professionalism.
- Do not turn every warning-only eval into a hard gate.
- Do not expand SKILL.md bodies to satisfy benchmarks.
- Do not add marketplace publishing, persona, slash command, badge, MCP, plugin-market, or UI packaging work that changes runtime packaging, duplicates registry truth, or creates a user-specific toolbox. A source-derived JSON discovery index and source-derived human catalog are allowed only when generated from registries/frontmatter and validated.
