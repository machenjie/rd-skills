# Security Policy

ChangeForge Skill Mesh is a skill-authoring, validation, build, packaging, and installer repository. Security reports may involve installer behavior, generated runtime skill artifacts, package shape, registry validation, routing rules, or documentation that could cause unsafe agent behavior.

## Supported Versions

Security fixes are handled on the default branch until maintainers publish a version support policy.

| Version | Supported |
| --- | --- |
| Default branch | Yes |
| Older releases | Best effort until a formal support window is published |

## Reporting A Vulnerability

Do not open a public issue for a vulnerability.

Use GitHub private vulnerability reporting when it is enabled for this repository. If private vulnerability reporting is not available, contact the repository maintainers through a private channel controlled by the repository owner before sharing details.

Include:

- A concise description of the issue.
- Affected files, commands, profiles, agents, or generated outputs.
- Reproduction steps using non-sensitive sample data.
- Expected impact and any known workaround.
- Whether the report includes installer behavior, generated runtime artifacts, or agent-routing behavior.

Do not include real secrets, private keys, tokens, customer data, or private repository content.

## Response Expectations

Maintainers should acknowledge valid private reports, investigate impact, prepare a fix, run the validation suite, and coordinate disclosure timing with the reporter when practical.

Security fixes must preserve repository boundaries:

- Do not install `src/` directly.
- Do not install raw registry content.
- Do not create personal asset mappings.
- Do not weaken validation, package shape, or manifest safety checks to work around a report.

## Security Validation

Security-sensitive changes should run the relevant validation tier from [docs/VALIDATION.md](docs/VALIDATION.md), plus any targeted reproducer or regression test needed for the report.
