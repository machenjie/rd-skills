# Installation

ChangeForge installs only built runtime artifacts from `dist/`. Source folders under `src/`, raw registries, and source foundation capability trees are authoring inputs and are never installed directly.

## Profiles

- `recommended`: 21 professional skills as top-level runtime skills. 136 foundation capabilities are compiled into professional skill references.
- `full`: 21 professional skills plus 7 domain extensions as top-level runtime skills. 136 foundation capabilities remain compiled references.
- `dev`: 21 professional skills plus 136 foundation capabilities plus 7 domain extensions as top-level skills. Use only for ChangeForge authoring/debugging.

Top-level runtime counts are `recommended` = 21, `full` = 28, and `dev` = 164.

`SKILL.md` is loaded when a skill is selected. Compiled `references/` are not fully loaded automatically; the router selects capabilities and professional skills read only selected references according to L1/L2/L3/L4/L5 policy.

Language capabilities are professional engineering rules, not language tutorials or personal technical asset mappings.

Build the profile before installing it:

```bash
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
```

## Supported Targets

- Codex project: `<target>/.agents/skills`
- Codex user: `~/.agents/skills`
- Codex admin: `/etc/codex/skills`
- Claude Code project: `<target>/.claude/skills`
- Claude Code user: `~/.claude/skills`
- GitHub Copilot project: `<target>/.github/skills`
- GitHub Copilot user: `~/.copilot/skills`
- Cline project: `<target>/.cline/skills`
- Cline user: `~/.cline/skills`
- OpenAI API: profile-scoped zip bundles under `dist/openai-api/zips/<profile>`

For project installs, `--target` is the project root. For user and admin installs, omitting `--target` uses the default skills directory; supplying `--target` treats it as an explicit skills directory override.

## Hook Runtime Defaults

Builds also emit hook artifacts for Codex, Claude, and Copilot, project and
user scope:

- Codex project hook runtime: `dist/codex/project/.codex`
- Codex user hook runtime: `dist/codex/user/.codex`
- Claude project hook fragment and scripts: `dist/claude/project/.claude`
- Claude user hook fragment and scripts: `dist/claude/user/.claude`
- Copilot project hook config and scripts: `dist/copilot/project/.github`
- Copilot user hook config and scripts: `dist/copilot/user/.copilot`

The hook runtime is not a skill and does not replace `change-forge-router`.
For supported Codex, Claude, and Copilot project/user installs, hooks now
install by default in the strongest supported mode. Existing hook configuration
is always preserved. Pass `--without-hooks` to opt out of executable hooks and
professional injection runtime. `--with-hooks` remains accepted for backward
compatibility, but it is no longer required.

Codex and Claude wire a per-prompt route reminder (`UserPromptSubmit`),
professional injection, SDD material choice gate, pre-edit risk preview
(`PreToolUse`), structure/risk gates after edits (`PostToolUse`), subagent
preflight (`SubagentStart`), subagent closure reminder (`SubagentStop`), and
Stop gates. Codex and Claude block SDD material choice and pre-edit structure
by default where supported. Stop closure is advisory by default: it records
missing route/stage/validation/review evidence as closure risk and telemetry
facts, but it does not force continuation or block final handoff unless a
maintainer explicitly overrides the policy. Hook runtime failures still fail
open unless explicitly configured fail-closed.
Claude commands explicitly set `CHANGEFORGE_AGENT=claude` and use 10-second
`timeout` values because Claude Code measures timeout in seconds. Copilot local
hooks wire only `SessionStart`, `SubagentStart`, `PostToolUse`, and `Stop`, so
Copilot receives SessionStart/SubagentStart/PostToolUse context and Stop
closure compensation where supported. Stop closure remains advisory by default
and records missing evidence as closure risk; Copilot cannot enforce
Codex/Claude-style PreToolUse gates. The shared scripts recognize Codex,
Claude, and VS Code Copilot tool names.

Cline, Roo, and OpenHands support is staged adapter support, not executable
hook support. Cline can install skills into `.cline/skills`; Roo mode-policy
and OpenHands backend-protocol adapters report unsupported lifecycle checks as
degraded residual risk until deterministic runtime templates or backend wiring
are added.

Project hooks install under the project root and resolve their command path from
the git root. User hooks install under the agent home (`~/.codex`, `~/.claude`,
`~/.copilot`), apply to every project, and resolve their command path from
`${CODEX_HOME:-$HOME/.codex}` / `${CLAUDE_CONFIG_DIR:-$HOME/.claude}` /
`${HOME}/.copilot`; for user scope `--target` does not relocate the hooks. VS
Code Copilot loads every `*.json` in its hook folder, so the managed config is a
dedicated `changeforge-hooks.json` and the scripts live in a `changeforge/`
subfolder.

```bash
# Codex user hooks apply to every Codex project by default:
python3 installers/install.py --agent codex --scope user --profile full
# Claude user hooks:
python3 installers/install.py --agent claude --scope user --profile full
# Copilot project hooks (.github/hooks) and user hooks (~/.copilot/hooks):
python3 installers/install.py --agent copilot --scope project --target /path/to/project --profile full
python3 installers/install.py --agent copilot --scope user --profile full
# Explicit opt-out:
python3 installers/install.py --agent codex --scope user --profile full --without-hooks
```

The route-preflight guidance also ships as an advisory fragment for users who
prefer not to trust an executable hook. Install only that fragment for any
project with `installers/install.py --with-bootstrap`, and inspect it with
`installers/doctor.py --check-bootstrap`.

`scripts/quickstart.py` exposes this choice through
`--activation-level none|bootstrap|hooks|professional-injection` and
`--without-hooks`. Hook-capable project/user scopes default to
`professional-injection`. `--activation-level none` and `--without-hooks` opt
out. `--activation-level bootstrap` installs only the non-executable
route-preflight fragment and skips hooks.

