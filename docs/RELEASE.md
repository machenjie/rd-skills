# Release

This runbook covers ChangeForge skill system releases. Releases are cut from authored source, validated registries, generated `dist/` outputs, profile-scoped OpenAI API zips, and installer smoke evidence.

## Versioning

- Update `pyproject.toml` `[project].version` for repository release identity.
- Update `changeforge_version` in touched `SKILL.md` files when skill behavior changes.
- Preserve backward compatibility for registry fields, runtime folder names, and installer CLI flags unless a migration note is included.

## Build

Build every profile:

```bash
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
```

Expected top-level runtime counts:

- `recommended`: 19 professional skills.
- `full`: 19 professional skills plus 7 domain extensions.
- `dev`: 19 professional skills plus 81 foundation capabilities plus 7 domain extensions.

## Package

OpenAI API zips are profile-scoped under `dist/openai-api/zips/<profile>`. Repackage a built profile when needed:

```bash
python3 scripts/package.py --profile recommended
python3 scripts/package.py --profile full
python3 scripts/package.py --profile dev
```

Each zip must contain exactly one top-level skill folder and exactly one root `SKILL.md`.

## Validation

Run the core validation suite before handoff:

```bash
python3 scripts/validate-skills.py
python3 scripts/validate-capabilities.py
python3 scripts/validate-registry.py
python3 scripts/validate-installation.py
```

Run installer dry runs for supported targets:

```bash
python3 installers/install.py --agent codex --scope user --profile recommended --dry-run
python3 installers/install.py --agent codex --scope project --target /tmp/changeforge-test-repo --profile full --dry-run
python3 installers/install.py --agent claude --scope user --profile recommended --dry-run
python3 installers/install.py --agent claude --scope project --target /tmp/changeforge-test-repo --profile full --dry-run
python3 installers/install.py --agent copilot --scope user --profile recommended --dry-run
python3 installers/install.py --agent copilot --scope project --target /tmp/changeforge-test-repo --profile full --dry-run
python3 installers/install.py --agent openai-api --profile recommended --dry-run
```

## Release Checklist

- Source structure matches the registry counts.
- No banned `src/toolbox` or `registry/toolbox.yaml` path exists.
- No personal asset mapping, raw `src/`, or raw registry content is installed.
- All runtime skills contain root `SKILL.md`.
- Foundation capabilities are compiled into professional skill references for `recommended` and `full`.
- Installer dry runs show 19 skills for recommended and 26 for full project installs.
- Smoke install, uninstall, reinstall, and doctor pass for Codex, Claude Code, and GitHub Copilot project targets.
- OpenAI API zips pass profile count and archive shape validation.
- Docs reflect any CLI, packaging, profile, or installer behavior changes.
- Unresolved assumptions and manual review points are listed in the release handoff.
