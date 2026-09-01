# Advanced Installation & Recovery Reference

Use this reference for non-default paths, project or admin scope, previewing changes, conflicts, backups, upgrade, uninstall, OpenAI API packages, and recovery. For a normal first installation, use [Quickstart](QUICKSTART.md).

Run commands from the repository root with Python 3.11 or newer after:

```bash
python3 -m pip install .
```

Install only generated artifacts under `dist/`. Never copy `src/`, source registries, reports, or personal content into an AI coding tool's configuration.

## Host, Scope, And Default Targets

| Host | Supported scope | Default/project Skill target | Agent Profile target |
| --- | --- | --- | --- |
| Codex | `project` | `<project>/.agents/skills` | `<project>/.codex/agents` |
| Codex | `user` | `~/.agents/skills` | `~/.codex/agents` |
| Codex | `admin` | `/etc/codex/skills` | `/etc/codex/agents` |
| Claude | `project` | `<project>/.claude/skills` | `<project>/.claude/agents` |
| Claude | `user` | `~/.claude/skills` | `~/.claude/agents` |
| Copilot | `project` | `<project>/.github/skills` | `<project>/.github/agents` |
| Copilot | `user` | `~/.copilot/skills` | `~/.copilot/agents` |
| Cline | `project` | `<project>/.cline/skills` | none |
| Cline | `user` | `~/.cline/skills` | none |
| OpenAI API | zip output only | `dist/openai-api/zips/recommended/` | none |

Codex, Claude, and Copilot install the four static Agent Profiles. Cline installs Skills without native Agent Profile files. OpenAI API produces zip files only and has no runtime target.

For `project`, `--target` means the project root and is required. For `user` or Codex `admin`, `--target` means an explicit Skill directory, not a project root. An explicit user/admin Skill target does not relocate the host's default Agent Profile target. Omit `--target` to use the user or admin defaults above.

Codex `admin` writes below `/etc/codex`; preview it first and use only an approved privilege boundary. Claude, Copilot, and Cline reject `admin` scope.

## Build

```bash
python3 scripts/build.py
```

The build creates the fixed current Runtime under `dist/`. It contains 26 top-level Skills and the supported host-specific outputs. The internal `recommended` directory and manifest identity remain for compatibility; they are not a CLI choice. [Runtime build](BUILD_PROFILES.md) owns the full composition and generated manifest contract.

Every installer validates the built source and manifest before changing a target. Never hand-edit generated build manifests.

## Install

The normal one-command path is:

```bash
python3 scripts/quickstart.py --agent codex --scope user
```

For direct installer control, build first and preview the exact operation:

```bash
python3 scripts/build.py
python3 installers/install.py --agent codex --scope project --target /absolute/path/to/project --dry-run
python3 installers/install.py --agent codex --scope project --target /absolute/path/to/project
```

A user installation uses its default target unless you provide an explicit Skill directory:

```bash
python3 installers/install.py --agent claude --scope user --dry-run
python3 installers/install.py --agent claude --scope user
```

### Conflicts and `--force`

The installer rejects unmanaged artifacts whose names collide with incoming rd-skills artifacts. Inspect every reported path before considering `--force`.

Use `--force` only when replacement of those exact unmanaged same-name artifacts is intended and separately recoverable. It does not bypass source validation, ownership checks, path containment, unsupported scopes, unsafe names, or permissions.

### Optional install backup

`--backup` copies only incoming or previously managed rd-skills paths, the install manifest, and bounded known legacy paths that already exist. It writes below the Skill target's `.changeforge-backups/` directory.

This backup is not a complete snapshot of the AI coding tool's configuration. Make an independent backup when local policy or surrounding user-owned content requires one.

## Doctor

```bash
python3 installers/doctor.py --agent codex --scope user
```

Healthy normal output reports the result and next step. Detailed inventory, source binding, enforcement, Profile, and digest information is available only when requested:

```bash
python3 installers/doctor.py --agent codex --scope user --verbose
```

Doctor checks the install manifest, top-level Skill roots, current build/core/source bindings, legacy residue, and the host-specific Agent Profile contract. Failures retain the specific issue and return a nonzero exit.

Doctor verifies installation artifacts. It does not prove your AI coding tool loaded rd-skills. A real-host smoke test requires restarting the target tool and running a small task.

## Upgrade And Legacy Runtime Migration

