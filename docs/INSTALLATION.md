# Installation

Install only generated artifacts under `dist/`. Never copy `src/`, source
registries, reports, or personal content into an agent configuration. Run all
commands from the repository root with Python 3.11 or newer after
`python3 -m pip install .`.

For the shortest build/install/doctor path, start with [Quickstart](QUICKSTART.md).

## Build

Build the one Runtime:

```bash
python3 scripts/build.py
```

The build emits exactly 26 top-level Skills: 1 Control and 25 Professional.
Foundation and Domain Skills remain in the complete source inventory and are
compiled only as Professional-owned JIT Layer 3 guidance. [Runtime build](BUILD_PROFILES.md)
owns composition, temporary completeness validation, supported-host Agent
Profile output, and manifest fields. Every installer validates the built
manifest before changing its target.

The internal directory and manifest identity remains `recommended` for
compatibility. It is fixed and is not a CLI choice.

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

Codex, Claude, and Copilot install the four static Agent Profiles. Cline
installs Skills without native Agent Profile files. OpenAI API produces zip
files only and has no runtime target.

For `project`, `--target` means the project root and is required. For `user` or
Codex `admin`, `--target` means an explicit Skill directory, not a project root.
An explicit user/admin Skill target does not relocate the host's default Agent
Profile target. Omit `--target` to use the defaults above.

Codex `admin` writes below `/etc/codex`; preview it first and use only an
approved privilege boundary. Claude, Copilot, and Cline reject `admin` scope.

## Install

Replace `/absolute/path/to/project` with an existing project root. Always
preview the same command first:

```bash
python3 installers/install.py \
  --agent codex --scope project --target /absolute/path/to/project \
  --dry-run
python3 installers/install.py \
  --agent codex --scope project --target /absolute/path/to/project
```

User installation needs no target when the default is correct:

```bash
python3 installers/install.py --agent claude --scope user --dry-run
python3 installers/install.py --agent claude --scope user
```

The installer rejects unmanaged artifacts whose names collide with incoming
rd-skills artifacts. Inspect every reported path before considering `--force`.
Use `--force` only when replacement of those exact unmanaged same-name
artifacts is intended and separately recoverable. It does not bypass source
validation, path containment, unsupported scopes, or unsafe names.

Optional install `--backup` copies only incoming or previously managed
rd-skills paths, the install manifest, and bounded known legacy paths that
already exist. It writes below the Skill target's `.changeforge-backups/`
directory and is not a full Host-configuration snapshot.

## Doctor

```bash
python3 installers/doctor.py --agent codex --scope user
```

Doctor checks the manifest, 26 top-level Skill roots, current build/core/source
bindings, legacy residue, and the host-specific Agent Profile contract. Codex,
Claude, and Copilot must have the exact four-role file set; Cline correctly has
none. A valid legacy `full` or `dev` manifest is reported as
migration-required. Doctor is artifact evidence, not proof of real-Host
startup.

## Upgrade And Legacy Runtime Migration

Build first, then preview and run upgrade. Do not uninstall an existing
`full` or `dev` installation first:

```bash
python3 scripts/build.py
python3 installers/upgrade.py --agent codex --scope user --dry-run
python3 installers/upgrade.py --agent codex --scope user
python3 installers/doctor.py --agent codex --scope user
```

Upgrade requires an existing rd-skills manifest. It accepts the exact current
or legacy `recommended`, `full`, and `dev` inventories, validates ownership,
and migrates all of them to the fixed Runtime manifest. For legacy installs it
removes managed top-level Domain Skills and, for `dev`, managed top-level
Foundation Skills. It does not require an intermediate uninstall.

Before any live cleanup or replacement, upgrade must create a complete backup
of the currently managed Skill directories, managed Agent Profile files,
manifest, and bounded known legacy paths. If that backup cannot be completed,
upgrade stops before mutation. The resulting path is printed and recorded in
the new manifest.

Ownership is directory-granular for a managed top-level Skill. Unmanaged
top-level files and directories remain in place. A user file mixed inside a
managed Skill directory is included in the backup, but the managed directory
is then replaced as a unit; restore that mixed-in file selectively from the
backup after verifying it belongs there. Upgrade never deletes an unrelated
top-level user Skill merely because a legacy Runtime is being migrated.

Upgrade is not crash-atomic across legacy cleanup, Skill replacement, Agent
Profile replacement, and final manifest write. If it is interrupted after the
backup, stop further writes, inspect the newest `upgrade-*` backup, compare its
`skills/`, `profiles/`, and optional `legacy/` contents with the target, and
restore only verified files through the normal filesystem or configuration
management process.

rd-skills has no automatic restore CLI. Do not copy the backup root wholesale
over unrelated Host content. If no usable backup exists, stop rather than
guessing ownership.

## Uninstall

```bash
python3 installers/uninstall.py --agent codex --scope user --dry-run
python3 installers/uninstall.py --agent codex --scope user
```

Uninstall accepts current and exact legacy manifests and removes only their
declared managed inventory plus bounded known legacy artifacts. It does not
remove unrelated user content or restore a backup automatically.

## OpenAI API Zip Output

Generate and validate the fixed Runtime zip set:

```bash
python3 scripts/build.py
python3 scripts/package.py
python3 installers/install.py --agent openai-api
```

Build and package write 26 zip files under the compatibility path
`dist/openai-api/zips/recommended/`. Each zip is named for one top-level
Control or Professional Skill and contains exactly one matching folder with a
root `SKILL.md`. Foundation and Domain Skills never receive top-level zips.
The installer command validates the local bundles; it does not upload or
install them. These files are not evidence of official marketplace publication.

Builds, zip validation, quickstart, installer, and doctor results prove only
the declared local artifact contracts. They do not prove real-host Profile
startup, wall-clock performance, production accuracy, provider behavior, or
the installed user experience.

## Troubleshooting And Recovery

| Symptom | Safe recovery |
| --- | --- |
| `missing built runtime ...` | Run `python3 scripts/build.py`, then repeat the dry run. |
| Build directory is missing `.changeforge-build-manifest.json` or fails validation | Delete no target content. Re-run `python3 scripts/build.py`; never hand-author the manifest. |
| Doctor reports a legacy Runtime migration | Build, preview upgrade, and run upgrade directly; do not uninstall first. |
| `no rd-skills manifest found ...; run install first` during upgrade | Inspect the target. Use install only for a new target; otherwise back up pre-manifest artifacts and resolve each reported unmanaged conflict. |
| Permission denied | Stop. Choose `user`/`project`, correct ownership through the Host's approved process, or obtain authorization for Codex `admin`; do not use `--force` as a permission workaround. |
| Unsupported scope | Use the Host/scope matrix above. Only Codex supports `admin`; project installs require a project-root `--target`; OpenAI API uses zip output. |
| Doctor reports missing/stale files or bindings | Preserve the output, rebuild, preview upgrade, run it only with a valid manifest, then rerun doctor. |
| Unmanaged-name conflict | Inspect exact paths and ownership. Move or back up user-owned content, or use `--force` only after confirming replacement of those exact names. |

For migration-specific behavior and rollback, see [Migration to the hookless
architecture](MIGRATING_TO_HOOKLESS.md#rollback). For task requests after a
healthy install, continue to [Usage](USAGE.md).
