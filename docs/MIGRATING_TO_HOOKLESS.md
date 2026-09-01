# Migrating to the Hookless Architecture

Use this guide only when doctor or upgrade identifies an older rd-skills installation, or when you need to recover or roll back an interrupted migration. New installations should use [Quickstart](QUICKSTART.md).

Current rd-skills installs generated Skill files, four static Agent Profile files where the host supports them, and an ownership manifest. It does not install executable interception, a private state store, a hidden task engine, or a second workspace manager.

## Historical installations

The upgrader recognizes only these closed historical generations:

- the earlier 27-Skill `recommended` manifest;
- the retired 40-Skill `full` manifest; and
- the retired 190-Skill `dev` manifest.

Every recognized historical generation contains the retired managed `routing-quality-review` Skill. Historical `full` also contains managed top-level Domain Skills. Historical `dev` contains managed top-level Foundation and Domain Skills.

These identities are migration inputs, not supported build, install, or discovery choices. The historical bridge is embedded installation metadata with fixed layer fingerprints. It does not read Git history or infer ownership from arbitrary current registries.

All five manifest inventory fields must identify the same supported generation. A forged, partial, duplicate, unsafe, or current/historical hybrid inventory fails before backup or mutation, including when `--force` is present.

## Before upgrade

1. Record the tool, scope, target, and current manifest location.
2. Make an independent backup of user-owned Skills and surrounding host configuration when local policy requires it.
3. Build the current checkout.
4. Preview upgrade against the existing installation.
5. Do not uninstall a historical installation first.

```bash
python3 scripts/build.py
python3 installers/upgrade.py --agent codex --scope user --dry-run
```

Inspect every reported path. Stop if the tool, scope, target, ownership, or expected removal differs from the installation you intend to migrate.

## Upgrade

```bash
python3 installers/upgrade.py --agent codex --scope user
python3 installers/doctor.py --agent codex --scope user
```

Upgrade removes only the managed directories declared by an accepted historical manifest and writes the current fixed manifest. It does not require an intermediate uninstall.

Before cleanup or replacement, upgrade creates a complete backup of managed Skill directories, managed Agent Profile files, the manifest, and bounded known legacy paths. If the backup cannot complete, target mutation does not start.

Unrelated top-level user files and Skill directories remain in place. Content placed inside a managed Skill directory belongs to that directory for replacement purposes: it is copied into the backup, then the managed directory is replaced. Restore a mixed-in user file selectively only after verifying its ownership and destination.

## If upgrade is interrupted

Upgrade is not crash-atomic across cleanup, Skill replacement, Agent Profile replacement, and final manifest write.

If interruption occurs after backup creation:

1. stop all further writes to the target;
2. locate the newest `upgrade-*` directory below the Skill target's `.changeforge-backups/` directory;
3. compare its `skills/`, `profiles/`, and optional `legacy/` contents with the current target;
4. identify which managed operations completed; and
5. restore only verified files through the normal filesystem or configuration-management process.

rd-skills has no automatic restore CLI. If no usable backup exists, stop rather than inferring ownership.

## What changes after migration

- Retired managed top-level guidance directories are removed from host discovery.
- Current tasks choose their professional guidance once and load only the focused supporting material needed for the request.
- Validation follows the final material edit.
- A separate reviewer checks the actual bounded change.
- Executable interception and private runtime state are not restored.

These are internal delivery changes. Everyday use remains a natural-language request beginning with the host-native invocation in the [Quickstart table](QUICKSTART.md#host-invocation); see [Usage](USAGE.md).

## Rollback

Use the printed upgrade backup or a previously built release artifact with its matching manifest. Restore only verified managed paths. Do not copy the backup root over unrelated host content.

If rollback would reintroduce executable interception, private state, retired top-level discovery, or a historical manifest not accepted by the current installer, treat it as an explicit release and security decision rather than a normal recovery step.

After restoration, rerun doctor for the same tool, scope, and target. Doctor verifies installed artifacts; it does not prove a live host loaded them.

For target paths, permissions, uninstall, and general recovery, return to [Advanced Installation & Recovery](INSTALLATION.md#troubleshooting-and-recovery).
