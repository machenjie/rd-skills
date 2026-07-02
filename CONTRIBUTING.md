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

Run the validation tier that matches the change from
[docs/VALIDATION.md](docs/VALIDATION.md). For most productization and release
work, run **Fast Source Invariants** during development, then **Full Local** or
**Release Gate** before handoff. `docs/VALIDATION.md` is the canonical command
set; do not copy the full suite into pull request notes or other docs.

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

Documentation updates are required when a change affects CLI flags, install targets, runtime profiles, packaging behavior, release process, or skill selection behavior. Docs-only typo fixes can remain docs-only, but documentation that changes hook, validation, quality, stage, operating-model, benchmark, eval, routing, or release semantics must run the corresponding validation gate.

## Contribution Licensing

This repository is licensed under the MIT License. Contributions are accepted under the repository license unless maintainers document a different policy for a specific contribution path.
