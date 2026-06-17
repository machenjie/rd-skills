# Scorecard

The professional scorecard is a conservative health view of ChangeForge. It should help users understand what is verified, what is partial, and what still requires maintainer action.

Generate it with:

```bash
python3 scripts/generate-professional-scorecard.py --out reports/professional-scorecard.md --json-out reports/professional-scorecard.json
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
| Open-source readiness | [OPEN_SOURCE_READINESS.md](OPEN_SOURCE_READINESS.md) and `pyproject.toml`. | `python3 scripts/validate-productization-assets.py` | Owner chooses license and security contact before open-source publication. |
| Example coverage | `examples/` scenario structure. | `python3 scripts/validate-examples.py` | Add prompt, route, and evidence files for each scenario. |
| Productization assets | Productization docs, schema, and generation/validation scripts. | `python3 scripts/validate-productization-assets.py` | Restore required productization assets. |

## Status Rules

- `pass`: machine-readable evidence exists and the check passed.
- `partial`: evidence exists but has warnings, needs-review items, or owner decisions.
- `fail`: evidence shows a broken invariant.
- `unknown`: the expected evidence artifact is absent or incomplete.
- `not_collected`: the command is known, but no machine-readable result is available for the scorecard to consume.

Do not replace `unknown` or `not_collected` with `pass` by hand. Run the verification command and update the scorecard generator only when the underlying tool emits reliable machine-readable evidence.

Open-source readiness is conservative: a root `LICENSE` alone is not enough. Proprietary `pyproject.toml` license metadata fails the dimension once a license file exists; confirmed contribution licensing and an enabled private vulnerability report path or private security contact are required for `pass`.

## README Summary

The README should stay short. Link here for details instead of copying the full table into the front page.

See [BENCHMARKS.md](BENCHMARKS.md) for the benchmark system behind the scorecard.
