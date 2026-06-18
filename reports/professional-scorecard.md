# Professional Scorecard

This scorecard is generated from local registry, build, and report evidence. Missing machine-readable evidence is shown as `not_collected` or `unknown`, not as pass.

## Summary

- `pass`: 11
- `partial`: 3
- `fail`: 0
- `unknown`: 0
- `not_collected`: 2

## Evidence Levels

| Evidence | Status | Meaning |
| --- | --- | --- |
| structural fixture | `pass` | Local deterministic structure sample passed; not evidence of live task success. |
| runtime telemetry sample | `not_collected` | Actual runtime fact sample; may still require human review. |
| promoted golden case | `pass` | Human-reviewed case admitted to regression coverage. |
| live pass-rate | `not_collected` | Measured real-task success rate. |
| token overhead | `not_collected` | Measured additional token cost. |
| turn overhead | `not_collected` | Measured additional turn cost. |

## Dimensions

| Dimension | Status | Source | Verification |
| --- | --- | --- | --- |
| Registry source counts | `pass` | src/registry/*.yaml | `python3 scripts/validate-registry.py` |
| Profile build reproducibility | `pass` | dist/universal/skills/*/.changeforge-build-manifest.json | `python3 scripts/build.py --profile recommended && python3 scripts/build.py --profile full && python3 scripts/build.py --profile dev` |
| Routing coverage | `pass` | reports/professionalism-release-readiness.json | `python3 scripts/validate-professional-routing-coverage.py` |
| Professional skill coverage | `partial` | reports/professionalism-release-readiness.json | `python3 scripts/eval-skill-professionalism.py` |
| Foundation capability coverage | `partial` | reports/professionalism-release-readiness.json | `python3 scripts/eval-skill-professionalism.py --coverage-matrix` |
| Professional benchmarks | `pass` | reports/professionalism-release-readiness.json | `python3 scripts/eval-professional-benchmarks.py` |
| Professionalism regression | `pass` | reports/professionalism-release-readiness.json | `python3 scripts/validate-professionalism-regression.py --strict` |
| Promoted agent samples | `pass` | reports/professionalism-release-readiness.json | `python3 scripts/eval-professional-agent-samples.py --promoted-only --strict` |
| Skill efficacy structural fixtures | `pass` | evals/skill-efficacy and scripts/validate-skill-efficacy-benchmarks.py | `python3 scripts/validate-skill-efficacy-benchmarks.py` |
| Runtime governance structural fixtures | `pass` | evals/executor-adapters, evals/repository-intelligence, evals/project-memory, evals/validation-broker, evals/trajectory | `python3 scripts/validate-professional-routing-coverage.py` |
| Example coverage | `pass` | examples/ and scripts/validate-examples.py | `python3 scripts/validate-examples.py` |
| Productization assets | `pass` | docs/productization assets, schemas, and scripts | `python3 scripts/validate-productization-assets.py` |
| Marketplace index validation | `pass` | scripts/validate-marketplace-index.py | `python3 scripts/validate-marketplace-index.py --profile recommended && python3 scripts/validate-marketplace-index.py --profile full && python3 scripts/validate-marketplace-index.py --profile dev` |
| Open-source readiness | `partial` | config/open-source-release.yaml, docs/LICENSE_DECISION.md, docs/OPEN_SOURCE_READINESS.md, pyproject.toml, CONTRIBUTING.md, SECURITY.md, LICENSE | `python3 scripts/validate-open-source-readiness.py` |
| Hook safety | `not_collected` | scripts/validate-hooks.py does not emit a machine-readable report | `python3 scripts/validate-hooks.py` |
| Installation validation | `not_collected` | scripts/validate-installation.py does not emit a machine-readable report | `python3 scripts/validate-installation.py` |

## Profile Counts

- `recommended`: `pass` - recommended top-level count is 19
- `full`: `pass` - full top-level count is 26
- `dev`: `pass` - dev top-level count is 153

## Repair Hints

- Professional skill coverage: Repair weak professional skill sections without keyword stuffing.
- Foundation capability coverage: Improve selected capability evidence contracts and references.
- Open-source readiness: Owner must select an OSI license, update package metadata, confirm contribution licensing, and configure private vulnerability reporting before open-source publication.
- Hook safety: Run hook validation and inspect hook runtime changes; hooks must remain advisory and fail-open unless explicitly stricter.
- Installation validation: Run installation validation after rebuilding all profiles.
