# License Decision

The repository license decision is complete.

## Current Status

- Repository/tooling license metadata: MIT.
- Root `LICENSE`: present with MIT License text.
- Open-source publication status: ready when release validation passes.
- Contribution licensing confirmation: confirmed in [../CONTRIBUTING.md](../CONTRIBUTING.md).
- Private vulnerability reporting or private security contact: confirmed in [../SECURITY.md](../SECURITY.md).

## Decision

ChangeForge Skill Mesh is licensed under the MIT License. The root [../LICENSE](../LICENSE) file is the repository legal grant for source, tooling, validation, build, packaging, installer, and approved runtime support artifacts unless a file states otherwise.

Repository/tooling license metadata and generated skill frontmatter remain separate contracts. Build and install tooling preserves each generated skill's runtime frontmatter instead of inheriting repository metadata.

## Release Requirements

Before public release handoff, maintainers should verify:

1. `pyproject.toml` declares `license = { text = "MIT" }`.
2. `config/open-source-release.yaml` declares `selected_license: MIT`, `contribution_licensing_confirmed: true`, and `security_contact_confirmed: true`.
3. [../CONTRIBUTING.md](../CONTRIBUTING.md) confirms contribution licensing under the repository license.
4. [../SECURITY.md](../SECURITY.md) documents private vulnerability reporting when enabled and the private maintainer-channel fallback.
5. `python3 scripts/validate-open-source-readiness.py` passes.
6. Release scorecards and public benchmark summaries are regenerated or validated fresh when their source inputs change.
