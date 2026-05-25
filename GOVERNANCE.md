# Governance

This document defines the default governance model for ChangeForge Skill Mesh until maintainers publish a more formal structure.

## Roles

Maintainers are responsible for repository direction, review standards, release decisions, security handling, and enforcement of project boundaries.

Contributors propose issues, pull requests, documentation, tests, examples, and review feedback. Contributors do not gain release authority unless maintainers explicitly grant it.

## Decision Process

Routine fixes may be accepted after maintainer review and passing validation.

Changes require explicit maintainer agreement when they affect:

- Runtime profile semantics.
- Installer, upgrade, uninstall, or doctor behavior.
- Registry schema or routing behavior.
- Security, privacy, licensing, or release policy.
- Public documentation promises.
- The repository boundary against personal asset mapping or raw `src/` installation.

Maintainers should prefer small, evidence-backed changes with clear validation output. Unresolved assumptions should be documented in the pull request or release handoff.

## Release Authority

Only maintainers may cut releases, publish packaged artifacts, or change project license metadata. Releases must follow [docs/RELEASE.md](docs/RELEASE.md).

## Conflict Of Interest

A maintainer should recuse themselves from final decisions when they have a direct personal, employment, financial, or security-reporting conflict that could reasonably affect judgment.

## License Decision

The current repository metadata records a proprietary license. Before public open-source launch, maintainers must choose an OSI-approved license, add the matching `LICENSE` file, update `pyproject.toml`, and record the decision in [docs/OPEN_SOURCE_READINESS.md](docs/OPEN_SOURCE_READINESS.md) or a future decision record.