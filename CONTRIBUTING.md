# Contributing

Thank you for helping improve rd-skills. This repository authors, validates,
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

For bugs, include the command you ran, the Host and scope, relevant OS/runtime
details, the observed result, and the expected result. Do not include secrets,
tokens, private keys, customer data, or private repository content.

## Development Requirements

- Python 3.11 or newer.
- A clean checkout of this repository.
- Generated runtime outputs must come from `scripts/build.py`.

Install the declared validation dependency before running repository checks:

```bash
python3 -m pip install .
```

Build the Runtime before testing install behavior:

```bash
python3 scripts/build.py
```

## Validation Required Before Pull Request

Every committed Skill-system change must run [Development
Affected](docs/VALIDATION.md#development-affected) for its selected base and
head. Documentation-only changes remain in scope because the Core impact graph
maps them to their owning documentation producer and tests.

Focused checks remain useful while changes are uncommitted. The [local Full
Regression](docs/VALIDATION.md#local-full-regression) runs once before an
integration handoff or release-candidate decision. The local formal-release
command is additional independent release evidence.

## Pull Request Checklist

Every pull request should state:

- What changed and why.
- Which Control, Professional, Foundation, or Domain Skills, Agent Profiles, registries, docs, installers, or evals were affected.
- Which validation commands passed.
- Any risk, rollback, compatibility, or migration notes.
- Any unresolved assumptions or maintainer decisions.

Documentation updates are required when a change affects CLI flags, install
targets, Runtime composition, packaging behavior, migration, release process,
or Skill selection behavior. New knowledge must prefer an existing Targeted
Reference, Foundation/Domain Skill, or Professional Skill in that order. A new
Professional Skill requires stable independent Primary routing and clear task
ownership. Small wording fixes may remain documentation-only in file scope, but
their committed base/head still runs Development Affected validation.

## Contribution Licensing

This repository is licensed under the MIT License. Contributions are accepted under the repository license unless maintainers document a different policy for a specific contribution path.
