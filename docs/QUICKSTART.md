# Quickstart

Use this when you want to understand, build, install, verify, and try ChangeForge in a few minutes. For the complete operating guide, see [USAGE.md](USAGE.md).

## 30 Seconds

ChangeForge Skill Mesh turns product and code changes into a routed professional workflow: clarify the request, inspect the target code before planning, define test or validation evidence, assign the right skill owner, review independently, repair and re-review when needed, then hand off with evidence and residual risk.

It is not a prompt dump. The system combines:

- `change-forge-router` for route selection and risk sizing.
- Professional skills for action ownership.
- Foundation capability references loaded precisely by route.
- Quality gates for security, reliability, delivery, tests, docs, and review.
- Default hooks for supported agents that inject professional context and block
  material SDD choices before mutation or handoff.

## Pick A Profile

| Profile | Choose It When | Top-Level Runtime Skills |
| --- | --- | --- |
| `recommended` | Default global/user install. | 21 professional skills |
| `full` | Project install where domain extensions should be visible. | 21 professional skills plus 7 domain extensions |
| `dev` | ChangeForge authoring/debugging only. | 21 professional skills plus 136 foundation capabilities plus 7 domain extensions |

`recommended` and `full` keep foundation capabilities inside professional skill `references/` so the selected route reads only the relevant references. They do not expose every foundation capability as a global top-level skill.

## Three Steps

For the shortest Codex user install, run one command:

```bash
python3 scripts/quickstart.py --agent codex --scope user
```

Dry-run the same path without writing:

```bash
python3 scripts/quickstart.py --agent codex --scope user --dry-run
```

Project installs default to the `full` profile and require `--target`:

```bash
python3 scripts/quickstart.py --agent claude --scope project --target /path/to/project
python3 scripts/quickstart.py --agent copilot --scope project --target /path/to/project
python3 scripts/quickstart.py --agent cline --scope project --target /path/to/project
```

Hook-capable Codex, Claude, and Copilot project/user quickstart installs default
to `professional-injection`: executable hooks are installed, professional
context is injected, and supported blocking gates run by default. Codex and
Claude block SDD material choice, pre-edit structure, process phase, and Stop
closure directly where supported. Copilot receives
SessionStart/SubagentStart/PostToolUse context and Stop closure compensation
where supported. Copilot cannot enforce Codex/Claude-style `PreToolUse` or
`SubagentStop` gates, so missing phase evidence is disclosed as degraded
enforcement. Use `--without-hooks` or
`--activation-level none` to opt out. Use `--activation-level bootstrap` when
you want only the non-executable
`.changeforge/changeforge-route-preflight.md` fragment:

```bash
python3 scripts/quickstart.py --agent codex --scope project --target /path/to/project --without-hooks
python3 scripts/quickstart.py --agent codex --scope project --target /path/to/project --activation-level bootstrap
```

OpenAI API zip output:

```bash
python3 scripts/quickstart.py --agent openai-api
```

`scripts/quickstart.py` orchestrates the existing build, installer, and doctor
commands. Its final summary prints the selected activation status as well as
the next prompt. It does not implement official marketplace installation.
The next prompt reminds you that hooks perform route, preflight, and material
choice checks by default, but you should still state business constraints and
design preferences clearly.

## Manual Path

1. Build the profile:

```bash
python3 scripts/build.py --profile recommended
```

2. Install into one runtime:

```bash
python3 installers/install.py --agent codex --scope user --profile recommended --dry-run
python3 installers/install.py --agent codex --scope user --profile recommended
```

3. Verify the install:

```bash
python3 installers/doctor.py --agent codex --scope user --profile recommended
```

Restart or reload the target runtime after installation if it was already open.

## Minimal Install Examples

Codex user install:

```bash
python3 scripts/quickstart.py --agent codex --scope user
```

Claude Code project install:

```bash
python3 scripts/quickstart.py --agent claude --scope project --target /path/to/project
```

GitHub Copilot project install:

```bash
python3 scripts/quickstart.py --agent copilot --scope project --target /path/to/project
```

Cline project install:

```bash
python3 scripts/quickstart.py --agent cline --scope project --target /path/to/project
```

OpenAI API zip bundles:

```bash
python3 scripts/quickstart.py --agent openai-api
```

## First Prompts

Unknown change:

```text
Use change-forge-router to classify this request, select the minimum sufficient ChangeForge skill path, and list the evidence gates before implementation.
```

Frontend form state change:

```text
Use frontend-change-builder and quality-test-gate for this form state change. Clarify acceptance criteria, inspect the existing component and tests before planning, then provide validation evidence and residual risk.
```

Backend API permission change:

```text
Use backend-change-builder, data-api-contract-changer, security-privacy-gate, and quality-test-gate for this API permission change. Include denied-path tests, object-level authorization risk, contract compatibility, and validation evidence.
```

Release or deployment review:

```text
Use delivery-release-gate and reliability-observability-gate to review this deployment plan. Check rollback, configuration, migration order, observability, and post-release validation evidence.
```

## Common Failures

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Runtime cannot see installed skills | Runtime was already open. | Restart or reload the target runtime. |
| Too many top-level skills in a user/global install | Installed `dev` or raw source content. | Use `recommended` and install from `dist/` only. |
| Foundation capabilities appear as top-level global skills | Wrong profile or wrong install source. | Rebuild/install `recommended` or `full`; do not install `src/`. |
| Hooks block for a design choice | Material SDD choice has no resolved user evidence. | Choose A/B or provide constraints, then record `resolution_evidence`. |
| Handoff claims completion without proof | Missing validation evidence. | Run the relevant validator/test/build/doctor command and include result plus residual risk. |

Material choice examples that require user resolution by default:

- New public API, export, interface, or protocol.
- New shared utility versus reusing an existing owner object.
- Inheritance versus composition, adapter, wrapper, factory, strategy, plugin, or registry.
- Schema, migration, rollback, security, auth, permission, tenant, privacy, payment, or irreversible operation.

Examples that should not require a choice:

- Typo, formatting, or docs-only edits.
- Local reversible same-file fixes that follow repository convention.
- Prompts, fixtures, or existing owner conventions that already specify the only valid design.

## Next

- Full usage: [USAGE.md](USAGE.md)
- Hook behavior: [HOOKS.md](HOOKS.md)
- Benchmarks: [BENCHMARKS.md](BENCHMARKS.md)
- Scorecard: [SCORECARD.md](SCORECARD.md)
- Marketplace index: [MARKETPLACE.md](MARKETPLACE.md)
