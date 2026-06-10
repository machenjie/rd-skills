# Professionalism Release Checklist

## Required Validation Commands

Run before release:

```bash
python3 scripts/eval-skill-professionalism.py
python3 scripts/eval-skill-professionalism.py --coverage-matrix
python3 scripts/eval-professional-benchmarks.py
python3 scripts/validate-professionalism-regression.py
python3 scripts/validate-professional-routing-coverage.py
python3 scripts/eval-professional-agent-samples.py
python3 scripts/eval-professional-agent-samples.py --promoted-only --strict
```

Also run the repository validation/build suite listed in `AGENTS.md`.

## Blocking Conditions

- `validate-professionalism-regression.py` fails in default mode.
- `validate-professionalism-regression.py --strict` fails for release.
- benchmark schema, comparison, or quality status fails.
- professional routing coverage reports uncovered hidden risks.
- promoted professional agent samples fail under `--strict`.
- new content bloat warning appears without a recorded exception.
- a release readiness report status is `blocked`.

## Non-Blocking Warnings

- Existing baseline warnings may ship only when unchanged and visible in the regression report.
- Candidate professional samples may warn while under human review.
- Daily development may use `--report-only`; release may not rely on report-only status.

## Baseline Update Rules

- Update the baseline only after refreshing reports from the required commands.
- Baseline updates must show added, removed, or changed items in the regression report.
- Do not update the baseline to hide unexplained weak status, new warnings, or content bloat.
- `max_known_warnings_count` must not grow without a named review reason.

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

- `ready` means current reports have no blocking regression findings.
- `ready` does not mean every warning is fixed.
- `blocked` means release stops until the listed blockers are fixed or explicitly removed by a reviewed baseline update.

## What Not To Do

- Do not add keywords to raise scores.
- Do not add section-only fake professionalism.
- Do not turn every warning-only eval into a hard gate.
- Do not expand SKILL.md bodies to satisfy benchmarks.
- Do not add marketplace, catalog, persona, slash command, badge, MCP, plugin-market, or UI packaging work.
