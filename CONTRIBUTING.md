# Contributing

Thank you for helping improve ChangeForge. This repository authors, validates,
builds, packages, installs, upgrades, and uninstalls standard AI Skills and
static Agent Profiles. Contributions should preserve that boundary.

## Repository Boundaries

Contributions must not:

- Install `src/` directly as runtime content.
- Install `src/registry` as runtime content.
- Add personal asset ingestion, scanning, indexing, summarization, mapping, packaging, or installation.
- Add toolbox mappings for user-specific technical archives.
- Create `src/toolbox` or `registry/toolbox.yaml`.
- Treat generated `references/` as automatic context loaded for every task.

Installable Skills and optional host-native Agent Profiles are generated into
`dist/` and installed from build outputs only. Hook interception, hidden pack
delivery, runtime state engines, private or persistent evidence-ledger
machinery, and user-specific content corpora are outside the architecture.
Implementation handoffs still require the visible task-local Markdown Evidence
Ledger defined by the operating and subagent models.

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

Install the declared validation dependency before running repository checks:

```bash
python3 -m pip install .
```

Build a profile before testing install behavior:

```bash
python3 scripts/build.py --profile full
```

## Validation Required Before Pull Request

Every Skill-system change must run the complete ordinary authoring gate from
[Validation](docs/VALIDATION.md) on the final material edit, in the documented
order. This includes documentation-only changes because documentation,
generated discovery assets, productization, unit tests, code-generation checks,
and quickstart dry runs share current-tree evidence. Do not replace the complete
gate with a smaller set of individually passing checks.

Targeted tests remain useful while developing, but they are diagnostic evidence
until the complete ordinary gate passes. Formal-release commands and the remote
`Formal Release` workflow are additional release evidence; they are not part of
the ordinary pull-request gate.

## Pull Request Checklist

Every pull request should state:

- What changed and why.
- Which Control, Professional, Foundation, or Domain Skills, Agent Profiles, registries, docs, installers, or evals were affected.
- Which validation commands passed.
- Any risk, rollback, compatibility, or migration notes.
- Any unresolved assumptions or maintainer decisions.

Documentation updates are required when a change affects CLI flags, install
targets, build profiles, packaging behavior, release process, or Skill
selection behavior. Small wording fixes may remain documentation-only in file
scope, but they still run the complete ordinary authoring gate.

## Contribution Licensing

This repository is licensed under the MIT License. Contributions are accepted under the repository license unless maintainers document a different policy for a specific contribution path.
