# Contributing

Thank you for helping improve ChangeForge Skill Mesh. This repository authors, validates, builds, packages, installs, upgrades, and uninstalls ChangeForge runtime skills. Contributions should preserve that boundary.

## Repository Boundaries

Contributions must not:

- Install `src/` directly as runtime content.
- Install `src/registry` as runtime content.
- Add personal asset ingestion, scanning, indexing, summarization, mapping, packaging, or installation.
- Add toolbox mappings for user-specific technical archives.
- Create `src/toolbox` or `registry/toolbox.yaml`.
- Treat generated `references/` as automatic context loaded for every task.

Runtime skills are generated into `dist/` and installed from build outputs only.

## Before Opening An Issue

Search existing issues and docs first:

- [README.md](README.md)
- [docs/USAGE.md](docs/USAGE.md)
- [docs/INSTALLATION.md](docs/INSTALLATION.md)
- [docs/OPERATING_MODEL.md](docs/OPERATING_MODEL.md)
- [docs/RELEASE.md](docs/RELEASE.md)

For bugs, include the command you ran, the profile, the agent target, the relevant OS/runtime details, the observed result, and the expected result. Do not include secrets, tokens, private keys, customer data, or private repository content.

## Development Requirements

- Python 3.11 or newer.
- A clean checkout of this repository.
- Generated runtime outputs must come from `scripts/build.py`.

Build a profile before testing install behavior:

```bash
python3 scripts/build.py --profile full
```

## Validation Required Before Pull Request

Run the full validation suite before handoff:

```bash
python3 scripts/validate-skills.py
python3 scripts/validate-capabilities.py
python3 scripts/validate-domain-extensions.py
python3 scripts/validate-registry.py
python3 scripts/validate-skill-body-links.py
python3 scripts/validate-skill-content-size.py
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
```

When updating or verifying captured router outputs, also run:

```bash
python3 scripts/eval-routing.py --candidate-output-dir evals/routing-outputs
```

## Pull Request Checklist

Every pull request should state:

- What changed and why.
- Which skills, capabilities, registries, docs, installers, or evals were affected.
- Which validation commands passed.
- Any risk, rollback, compatibility, or migration notes.
- Any unresolved assumptions or maintainer decisions.

Documentation updates are required when a change affects CLI flags, install targets, runtime profiles, packaging behavior, release process, or skill selection behavior.

## Contribution Licensing

This repository currently records proprietary license metadata. Maintainers must choose and publish an OSI-approved repository license before accepting external contributions intended for public open-source distribution. After that decision, contribution licensing should follow the repository license and any additional maintainer policy documented here.
