# Public Benchmark Summary

This generated summary reports local deterministic ChangeForge evidence. Skill efficacy fixtures are structural/local evidence, not live pass-rate or empirical before/after agent-performance proof. It does not claim external popularity, marketplace availability, or market adoption.

## Repository

- Repository: `machenjie/rd-skills`
- Version: `0.1.0`
- Source commit: `provided by release artifact / CI metadata`

## Status Counts

- `pass`: 9
- `partial`: 2
- `fail`: 0
- `unknown`: 0
- `not_collected`: 1

## Evidence

| Area | Status | Source | Detail | Refresh Command |
| --- | --- | --- | --- | --- |
| Routing coverage | `pass` | reports/professionalism-release-readiness.json | {"cases_checked": 118, "cases_without_forbidden": 0, "hidden_risks_checked": 91, "hidden_risks_needing_manual_review": 0, "hidden_risks_strongly_covered": 87, "l1_anti_over_routing_count": 9} | `python3 scripts/validate-professional-routing-coverage.py` |
| Professional skill coverage | `partial` | reports/professionalism-release-readiness.json | {"count": 19, "statuses": {"sample-grade": 19}} | `python3 scripts/eval-skill-professionalism.py` |
| Foundation capability coverage | `partial` | reports/professionalism-release-readiness.json | {"count": 40, "statuses": {"acceptable": 29, "needs-review": 10, "sample-grade": 1}} | `python3 scripts/eval-skill-professionalism.py --coverage-matrix` |
| Strict regression | `pass` | reports/professionalism-release-readiness.json | strict_regression_status=pass | `python3 scripts/validate-professionalism-regression.py --strict` |
| Skill professionalism report | `pass` | reports/skill-professionalism-eval.json | average_score=41.62 | `python3 scripts/eval-skill-professionalism.py` |
| Professional coverage matrix | `pass` | reports/professional-coverage-matrix.json | rows=59 | `python3 scripts/eval-skill-professionalism.py --coverage-matrix` |
| Profile build: recommended | `pass` | dist/universal/skills/recommended/.changeforge-build-manifest.json | top_level=19, expected=19 | `python3 scripts/build.py --profile recommended` |
| Profile build: full | `pass` | dist/universal/skills/full/.changeforge-build-manifest.json | top_level=26, expected=26 | `python3 scripts/build.py --profile full` |
| Profile build: dev | `pass` | dist/universal/skills/dev/.changeforge-build-manifest.json | top_level=148, expected=148 | `python3 scripts/build.py --profile dev` |
| Installation validation | `not_collected` | scripts/validate-installation.py | validator does not emit a committed machine-readable report | `python3 scripts/validate-installation.py` |
| Skill efficacy structural fixtures | `pass` | reports/professional-scorecard.json | {"evidence_boundary": "structural/local fixtures only; no empirical before/after agent performance", "fixtures": 3, "live_pass_rate": "not_collected", "token_overhead": "not_collected", "turn_overhead": "not_collected", "verdicts": {"structural_pass": 3}} | `python3 scripts/validate-skill-efficacy-benchmarks.py` |
| Marketplace index validation | `pass` | reports/professional-scorecard.json | recommended, full, and dev marketplace indexes validate | `python3 scripts/validate-marketplace-index.py --profile recommended && python3 scripts/validate-marketplace-index.py --profile full && python3 scripts/validate-marketplace-index.py --profile dev` |

## Known Unknowns / Not Collected

- Installation validation

## Refresh Commands

```bash
python3 scripts/eval-routing.py
python3 scripts/eval-skill-professionalism.py
python3 scripts/eval-skill-professionalism.py --coverage-matrix
python3 scripts/eval-professional-benchmarks.py
python3 scripts/validate-skill-efficacy-benchmarks.py
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
