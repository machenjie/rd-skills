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
| Codegen benchmark smoke | Codegen benchmark manifest and limited run. | `python3 scripts/validate-codegen-benchmarks.py` and `python3 scripts/run-codegen-benchmarks.py --limit 3` |
| Professionalism regression | Baseline-aware regression check. | `python3 scripts/validate-professionalism-regression.py --strict` |

## Scorecard Generation

Generate a public scorecard from the local evidence already present in `reports/` and `dist/`:

```bash
python3 scripts/generate-professional-scorecard.py --out reports/professional-scorecard.md --json-out reports/professional-scorecard.json
```

The generator does not mark a validator as passed just because a command name exists. If a tool does not emit a machine-readable report, that status is reported as `not_collected` and the verification command is listed.

## Recommended Evidence Refresh

Before publishing a scorecard, refresh the relevant evidence:

```bash
python3 scripts/eval-routing.py
python3 scripts/eval-skill-professionalism.py
python3 scripts/eval-skill-professionalism.py --coverage-matrix
python3 scripts/eval-professional-benchmarks.py
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
```

Longer comparisons such as `python3 scripts/eval-routing.py --candidate-output-dir evals/routing-outputs` should be run when maintaining captured router outputs, not as a default PR blocker.

## Report Policy

`reports/` contains sample/generated report snapshots that document local evidence. Regenerate them before release decisions and include the generation command in handoff notes. Do not edit scorecard numbers by hand.

See [SCORECARD.md](SCORECARD.md) for the reader-facing scorecard interpretation.