To downgrade runtime enforcement without uninstalling hooks:

```text
CHANGEFORGE_SDD_CHOICE_MODE=warn
CHANGEFORGE_SDD_CHOICE_MODE=off
CHANGEFORGE_PRE_EDIT_MODE=warn
CHANGEFORGE_STOP_MODE=warn
CHANGEFORGE_HOOK_MODE=warn
```

See [HOOKS.md](HOOKS.md) for hook modes, the session bootstrap, validation,
enablement, and troubleshooting.

## Codex

```bash
python3 installers/install.py --agent codex --scope project --target /path/to/project --profile full --dry-run
python3 installers/install.py --agent codex --scope user --profile recommended --dry-run
python3 installers/install.py --agent codex --scope admin --target /etc/codex/skills --profile recommended --dry-run
```

Remove `--dry-run` after reviewing the target path and skill count. Use `--backup` when replacing an existing managed install.

## Claude Code

```bash
python3 installers/install.py --agent claude --scope project --target /path/to/project --profile full --dry-run
python3 installers/install.py --agent claude --scope user --profile recommended --dry-run
```

## GitHub Copilot

```bash
python3 installers/install.py --agent copilot --scope project --target /path/to/project --profile full --dry-run
python3 installers/install.py --agent copilot --scope user --profile recommended --dry-run
```

## Cline

```bash
python3 installers/install.py --agent cline --scope project --target /path/to/project --profile full --dry-run
python3 installers/install.py --agent cline --scope user --profile recommended --dry-run
```

## OpenAI API Zip Packaging

`scripts/build.py` refreshes OpenAI API zips for the profile being built. `scripts/package.py` can package a previously built profile again:

```bash
python3 scripts/package.py --profile recommended
python3 installers/install.py --agent openai-api --profile recommended --dry-run
```

OpenAI API is zip-only; it does not install runtime skill folders into a project, user, or admin directory. Each zip contains exactly one top-level skill folder and exactly one root `SKILL.md`.

## Uninstall, Upgrade, And Doctor

Install writes `.changeforge-install-manifest.json` into the target skills directory. The manifest records `installed_professional_skills`, `installed_foundation_capabilities`, `installed_domain_extensions`, and `installed_skills` as the complete managed union. Uninstall removes only names listed in this manifest and then removes the manifest. For user and admin scopes, omit `--target` to use the same default skills directory as install; pass `--target` only to override the exact skills directory:

```bash
python3 installers/uninstall.py --agent codex --scope project --target /path/to/project --dry-run
python3 installers/uninstall.py --agent codex --scope project --target /path/to/project
python3 installers/uninstall.py --agent codex --scope user --dry-run
python3 installers/uninstall.py --agent codex --scope user
```

Upgrade backs up the existing ChangeForge-managed directories, replaces managed names from the selected built profile, preserves unrelated skills, and reports source/profile/skill version changes:

```bash
python3 installers/upgrade.py --agent codex --scope project --target /path/to/project --profile full --dry-run
```

Doctor checks supported directories, missing `SKILL.md`, duplicate skill names across scopes, old source versions, manifest drift, and profile mismatches:

```bash
python3 installers/doctor.py --agent codex --scope project --target /path/to/project --profile full
```

Doctor also prints source governance status for the skill and capability
registries, source/dist boundary, hook adapter matrix, Validation Broker,
Project Memory, repository graph freshness support, and skill-efficacy fixtures.
It is structural and does not run expensive test suites. See
[VALIDATION.md](VALIDATION.md) for the canonical validation tiers.

## Duplicate Skill Conflicts

Install refuses to overwrite an unmanaged skill directory whose name matches a ChangeForge skill. Review the conflict first, then either move the unmanaged directory, uninstall the managed copy, or rerun install with `--force` when replacing that directory is intentional.

## Final Smoke Checks

Before release handoff, run these smoke checks against disposable targets:

```bash
python3 installers/install.py --agent codex --scope user --target /tmp/changeforge-recommended-user-smoke --profile recommended
python3 installers/install.py --agent codex --scope project --target /tmp/changeforge-full-project-smoke --profile full
python3 installers/uninstall.py --agent codex --scope project --target /tmp/changeforge-full-project-smoke --dry-run
python3 installers/doctor.py --agent codex --scope user --target /tmp/changeforge-recommended-user-smoke --profile recommended
python3 installers/doctor.py --agent codex --scope project --target /tmp/changeforge-full-project-smoke --profile full
python3 installers/install.py --agent claude --scope project --target /tmp/changeforge-claude-full-smoke --profile full
python3 installers/doctor.py --agent claude --scope project --target /tmp/changeforge-claude-full-smoke --profile full
python3 installers/uninstall.py --agent claude --scope project --target /tmp/changeforge-claude-full-smoke --dry-run
python3 installers/install.py --agent copilot --scope project --target /tmp/changeforge-copilot-full-smoke --profile full
python3 installers/doctor.py --agent copilot --scope project --target /tmp/changeforge-copilot-full-smoke --profile full
python3 installers/uninstall.py --agent copilot --scope project --target /tmp/changeforge-copilot-full-smoke --dry-run
python3 installers/install.py --agent openai-api --profile recommended --dry-run
python3 scripts/validate-installation.py
```

The Codex recommended user install smoke should report 21 top-level skills. The Codex, Claude Code, and GitHub Copilot full project install smokes should each report 28 top-level skills. Uninstall dry-runs should operate only on manifest-managed names, doctor should report no issues for every installed smoke target, and OpenAI API zip validation should pass profile count and archive-shape checks.
