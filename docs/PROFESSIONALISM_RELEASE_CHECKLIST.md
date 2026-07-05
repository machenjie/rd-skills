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

`eval-skill-professionalism.py` writes the legacy mixed professionalism eval, the separated
100-point professionalism depth eval, and the key foundation coverage matrix by default.
`eval-skill-professionalism.py --coverage-matrix` writes only the coverage matrix reports for
compatibility with release checklists that call it separately.
The depth report is not advisory-only: `validate-professionalism-regression.py` and
`validate-professionalism-regression.py --strict` load `reports/skill-professionalism-depth.json`
and compare it against `config/professionalism-baseline.yaml`.

Also run the repository validation/build suite listed in `AGENTS.md`.

For productization releases, also run [Release Gate](VALIDATION.md#release-gate).
`docs/VALIDATION.md` owns the full local, profile build, runtime link,
installation, marketplace, generated snapshot, and smoke-check command set so
this checklist does not drift from the canonical release validation commands.

## Blocking Conditions

- `validate-professionalism-regression.py` fails in default mode.
- `validate-professionalism-regression.py --strict` fails for release.
- professional depth score, status, or core-dimension regression is detected.
- professional depth metadata references a missing standard or axis registry path.
- professional depth release-blocking warnings are present.
- benchmark schema, comparison, or quality status fails.
- professional routing coverage reports uncovered hidden risks.
- promoted professional agent samples fail under `--strict`.
- new content bloat warning appears without a recorded exception.
- depth `release-review-required` warnings lack accepted release review decisions.
- `reports/professionalism-release-readiness.json` has `release_ready: blocked`,
  `strict_release_ready: blocked`, or `status: ready-for-authoring / not-release-certified` for a
  release decision.

## Non-Blocking Warnings

- Existing baseline warnings may ship only when unchanged and visible in the regression report.
- Skill professionalism eval warnings outside baseline-tracked release rows are report-only unless
  promoted into the key coverage matrix or baseline release budget, and must be visible in release
  readiness as out-of-scope / non-key advisory warnings.
- Non-release-blocking depth warnings for non-key foundation capabilities may be tracked as
  follow-up, but key/enhanced foundation and domain-extension depth warnings require release review.
- A nonzero `TIGHTEN_BODY` count in `reports/skill-content-audit.json` is a content efficiency
  follow-up, not proof that efficiency is fixed by a passing content bloat exception gate.
- Candidate professional samples may warn while under human review.
- Daily development may use `--report-only`; release may not rely on report-only status.

## Release Review Decision Rules

- `release-review-required` warnings must have a matching entry in `config/professionalism-release-review.yaml`.
- Depth `release-review-required` warnings remain review-required even when already recorded in the
  baseline; the baseline does not replace explicit release review.
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

- Promote only human-reviewed samples with concrete actual output or route context.
- Required obligations, inspected boundaries, validation evidence, residual risk, and next gate must be present.
- Forbidden behaviors must be absent under `eval-professional-agent-samples.py --promoted-only --strict`.

## Content Bloat Exceptions

- Exceptions need a path, reason, owner, and review intent.
- Prefer moving long tables, examples, and anti-examples into references with loading hints.
- Do not copy Evidence Contract text across skills to raise scores.
- `TIGHTEN_BODY` items require owner follow-up or a documented tightening plan. Do not resolve them
  by adding more generic body paragraphs to raise professionalism scores.

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
- professional depth regression
- routing coverage
- promoted agent samples strict
- content bloat exceptions
- content efficiency follow-up
- known warnings budget
- baseline update drift

It must also include a professional depth summary with average score, status distribution, warning
count, score model path, and judgment axis registry. Latest results must include depth average,
depth warnings, release-blocking depth warnings, review-required depth warnings, needs-review depth
items, and weak/failing depth items.

It must also include an out-of-scope / non-key skill eval warnings section that reconciles total
`skill-professionalism-eval` warnings against tracked release warnings and report-only advisory
warnings, plus a professional depth warning reconciliation section that feeds the same release
review decision gate.

## What Not To Do

- Do not add keywords to raise scores.
- Do not add generic axis words to raise depth scores; item-specific judgment axes in
  `docs/skill_professionalism_standard/professionalism-axes.yaml` are the scoring target.
- Do not add section-only fake professionalism.
- Do not turn every warning-only eval into a hard gate.
- Do not expand SKILL.md bodies to satisfy benchmarks.
- Do not add marketplace publishing, persona, slash command, badge, MCP, plugin-market, or UI packaging work that changes runtime packaging, duplicates registry truth, or creates a user-specific toolbox. A source-derived JSON discovery index and source-derived human catalog are allowed only when generated from registries/frontmatter and validated.
