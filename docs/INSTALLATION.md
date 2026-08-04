# Installation

Install only generated artifacts under `dist/`. Never copy `src/`, source
registries, reports, or personal content into an agent configuration. Run all
commands from the repository root with Python 3.11 or newer after
`python3 -m pip install .`.

For the shortest build/install/doctor path, start with [Quickstart](QUICKSTART.md).

## Build

Build the profile you intend to install:

```bash
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
```

You normally need only one command. The `recommended`, `full`, and `dev`
profiles contain 27, 40, and 190 top-level Skills respectively. [Build
profiles](BUILD_PROFILES.md) owns composition, compiled Layer 3 behavior,
supported-host Agent Profile output, and manifest fields. Every runtime
installer validates the built manifest before changing its target.

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
| OpenAI API | zip output only | `dist/openai-api/zips/<profile>/` | none |

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
  --profile recommended --dry-run
python3 installers/install.py \
  --agent codex --scope project --target /absolute/path/to/project \
  --profile recommended
```

User installation needs no target when the default is correct:

```bash
python3 installers/install.py \
  --agent claude --scope user --profile recommended --dry-run
python3 installers/install.py \
  --agent claude --scope user --profile recommended
```

The installer rejects unmanaged artifacts whose names collide with incoming
ChangeForge artifacts. Inspect every reported path before considering
`--force`. Use `--force` only when you have confirmed that replacing those
specific unmanaged same-name artifacts is intended and have a separate
recovery copy. It does not bypass source validation, path-overlap protection,
unsupported scopes, or unsafe names.

Optional install `--backup` copies only the ChangeForge-named incoming/previously
managed paths, the install manifest, and bounded known legacy paths that already
exist. It is stored under the Skill target's `.changeforge-backups/` directory.
It is not a snapshot of the full host configuration.

## Doctor

```bash
python3 installers/doctor.py \
  --agent codex --scope user --profile recommended
```

Doctor checks the installed manifest, expected top-level Skill count, root
`SKILL.md` files, current build/core/source bindings, legacy residue, and the
host-specific Agent Profile contract. Codex, Claude, and Copilot must have the
exact four-profile set; Cline correctly has no native profiles. Doctor also
prints declared host enforcement and its limitations. This is repository-level
artifact evidence, not proof of real-host startup.

## Upgrade

Build the target profile first, then preview and run upgrade:

```bash
python3 scripts/build.py --profile recommended
python3 installers/upgrade.py \
  --agent codex --scope user --profile recommended --dry-run
python3 installers/upgrade.py \
  --agent codex --scope user --profile recommended
```

Upgrade requires an existing ChangeForge install manifest. It automatically
backs up the currently managed Skills, managed Profile files, manifest, and
bounded known legacy paths before replacement when any exist. It removes only
manifest-owned or bounded legacy artifacts and preserves unrelated content.

ChangeForge has no automatic restore CLI. Install creates a backup only when
`--backup` was requested and matching content already exists; upgrade creates
one when matching managed or legacy content exists. If a successful command
prints a backup path, use it; the new manifest records the same path. If an
operation was interrupted before that output or manifest write, stop further
writes and inspect the Skill target's `.changeforge-backups/` directory for a
newly created `install-*` or `upgrade-*` backup instead of assuming none exists.

Compare any candidate backup's `skills/`, `profiles/`, and optional `legacy/`
contents with the target, then restore only verified files through your normal
filesystem or configuration-management process. Do not copy the backup root
wholesale over unrelated host content. If no usable backup exists, resolve the
failure cause, rebuild the intended profile, preview the install or upgrade
appropriate to the remaining manifest, and run it only when safe; otherwise
restore from your own verified backup.

## Uninstall

```bash
python3 installers/uninstall.py --agent codex --scope user --dry-run
python3 installers/uninstall.py --agent codex --scope user
```

Uninstall removes only files declared by the ChangeForge manifest plus bounded
known legacy artifacts. It does not remove unrelated user content or restore a
backup automatically.

## OpenAI API Zip Output

Generate and then validate the `recommended` zip set exactly as follows:

```bash
python3 scripts/build.py --profile recommended
python3 installers/install.py --agent openai-api --profile recommended
```

The build writes 27 zip files under `dist/openai-api/zips/recommended/`. Use
`full` or `dev` in both commands for their 40 or 190 files. The three profiles
therefore contain 257 zip files in total. Each zip is named
for one top-level Skill and contains exactly one matching top-level Skill folder
with a root `SKILL.md`. The second command validates the local bundles; it does
not upload or install them. These files are not evidence of official marketplace
publication.

The obsolete mobile Domain and compatibility mode have been removed. Removed
legacy Skill ids are unsupported and are not redirected. See [Build
profiles](BUILD_PROFILES.md) for current platform routing.

Builds, zip validation, quickstart, installer, and doctor results prove only
the declared local artifact contracts. They do not prove real-host Profile
startup, wall-clock performance, production accuracy, provider behavior, or
the installed user experience.

## Troubleshooting And Recovery

| Symptom | Safe recovery |
| --- | --- |
| `missing built profile ...` | Run `python3 scripts/build.py --profile <profile>` with `<profile>` replaced by `recommended`, `full`, or `dev`, then repeat the dry run. |
| Build directory is missing `.changeforge-build-manifest.json` or fails validation | Delete no target content. Re-run the build for the same profile so the generator recreates the directory and manifest; never hand-author the manifest. |
| `no ChangeForge manifest found ...; run install first` during upgrade | Inspect the target. If this is a new target, use install. If artifacts predate the manifest, back them up, preview install, and resolve any named unmanaged conflicts explicitly. |
| Permission denied | Stop. Choose `user`/`project`, correct ownership through the host's approved process, or obtain authorization for Codex `admin`; do not use `--force` as a permission workaround. |
| Unsupported scope | Use the host/scope matrix above. Only Codex supports `admin`; project installs require a project-root `--target`; OpenAI API uses zip output. |
| Doctor reports missing/stale files or bindings | Preserve its output, rebuild the same profile, preview upgrade, run upgrade only if the manifest is present, then rerun doctor. If the manifest is absent, follow the missing-manifest row. |
| Unmanaged-name conflict | Inspect the exact paths and ownership. Move or back up user-owned content, or use `--force` only after confirming replacement of those exact names is intended. |

For migration-specific legacy behavior and rollback, see [Migration to the
hookless architecture](MIGRATING_TO_HOOKLESS.md#rollback). For task requests
after a healthy install, continue to [Usage](USAGE.md).
