# Benchmarks

ChangeForge benchmarks are release evidence, not marketing claims. They are local, deterministic, and based on repository fixtures, registries, generated reports, and build manifests. Missing data must remain `unknown` or `not_collected`.

## What Is Measured

| Area | Evidence Source | Command |
| --- | --- | --- |
| Routing correctness | Routing fixtures and expected outputs. | `python3 scripts/eval-routing.py` |
| Professional skill coverage | Professionalism eval report. | `python3 scripts/eval-skill-professionalism.py` |
| Foundation capability coverage | Coverage matrix report. | `python3 scripts/eval-skill-professionalism.py --coverage-matrix` |
| Reference loading precision | Runtime reference links and build manifests. | `python3 scripts/validate-runtime-reference-links.py` |
| Hook validation | Hook runtime validators and tests. | `python3 scripts/validate-hooks.py` |
| Profile build reproducibility | Build manifests for `recommended`, `full`, and `dev`. | `python3 scripts/build.py --profile recommended && python3 scripts/build.py --profile full && python3 scripts/build.py --profile dev` |
| Installation validation | Installer/doctor validation. | `python3 scripts/validate-installation.py` |
| Skill efficacy structural fixtures | evals/skill-efficacy | `python3 scripts/validate-skill-efficacy-benchmarks.py` |
| Executor adapter structural fixtures | Deterministic adapter fixtures and sanitized telemetry sample under `evals/executor-adapter` and `reports/`. | `python3 scripts/eval-executor-adapters.py` |
| Activation precision benchmark | Deterministic activation fixtures for stage, skill, capability, reference, language, risk, and overroute precision against the built hook runtime. | `python3 scripts/eval-activation-precision.py --mode built --runtime-root dist/codex/project/.codex/hooks` |
| Codegen benchmark smoke | Codegen benchmark manifest and limited run. | `python3 scripts/validate-codegen-benchmarks.py` and `python3 scripts/run-codegen-benchmarks.py --limit 3` |
| Professionalism regression | Baseline-aware regression check. | `python3 scripts/validate-professionalism-regression.py --strict` |

## Scorecard Generation

Generate a public scorecard from the local evidence already present in `reports/` and `dist/`:

```bash
python3 scripts/generate-professional-scorecard.py --out reports/professional-scorecard.md --json-out reports/professional-scorecard.json
```

Render the reader-facing dashboard from the scorecard JSON:

```bash
python3 scripts/render-scorecard-dashboard.py --scorecard reports/professional-scorecard.json --out docs/SCORECARD_DASHBOARD.md --readme README.md
```

Generate the public benchmark summary snapshot:

```bash
python3 scripts/generate-public-benchmark-summary.py --out reports/public-benchmark-summary.md --json-out reports/public-benchmark-summary.json
```

Committed public benchmark snapshots do not embed the current Git HEAD. Release
artifacts or CI jobs that need exact provenance can provide it explicitly:

```bash
python3 scripts/generate-public-benchmark-summary.py --source-commit "$GITHUB_SHA" --out reports/public-benchmark-summary.md --json-out reports/public-benchmark-summary.json
```

The generator does not mark a validator as passed just because a command name exists. If a tool does not emit a machine-readable report, that status is reported as `not_collected` and the verification command is listed.

Skill efficacy benchmarks are currently structural/local evidence. The current
fixtures validate routing and evidence shape; they do not provide live pass-rate
evidence, empirical before/after agent performance, or measured token/turn
overhead.

Executor adapter benchmarks are also structural/local evidence. They validate
canonical event recognition, adapter degradation, privacy redaction, validation
freshness, and closure effects across supported executor runtimes. The generated
runtime telemetry fixture sample is bounded and sanitized, but it is not live
runtime telemetry; live runtime telemetry, live pass-rate, token overhead, and
turn overhead remain `not_collected` unless separately measured or collected.

## Recommended Evidence Refresh

Before publishing a scorecard, refresh the relevant evidence:

```bash
python3 scripts/eval-routing.py
python3 scripts/eval-skill-professionalism.py
python3 scripts/eval-skill-professionalism.py --coverage-matrix
python3 scripts/eval-professional-benchmarks.py
python3 scripts/validate-skill-efficacy-benchmarks.py
python3 scripts/eval-executor-adapters.py
python3 scripts/eval-activation-precision.py --mode built --runtime-root dist/codex/project/.codex/hooks
python3 scripts/validate-professionalism-regression.py --strict
python3 scripts/validate-professional-routing-coverage.py
python3 scripts/eval-professional-agent-samples.py --promoted-only --strict
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
python3 scripts/validate-runtime-reference-links.py
python3 scripts/validate-installation.py
python3 scripts/validate-marketplace-index.py --profile recommended
python3 scripts/validate-marketplace-index.py --profile full
python3 scripts/validate-marketplace-index.py --profile dev
python3 scripts/generate-professional-scorecard.py --out reports/professional-scorecard.md --json-out reports/professional-scorecard.json
python3 scripts/render-scorecard-dashboard.py --scorecard reports/professional-scorecard.json --out docs/SCORECARD_DASHBOARD.md --readme README.md
python3 scripts/generate-public-benchmark-summary.py --out reports/public-benchmark-summary.md --json-out reports/public-benchmark-summary.json
```

Longer comparisons such as `python3 scripts/eval-routing.py --candidate-output-dir evals/routing-outputs` should be run when maintaining captured router outputs, not as a default PR blocker.

## Report Policy

`reports/` contains release snapshots that document local evidence. Regenerate them before release decisions and include the generation command in handoff notes. Do not edit scorecard or public benchmark numbers by hand.

Ordinary CI freshness checks are limited to stable generated documentation whose inputs are refreshed during the productization smoke step:

- `docs/SHOWCASE.md`
- `docs/MARKETPLACE_CATALOG.md`

Release snapshot artifacts are committed for reader context but are not guaranteed to be refreshed on every pull request:

- `reports/public-benchmark-summary.md`
- `reports/public-benchmark-summary.json`
- `reports/professional-scorecard.md`
- `reports/professional-scorecard.json`
- `docs/SCORECARD_DASHBOARD.md`
- the README scorecard summary block generated from `reports/professional-scorecard.json`
- `reports/executor-adapter-eval.md`
- `reports/executor-adapter-eval.json`
- `reports/activation-precision.md`
- `reports/activation-precision.json`
- `reports/runtime-telemetry-sample.json`

When updating release snapshots, refresh executor adapter and activation precision evidence, rebuild all three profiles, refresh the scorecard, render the dashboard and README block, then regenerate the public benchmark summary. The public benchmark summary reuses scorecard dimensions for marketplace, activation precision, and executor adapter status so those artifacts do not disagree about generated evidence.

See [SCORECARD.md](SCORECARD.md) and [SCORECARD_DASHBOARD.md](SCORECARD_DASHBOARD.md) for the reader-facing scorecard interpretation.
