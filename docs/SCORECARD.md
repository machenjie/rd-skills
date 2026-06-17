# Scorecard

The professional scorecard is a conservative health view of ChangeForge. It should help users understand what is verified, what is partial, and what still requires maintainer action.

Generate it with:

```bash
python3 scripts/generate-professional-scorecard.py --out reports/professional-scorecard.md --json-out reports/professional-scorecard.json
```

Render the dashboard and generated README summary with:

```bash
python3 scripts/render-scorecard-dashboard.py --scorecard reports/professional-scorecard.json --out docs/SCORECARD_DASHBOARD.md --readme README.md
```

CI smoke checks use the stricter profile-build mode after all profiles are built:

```bash
python3 scripts/generate-professional-scorecard.py --strict-profile-builds --out /tmp/professional-scorecard.md --json-out /tmp/professional-scorecard.json
```

## Dimensions

| Dimension | Status Source | Verification Command | Repair Path |
| --- | --- | --- | --- |
| Routing coverage | `reports/professionalism-release-readiness.json` routing summary. | `python3 scripts/validate-professional-routing-coverage.py` | Add or repair routing fixtures for uncovered risks. |
| Professional skill coverage | Professional skill coverage summary. | `python3 scripts/eval-skill-professionalism.py` | Improve skill contracts without keyword stuffing. |
| Foundation capability coverage | Coverage matrix summary. | `python3 scripts/eval-skill-professionalism.py --coverage-matrix` | Improve selected capability references and evidence contracts. |
| Reference loading discipline | Build manifests and runtime link validation. | `python3 scripts/validate-runtime-reference-links.py` | Keep references selected and linked; do not top-level all capabilities in recommended/full. |
| Hook safety | Hook validator. | `python3 scripts/validate-hooks.py` | Preserve advisory/fail-open behavior unless a stricter mode is explicitly enabled. |
| Validation suite coverage | Validation command list in scorecard JSON. | Full suite in [RELEASE.md](RELEASE.md) | Run missing commands and include results in release handoff. |
| Installation reproducibility | Build manifests and installer validation. | `python3 scripts/validate-installation.py` | Rebuild profiles, repair manifest/install mismatches, rerun doctor. |
| Marketplace index validation | Source-derived marketplace exporter and profile validator. | `python3 scripts/validate-marketplace-index.py --profile recommended && python3 scripts/validate-marketplace-index.py --profile full && python3 scripts/validate-marketplace-index.py --profile dev` | Rebuild profiles and repair schema, visibility, or runtime path mismatches. |
| Open-source readiness | `config/open-source-release.yaml`, [LICENSE_DECISION.md](LICENSE_DECISION.md), [OPEN_SOURCE_READINESS.md](OPEN_SOURCE_READINESS.md), `pyproject.toml`, `CONTRIBUTING.md`, `SECURITY.md`, and root `LICENSE`. | `python3 scripts/validate-open-source-readiness.py` | Owner chooses license, adds exact license text, updates package metadata, confirms contribution licensing, and confirms private vulnerability reporting or private security contact before open-source publication. |
| Example coverage | `examples/` scenario structure. | `python3 scripts/validate-examples.py` | Add prompt, route, and evidence files for each scenario. |
| Productization assets | Productization docs, schema, and generation/validation scripts. | `python3 scripts/validate-productization-assets.py` | Restore required productization assets. |

## Status Rules

- `pass`: machine-readable evidence exists and the check passed.
- `partial`: evidence exists but has warnings, needs-review items, or owner decisions.
- `fail`: evidence shows a broken invariant.
- `unknown`: the expected evidence artifact is absent or incomplete.
- `not_collected`: the command is known, but no machine-readable result is available for the scorecard to consume.

Do not replace `unknown` or `not_collected` with `pass` by hand. Run the verification command and update the scorecard generator only when the underlying tool emits reliable machine-readable evidence.

Open-source readiness is conservative: a root `LICENSE` alone is not enough. Proprietary `pyproject.toml` license metadata fails the dimension once a license file exists. `config/open-source-release.yaml:selected_license` must be non-null, contribution licensing must be owner-confirmed, and GitHub private vulnerability reporting or a private security contact must be owner-confirmed before the dimension can be `pass`.

## README Summary

The README should stay short. Link here for details instead of copying the full table into the front page.

See [SCORECARD_DASHBOARD.md](SCORECARD_DASHBOARD.md) for the generated dashboard and [BENCHMARKS.md](BENCHMARKS.md) for the benchmark system behind the scorecard.
