# ChangeForge Hook Runtime

ChangeForge Hook Runtime is an optional project-level reminder layer. It is not
a skill, does not replace `change-forge-router`, and does not read all compiled
skill references. Its job is to notice execution-time signals after tools run or
before an agent stops, then remind the agent to close the matching ChangeForge
gate.

## What ChangeForge Hook Runtime Does

The first-stage runtime provides three reminder gates:

- Post-Edit Structure Gate: runs after edit tools and warns when changed paths
  look like structural code, shared utilities, public interfaces, SDK/client
  code, adapters, dependency files, or new service/repository/helper-style files.
- Risk Surface Gate: runs after edit tools and shell commands and warns when
  paths or commands touch auth, data contracts, cache, queue, Kubernetes, Helm,
  or big-data surfaces.
- Stop Closure Gate: runs before final handoff and reminds the agent to include
  skill path, changed files, validation evidence, residual risk, and next steps.

The default behavior is warning-only. A hook failure must fail open and must not
interrupt normal agent execution.

## Why Hooks Do Not Replace change-forge-router

`change-forge-router` remains the semantic entry point for classifying a request,
selecting skills, choosing capabilities, escalating risk, and defining quality
gates. Hooks run after execution signals appear. They do not choose a complete
route, do not create professional skills, and do not load every `references/`
file.

Use hooks as a guardrail for missed execution-time evidence, not as a planning
system.

## Supported Runtimes

First-stage build output supports project scope only:

- Codex project hooks: `dist/codex/project/.codex`
- Claude project hooks: `dist/claude/project/.claude`

User and admin hook scopes are intentionally out of scope for the first stage.

## Hook Modes

Set `CHANGEFORGE_HOOK_MODE` to control runtime behavior:

- `off`: do nothing.
- `monitor`: update per-turn state without emitting reminders.
- `warn`: emit reminders and continue. This is the default.
- `block`: emit a block decision. This mode is reserved for controlled rollout
  after warning behavior is stable.

## Build Hooks

Build any runtime profile. Hook artifacts are profile-independent and are
refreshed by each build:

```bash
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
```

Expected project hook outputs:

```text
dist/codex/project/.codex/hooks.json
dist/codex/project/.codex/.changeforge-hook-manifest.json
dist/codex/project/.codex/hooks/changeforge_common.py
dist/codex/project/.codex/hooks/changeforge_post_edit_structure_gate.py
dist/codex/project/.codex/hooks/changeforge_risk_surface_gate.py
dist/codex/project/.codex/hooks/changeforge_stop_closure_gate.py

dist/claude/project/.claude/settings.changeforge-hooks.fragment.json
dist/claude/project/.claude/.changeforge-hook-manifest.json
dist/claude/project/.claude/hooks/changeforge_common.py
dist/claude/project/.claude/hooks/changeforge_post_edit_structure_gate.py
dist/claude/project/.claude/hooks/changeforge_risk_surface_gate.py
dist/claude/project/.claude/hooks/changeforge_stop_closure_gate.py
```

Do not install `src/hook-runtime` directly.

## Manually Enable Hooks

First-stage hook support is build-only. Installer integration is deferred, so
manual enablement must be deliberate:

1. Build the selected profile.
2. Review the generated files under `dist/codex/project/.codex` or
   `dist/claude/project/.claude`.
3. Copy the generated hook scripts into the target project's matching hook
   directory.
4. Merge hook configuration with any existing project hook configuration.
5. For Claude, use the generated settings fragment instead of overwriting an
   existing `.claude/settings.json`.

Do not overwrite existing project hook configuration without reviewing user
hooks first.

## Codex Activation Checklist

1. Copy `dist/codex/project/.codex` into the target repository root.
2. Run `/hooks` in Codex.
3. Confirm the project hook is listed.
4. Trust the hook after reviewing the command.
5. Confirm `[features].hooks` is not disabled.
6. Set `CHANGEFORGE_HOOK_DEBUG=1` for troubleshooting.
7. Trigger an `apply_patch` or `Bash` tool call.
8. Inspect `${XDG_CACHE_HOME:-~/.cache}/changeforge/hooks/<repo_hash>/debug.log`.

Codex `PostToolUse` ignores plain text stdout. ChangeForge hooks therefore emit
JSON with `hookSpecificOutput.additionalContext`.

Codex `Stop` requires JSON stdout. Closure Gate uses JSON output and only uses
continuation behavior when `CHANGEFORGE_HOOK_MODE=block`.

## Validate Hooks

Run the hook validator after routing evaluation and before build validation:

```bash
python3 scripts/eval-routing.py
python3 scripts/validate-hooks.py
python3 -m unittest discover -s tests
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
python3 scripts/validate-installation.py
```

`validate-hooks.py` checks script presence, Python compilation, template JSON,
required hook events, timeout limits, Codex command protocol, Codex JSON warning
output, Stop output separation, no direct `src/` hook commands, no user-specific
absolute paths, no network imports, and no project-source writes. The `unittest`
command exercises hook behavior fixtures and must discover the hook runtime tests
from the repository-level `tests` directory.

## Troubleshooting

If hooks do not run, confirm the generated command path matches the target
project hook directory and that the target runtime has approved or trusted
project hooks where required.

If Codex hooks appear inactive:

1. Run `/hooks` inside Codex.
2. Confirm the project hook is listed.
3. Confirm the project hook is trusted.
4. Set `CHANGEFORGE_HOOK_DEBUG=1`.
5. Trigger an `apply_patch` or `Bash` action.
6. Inspect `~/.cache/changeforge/hooks/<repo_hash>/debug.log`.

If reminders appear stale, remove the per-turn state cache for the project:

```text
${XDG_CACHE_HOME:-~/.cache}/changeforge/hooks/<repo_hash>/current-turn.json
```

If a hook crashes, it should emit a warning and continue. Treat hook crashes as
validator or implementation bugs, not as agent task failures.

## False Positive Handling

A reminder is not a verdict. If the hook over-matches a file or command, state
the rationale in the final handoff and continue. Prefer improving the matching
rules with a fixture-backed test over suppressing a whole risk family.

Useful false-positive evidence includes:

- changed path or command that triggered the hook
- why the suggested gate is not applicable
- expected gate behavior
- a focused fixture or unit test that captures the case

## Future Plugin Packaging

Future phases may add installer, upgrade, doctor, and plugin packaging support.
Those phases must merge hook configuration rather than overwrite it, preserve
user hooks, and keep project scope separate from user/admin scopes unless a
maintainer explicitly accepts the broader blast radius.
