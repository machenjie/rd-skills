# Open Source Readiness

This audit tracks the repository work needed to meet common open-source project expectations. The repository is MIT licensed and ready for public open-source publication when the release validation gates pass.

## Current Status

| Area | Status | Notes |
| --- | --- | --- |
| README | Ready | Describes project purpose, usage, runtime profiles, validation, guardrails, governance links, and MIT license. |
| Quickstart / usage docs | Ready | [docs/QUICKSTART.md](QUICKSTART.md) covers first-run usage; [docs/USAGE.md](USAGE.md) covers build, install, agent usage, OpenAI API zips, upgrade, uninstall, and troubleshooting. |
| Benchmarks / scorecard | Ready | [docs/BENCHMARKS.md](BENCHMARKS.md) and [docs/SCORECARD.md](SCORECARD.md) explain generated evidence without hardcoded claims. |
| Examples / comparison / index | Ready | [../examples/README.md](../examples/README.md), [MARKETPLACE.md](MARKETPLACE.md), and [COMPARISON.md](COMPARISON.md) make capabilities discoverable and explain positioning. |
| Install/release docs | Ready | Existing installation, packaging, operating model, runtime profile, quality, and release docs are present. |
| Contribution guide | Ready | [CONTRIBUTING.md](../CONTRIBUTING.md) confirms contributions are accepted under the repository license unless maintainers document otherwise. |
| Code of conduct | Ready | [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) defines project participation standards. |
| Security policy | Ready | [SECURITY.md](../SECURITY.md) documents private vulnerability reporting when enabled and a private maintainer channel fallback. |
| Support policy | Ready | [SUPPORT.md](../SUPPORT.md) defines support scope and expected issue details. |
| Governance | Ready | [GOVERNANCE.md](../GOVERNANCE.md) defines maintainer responsibilities, decision authority, and license-change governance. |
| Changelog | Ready | [CHANGELOG.md](../CHANGELOG.md) tracks contributor-facing and release-facing changes. |
| GitHub templates | Ready | Issue and pull request templates capture repro details, boundaries, validation, and risk. |
| CI | Ready | `.github/workflows/ci.yml` runs core validation, profile builds for `recommended`, `full`, and `dev`, runtime reference validation, installation validation, marketplace export/validation, strict profile-build scorecard smoke, and unit tests. Heavy evals and benchmark comparisons remain release gates. |
| Package metadata | Ready | `pyproject.toml` declares MIT license metadata, project URLs, keywords, and classifiers. |
| License | Ready | The root [../LICENSE](../LICENSE) file contains the MIT License text. |
| Owner release config | Ready | [../config/open-source-release.yaml](../config/open-source-release.yaml) records `selected_license: MIT`, contribution licensing confirmation, security contact confirmation, and `release-artifact-only` dist policy. |

## Required Before Public Open-Source Release

1. Run the Release Gate from [VALIDATION.md#release-gate](VALIDATION.md#release-gate) or explicitly document any unrun command and residual risk.
2. Run `python3 scripts/validate-open-source-readiness.py` and confirm it passes.
3. Regenerate or validate the professional scorecard, scorecard dashboard, public benchmark summary, marketplace catalog, and showcase snapshots when their sources change.
4. Confirm the release handoff includes validation output, profile counts, installer smoke evidence, MIT license status, security contact status, and unresolved assumptions.

## Recommended Repository Standards

| Standard | Repository Expectation |
| --- | --- |
| Clear purpose | README explains this is a ChangeForge skill-authoring, build, package, and install repository. |
| Reproducible build | Runtime outputs are generated deterministically through `scripts/build.py`. |
| Safe install model | Installers consume `dist/` only and write manifests for managed install/uninstall. |
| Validation gate | Contributors run the appropriate validation suite before release handoff. CI runs core validators, productization smoke, all profile builds, runtime reference validation, installation validation, marketplace validation, strict profile-build scorecard smoke, and unit tests; heavy evals and codegen benchmarks remain release-gate commands. |
| Security posture | Vulnerabilities are handled privately, with targeted regression coverage before release. |
| Contribution path | Issues and pull requests ask for scope, evidence, validation output, and boundary checks. |
| Release hygiene | Release runbook defines versioning, packaging, validation, smoke checks, and handoff requirements. |
| Legal clarity | Repository/tooling is MIT licensed; per-skill runtime frontmatter remains a separate generated skill contract. |

## Publication Gate

A release may be described as open source only when [VALIDATION.md#release-gate](VALIDATION.md#release-gate) and `python3 scripts/validate-open-source-readiness.py` pass, or when any skipped release-gate command is explicitly disclosed with owner, reason, and residual risk.
