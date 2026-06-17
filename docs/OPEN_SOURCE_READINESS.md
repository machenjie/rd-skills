# Open Source Readiness

This audit tracks the repository work needed to meet common open-source project expectations. The repository is structurally close to open-source-ready after the governance, CI, quickstart, scorecard, examples, and discovery-index additions, but it is not publishable as an open-source project until maintainers choose and declare an OSI-approved license.

## Current Status

| Area | Status | Notes |
| --- | --- | --- |
| README | Ready | Describes project purpose, usage, runtime profiles, validation, guardrails, and governance links. |
| Quickstart / usage docs | Ready | [docs/QUICKSTART.md](QUICKSTART.md) covers first-run usage; [docs/USAGE.md](USAGE.md) covers build, install, agent usage, OpenAI API zips, upgrade, uninstall, and troubleshooting. |
| Benchmarks / scorecard | Ready | [docs/BENCHMARKS.md](BENCHMARKS.md) and [docs/SCORECARD.md](SCORECARD.md) explain generated evidence without hardcoded claims. |
| Examples / comparison / index | Ready | [../examples/README.md](../examples/README.md), [MARKETPLACE.md](MARKETPLACE.md), and [COMPARISON.md](COMPARISON.md) make capabilities discoverable and explain positioning. |
| Install/release docs | Ready | Existing installation, packaging, operating model, runtime profile, quality, and release docs are present. |
| Contribution guide | Ready | [CONTRIBUTING.md](../CONTRIBUTING.md) defines workflow, boundaries, validation, and PR expectations. |
| Code of conduct | Ready | [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) defines project participation standards. |
| Security policy | Needs owner setup | [SECURITY.md](../SECURITY.md) exists, but maintainers should enable GitHub private vulnerability reporting or publish a private contact channel. |
| Support policy | Ready | [SUPPORT.md](../SUPPORT.md) defines support scope and expected issue details. |
| Governance | Ready | [GOVERNANCE.md](../GOVERNANCE.md) defines maintainer responsibilities and decision authority. |
| Changelog | Ready | [CHANGELOG.md](../CHANGELOG.md) now tracks contributor-facing and release-facing changes. |
| GitHub templates | Ready | Issue and pull request templates capture repro details, boundaries, validation, and risk. |
| CI | Ready | `.github/workflows/ci.yml` runs core validation, profile builds for `recommended`, `full`, and `dev`, runtime reference validation, installation validation, marketplace export/validation, strict profile-build scorecard smoke, and unit tests. Heavy evals and benchmark comparisons remain release gates. |
| Package metadata | Partial | `pyproject.toml` has project URLs, keywords, and classifiers. License metadata remains proprietary pending owner decision. |
| License | Blocked | No open-source license file exists. Maintainers must choose the license. |

## Required Before Public Open-Source Release

1. Choose an OSI-approved license, such as MIT, Apache-2.0, BSD-3-Clause, MPL-2.0, GPL-3.0-only, or AGPL-3.0-only.
2. Add the matching root `LICENSE` file.
3. Update `pyproject.toml` from proprietary license metadata to the selected license metadata.
4. Confirm contribution licensing in [CONTRIBUTING.md](../CONTRIBUTING.md).
5. Enable GitHub private vulnerability reporting or publish a private security contact path in [SECURITY.md](../SECURITY.md).
6. Confirm whether generated `dist/` artifacts should remain ignored or be attached only to releases.
7. Run the full validation suite and confirm CI passes on a pull request.

## Owner Decision Required

The maintainer has not supplied a selected OSI license for this change. Until that decision is made:

- Do not add a root `LICENSE` file.
- Do not change `pyproject.toml` from proprietary license metadata.
- Do not describe the repository as open-source-ready.
- Treat outside contribution acceptance as blocked or maintainer-reviewed under the existing proprietary metadata.

Security contact also requires an owner-controlled private path. [SECURITY.md](../SECURITY.md) describes GitHub private vulnerability reporting when enabled, but the maintainer must either enable that feature or provide a private security contact channel before public release.

## Recommended Repository Standards

| Standard | Repository Expectation |
| --- | --- |
| Clear purpose | README explains this is a ChangeForge skill-authoring, build, package, and install repository. |
| Reproducible build | Runtime outputs are generated deterministically through `scripts/build.py`. |
| Safe install model | Installers consume `dist/` only and write manifests for managed install/uninstall. |
| Validation gate | Contributors run the full validation suite before release handoff. CI runs core validators, productization smoke, all profile builds, runtime reference validation, installation validation, marketplace validation, strict profile-build scorecard smoke, and unit tests; heavy evals and codegen benchmarks remain release-gate commands. |
| Security posture | Vulnerabilities are handled privately, with targeted regression coverage before release. |
| Contribution path | Issues and pull requests ask for scope, evidence, validation output, and boundary checks. |
| Release hygiene | Release runbook defines versioning, packaging, validation, smoke checks, and handoff requirements. |
| Legal clarity | License must be explicit before accepting outside contributions or publishing as open source. |

## Publication Gate

A release should not be described as open source until these checks pass:

```bash
python3 scripts/validate-skills.py
python3 scripts/validate-capabilities.py
python3 scripts/validate-domain-extensions.py
python3 scripts/validate-registry.py
python3 scripts/validate-skill-body-links.py
python3 scripts/validate-skill-content-size.py
python3 scripts/validate-examples.py
python3 scripts/validate-productization-assets.py
python3 scripts/audit-skill-content.py
python3 scripts/eval-routing.py
python3 scripts/eval-agent-behavior.py
python3 scripts/eval-skill-professionalism.py
python3 scripts/eval-skill-professionalism.py --coverage-matrix
python3 scripts/eval-professional-benchmarks.py
python3 scripts/validate-professionalism-regression.py
python3 scripts/validate-professional-routing-coverage.py
python3 scripts/validate-stage-routing-architecture.py
python3 scripts/validate-hooks.py
python3 scripts/eval-pressure-behavior.py
python3 -m unittest discover -s tests
python3 scripts/validate-codegen-benchmarks.py
python3 scripts/run-codegen-benchmarks.py --limit 3
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
python3 scripts/validate-runtime-reference-links.py
python3 scripts/validate-installation.py
python3 scripts/validate-marketplace-index.py --profile recommended
python3 scripts/validate-marketplace-index.py --profile full
python3 scripts/validate-marketplace-index.py --profile dev
python3 scripts/generate-professional-scorecard.py --strict-profile-builds --out /tmp/professional-scorecard.md --json-out /tmp/professional-scorecard.json
python3 scripts/export-marketplace-index.py --profile recommended --out /tmp/recommended-marketplace-index.json
```

The release handoff should include validation output, profile counts, installer smoke evidence, license decision, security contact status, and unresolved assumptions.
