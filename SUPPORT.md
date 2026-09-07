# Support

Start with the owner of the problem:

- First installation or first task: [Quickstart](docs/QUICKSTART.md).
- Everyday prompts, results, or task behavior: [Usage](docs/USAGE.md).
- Paths, scopes, permissions, conflicts, backup, upgrade, uninstall, or recovery: [Advanced Installation & Recovery](docs/INSTALLATION.md#troubleshooting-and-recovery).
- A historical `recommended`, `full`, or `dev` installation: [Migration](docs/MIGRATING_TO_HOOKLESS.md).
- A suspected vulnerability: follow the private reporting instructions in [Security](SECURITY.md), not a public issue.

## Report a reproducible problem

Use GitHub issues for reproducible bugs, documentation gaps, validation failures, packaging problems, and feature requests. Use pull requests for proposed fixes with current validation results.

Include:

- the exact command or natural-language request;
- the selected tool: `codex`, `claude`, `copilot`, `cline`, or `openai-api`;
- the selected scope: `project`, `user`, or `admin` when applicable;
- whether the target was default or explicit;
- operating system and Python version;
- the first specific error and relevant redacted output; and
- output from the matching real command, for example `python3 installers/doctor.py --agent codex --scope user --verbose`, when the problem concerns installation artifacts.

Remove usernames, private absolute paths, repository contents, tokens, credentials, customer data, and other secrets before posting.

## Support boundary

This project supports rd-skills authoring, validation, build, packaging, installation, upgrade, uninstall, and installed-artifact verification.

It does not support personal asset ingestion, private archive indexing, user-specific content packaging, installing raw `src/` content, or behavior caused by external private knowledge bases.

Doctor can prove the installed artifact contract. It cannot prove that a real AI coding tool loaded the files, that a provider enforced declared permissions, or that production behavior is correct.
