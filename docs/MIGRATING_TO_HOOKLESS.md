# Migrating to the Hookless Architecture

rd-skills installs one Runtime of standard Skills, four static Agent Profiles
where supported, and manifests. It does not install executable interception,
an internal task context engine, private evidence storage, role-projection
packages, or a runtime state machine.

## Before Upgrade

1. Record the Host, scope, target, and current manifest.
2. Make an independent backup of user-owned Skills and Host configuration when
   required by local policy.
3. Build the current Runtime.
4. Preview upgrade against the existing installation. Do not uninstall a
   historical `recommended`, `full`, or `dev` installation first.

```bash
python3 scripts/build.py
python3 installers/upgrade.py --agent codex --scope user --dry-run
```

## Upgrade

```bash
python3 installers/upgrade.py --agent codex --scope user
python3 installers/doctor.py --agent codex --scope user
```

The upgrader validates the exact current 26-Skill manifest and the closed
historical 27/40/190 manifest generation. Every historical profile contains
the retired managed `routing-quality-review` Skill; a historical `full`
manifest also contains managed top-level Domain Skills, and a historical `dev`
manifest contains managed top-level Foundation and Domain Skills. Upgrade
removes those managed directories and writes the one 26-Skill Runtime manifest
without an intermediate uninstall. These historical identities are migration
inputs, not supported build or discovery choices.

The historical generation is embedded in the installer with fixed fingerprints
for the unchanged layers. Runtime migration does not require `.git` history and
does not infer an old managed set from arbitrary current Registry contents. All
five manifest inventory fields must identify the same supported generation; a
forged, partial, duplicate, unsafe, or hybrid inventory fails before mutation,
including with `--force`.

Upgrade must complete its managed-content backup before any live mutation. It
preserves unrelated top-level user files and Skill directories in place. A user
file placed inside a managed Skill directory is part of that managed directory:
it is copied into the backup, then the directory is replaced. Restore such a
mixed-in file selectively from the printed backup path after verifying its
ownership and destination.

The operation is not crash-atomic across cleanup, Skill replacement, Agent
Profile replacement, and manifest write. If interrupted, stop further writes,
inspect the newest `upgrade-*` directory under `.changeforge-backups/`, compare
its `skills/`, `profiles/`, and optional `legacy/` contents with the target, and
restore only verified paths. rd-skills has no automatic restore command.

## Behavioral Changes

- The Host discovers only 1 Control and 25 Professional Skills.
- Foundation guidance is a capability modifier; Domain guidance is
  `modifier-only`. Neither is a top-level Runtime Skill.
- Main fixes the Primary Professional route once. Task and Review do not rerun
  global routing.
- Each task opens zero to three selector-chosen Layer 3 items and only required
  Targeted References; complete catalogs are never loaded.
- Validation follows the final material edit, and independent review examines
  the actual bounded change evidence.

## Rollback

Use the upgrade backup or a previously built release artifact and its matching
manifest. Restore only verified managed paths; do not overwrite unrelated Host
content with the backup root. If rollback would reintroduce executable
interception, private state, or retired top-level Layer 3 discovery, treat it as
an explicit release decision rather than current supported behavior.
