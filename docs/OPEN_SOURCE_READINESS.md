# Open-Source Readiness

The repository is MIT licensed and contains the normal policy and contribution files expected for publication. A specific release is ready only when current validation passes; this document does not predeclare that result.

## Repository Assets

| Area | Source |
| --- | --- |
| Purpose and usage | [README](../README.md), [Quickstart](QUICKSTART.md), [Usage](USAGE.md) |
| Architecture and boundaries | [Hookless architecture](HOOKLESS_ARCHITECTURE.md), [AI control boundaries](AI_CONTROL_BOUNDARIES.md) |
| Build and installation | [Installation](INSTALLATION.md), [Build profiles](BUILD_PROFILES.md), [Release](RELEASE.md) |
| Quality and claims | [Validation](VALIDATION.md), [Benchmarks](BENCHMARKS.md), [Scorecard](SCORECARD.md) |
| Contribution and governance | [CONTRIBUTING](../CONTRIBUTING.md), [GOVERNANCE](../GOVERNANCE.md), [CODE_OF_CONDUCT](../CODE_OF_CONDUCT.md) |
| Security and support | [SECURITY](../SECURITY.md), [SUPPORT](../SUPPORT.md) |
| Legal | [LICENSE](../LICENSE), [Governance](../GOVERNANCE.md) |

## License Metadata

The root [LICENSE](../LICENSE) is the legal authority. Project metadata declares
MIT in [pyproject.toml](../pyproject.toml), while
[open-source-release.yaml](../config/open-source-release.yaml) selects MIT and
records contribution-licensing and security-contact confirmation. Those
metadata facts do not replace the grant or predeclare a release pass.

## Publication Gate

Before describing a release as ready:

1. Run `python3 scripts/validate-open-source-readiness.py --require-pass` to
   verify the root grant, project metadata, release configuration,
   contribution licensing, and security contact together.
2. Run the current release suite in [Validation](VALIDATION.md).
3. Confirm all three build counts and supported-host Profile files.
4. Confirm install, upgrade, doctor, and uninstall preserve unrelated user content.
5. Regenerate source-derived catalogs and reports whose inputs changed.
6. Confirm tracked generated artifacts have no source drift.
7. Disclose every skipped check, unresolved assumption, evidence limitation, and residual risk.

Official marketplace publishing is not implemented. Repository readiness covers
static contracts, deterministic fixtures, code-generation definition and
harness/negative-control checks, builds, and simulated installation; it does
not prove real-host behavior, wall-clock performance, production accuracy, or
installed user experience.