Use upgrade for an existing manifest-owned installation. Build, preview, upgrade, and check in this order:

```bash
python3 scripts/build.py
python3 installers/upgrade.py --agent codex --scope user --dry-run
python3 installers/upgrade.py --agent codex --scope user
python3 installers/doctor.py --agent codex --scope user
```

Do not uninstall an existing `full` or `dev` installation first. Upgrade accepts only an exact supported current or historical manifest. Extra, missing, replacement, duplicate, unsafe, or hybrid inventory fails before target mutation, and `--force` does not bypass ownership validation.

Before any live cleanup or replacement, upgrade must create a complete backup of the currently managed Skill directories, managed Agent Profile files, manifest, and bounded known legacy paths. If backup cannot complete, upgrade stops before mutation. The path is printed and recorded in the new manifest.

Unmanaged top-level files and directories remain in place. A user file mixed inside a managed Skill directory is included in the backup, but the managed directory is replaced as a unit. Restore that file selectively only after verifying its owner and destination.

Upgrade is not crash-atomic across legacy cleanup, Skill replacement, Agent Profile replacement, and final manifest write. If interrupted, stop further writes and follow [Recovery](#troubleshooting-and-recovery).

Historical inventories, managed removals, interruption handling, and rollback are centralized in [Migrating to the Hookless Architecture](MIGRATING_TO_HOOKLESS.md).

## Uninstall

Preview first:

```bash
python3 installers/uninstall.py --agent codex --scope user --dry-run
python3 installers/uninstall.py --agent codex --scope user
```

Uninstall accepts the current and exact supported historical manifests. Unrelated top-level content is preserved. Every manifest-managed Skill directory is deleted as a whole, so files mixed into that directory are deleted with it. Managed Agent Profile files, the manifest, and bounded known legacy artifacts are also removed. Uninstall creates no automatic backup or recovery copy.

## OpenAI API Zip Output

Generate and validate the fixed package set:

```bash
python3 scripts/build.py
python3 scripts/package.py
python3 installers/install.py --agent openai-api
```

Build and package write 26 zip files under `dist/openai-api/zips/recommended/`. Each zip contains one matching top-level Skill folder with a root `SKILL.md`. The installer command validates local bundles; it does not upload them or install them into a live API service.

These files are not evidence of marketplace publication, provider behavior, or a loaded integration.

## Troubleshooting And Recovery

| Symptom | Safe response |
| --- | --- |
| `missing built runtime ...` | Run `python3 scripts/build.py`, then repeat the same dry run. |
| Build manifest is missing or invalid | Delete no target content. Re-run the build; never hand-author the manifest. |
| Doctor reports migration required | Build, preview upgrade, and run upgrade directly. Do not uninstall first. |
| Upgrade says no manifest exists | Inspect the target. Use install only for a new target; otherwise back up pre-manifest content and resolve each unmanaged conflict. |
| Permission denied | Stop. Choose `user` or `project`, correct ownership through the tool's approved process, or obtain authorization for Codex `admin`. `--force` is not a permission workaround. |
| Unsupported scope | Use the matrix above. Only Codex supports `admin`; project scope requires a project-root `--target`; OpenAI API uses zip output. |
| Doctor reports stale or missing files or bindings | Preserve the output, rebuild, preview upgrade, run it only with a valid manifest, then rerun doctor. |
| Unmanaged-name conflict | Inspect exact paths and ownership. Move or back up user content, or use `--force` only after confirming replacement of those exact names. |
| An upgrade was interrupted | Stop writes. Inspect the newest `upgrade-*` backup and compare its contents with the target before restoring any path. |

Backups live below the Skill target's `.changeforge-backups/` directory. Compare the backup's `skills/`, `profiles/`, and optional `legacy/` contents with the intended target. Restore only verified managed paths through the normal filesystem or configuration-management process.

rd-skills has no automatic restore CLI. Do not copy a backup root wholesale over unrelated tool configuration. If no usable backup exists, stop rather than guessing ownership.

After a healthy install, return to [Usage](USAGE.md). For historical cleanup or rollback, use [Migration](MIGRATING_TO_HOOKLESS.md#rollback). For unresolved installation problems, follow [Support](../SUPPORT.md).

Local build, installer, package, and doctor checks prove the declared artifact contracts only. They do not prove real-host startup, host-enforced permissions, wall-clock performance, production accuracy, provider behavior, or installed user experience.
