# Migrating to the Hookless Architecture

ChangeForge now installs only standard Skills, four static Agent Profiles where supported, and manifests. The product no longer relies on executable interception, an internal task context engine, private evidence storage, role-projection packages, internal task identities, digests, lifecycle protocols, or phase state.

## Before Upgrade

1. Record the currently installed ChangeForge profile and target.
2. Back up user-owned Skills and agent configuration if local policy requires it.
3. Build the desired new profile.
4. Preview the upgrade.

```bash
python3 scripts/build.py --profile recommended
python3 installers/upgrade.py \
  --agent codex --scope user --profile recommended --dry-run
```

## Upgrade

```bash
python3 installers/upgrade.py \
  --agent codex --scope user --profile recommended
python3 installers/doctor.py \
  --agent codex --scope user --profile recommended
```

The upgrader removes only known ChangeForge-managed legacy artifacts and manifest-owned files. Unrelated user Skills, agents, and configuration must remain. If doctor reports unknown residue, inspect it before deletion rather than widening cleanup rules.

## Behavioral Changes

- The main agent dispatches only; it does not fall back to implementation.
- Direct Tasks start a task agent after one classification.
- Complex or risky work starts one analysis pass and prioritizes the First Executable Slice.
- Each task loads one primary Professional Skill and only triggered Layer 3 Skills.
- Validation is run by the task agent. Independent implementation review
  examines the actual diff and all changed files; pre-implementation review
  examines its bounded artifact, criteria, and supporting evidence.
- Repair is followed by fresh validation and re-review.
- Handoffs use Markdown and observable evidence.

## Rollback

Use a previously built release artifact and its installer manifest. Do not restore only part of the old control machinery. If rollback would reintroduce executable interception or private state, treat that as an explicit release decision and document its risk rather than presenting it as the current architecture.
