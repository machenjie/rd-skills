# ChangeForge Hook Runtime

ChangeForge Hook Runtime is an optional project-level reminder layer. It is not
a skill, does not replace `change-forge-router`, and does not read all compiled
skill references. Its job is to notice signals at session start, after tools
run, or before an agent stops, then remind the agent to run a route preflight or
close the matching ChangeForge gate.

## What ChangeForge Hook Runtime Does

The first-stage runtime provides these reminder gates:

- Session Bootstrap (route preflight): runs at session start and reminds the
  agent to classify the change and run a `change-forge-router` preflight before
  engineering work, to require `implementation-structure-design` before new
  structure, and to bind any completion claim to `agent-execution-discipline`.
  It only emits a route preflight; it never selects a full route and never reads
  references. It is wired as a Claude `SessionStart` hook. Codex has no stable
  session-start hook, so Codex uses the install-time bootstrap fragment instead.

- Post-Edit Structure Gate: runs after edit tools and warns when changed paths
  look like structural code, shared utilities, public interfaces, SDK/client
  code, adapters, dependency files, or new service/repository/helper-style files.
  It also layers lightweight sub-gates that remind on new-file naming pattern
  mismatches against same-directory siblings, reuse-ladder evidence for
  helper/common/utils/shared/service/repository roles, extension-reuse safety
  when a patch modifies existing logic, advanced-refactor evidence when
  class/interface/inheritance/reflection keywords appear, and comment-quality
  evidence when exported/public declarations, test functions, or complex logic
  are added.
- Risk Surface Gate: runs after edit tools and shell commands and warns when
  paths or commands touch auth, data contracts, cache, queue, Kubernetes, Helm,
  or big-data surfaces.
- Stop Closure Gate: runs before final handoff and reminds the agent to include
  skill path, changed files, validation evidence, residual risk, next steps, and
  the structure-evidence records (file naming, reuse ladder, extension safety,
  advanced refactor, comment quality) for any structure sub-gate that fired.

The default behavior is warning-only. A hook failure must fail open and must not
interrupt normal agent execution.

## Telemetry

In addition to their reminders, all three gates append a small telemetry record
to the user cache after each watched event. Telemetry is a runtime fact log used
for offline review; it is never written into project source or `dist/`, and it
records no prompts, environment variables, secrets, or full command output. The
Stop Closure Gate records closure-completeness facts only: whether a
`changeforge_route` manifest, changed files, validation evidence, residual risk,
and required references were present.

Telemetry is enabled by default and can be disabled with `CHANGEFORGE_TELEMETRY=off`.
See [TELEMETRY.md](TELEMETRY.md) for the data model, the offline review tool, and
the human promotion workflow.

## Why Hooks Do Not Replace change-forge-router

`change-forge-router` remains the semantic entry point for classifying a request,
selecting skills, choosing capabilities, escalating risk, and defining quality
gates. Hooks run after execution signals appear. They do not choose a complete
route, do not create professional skills, and do not load every `references/`
file.

Use hooks as a guardrail for missed execution-time evidence, not as a planning
system.

## Session Bootstrap and Route Preflight

The session bootstrap is a route-preflight reminder, not a router and not a
planner. It tells the agent *when* to route, not *how* to route:

- A possible engineering change (code, review, debug, test, refactor, release,
  or skill authoring) triggers a `change-forge-router` preflight before acting.
- A change that adds or modifies a function, class, file, directory, helper,
  service, repository, adapter, or utility requires `implementation-structure-design`.
- A pending completion claim binds to `agent-execution-discipline`: no
  completion claim without fresh validation evidence and residual risk. A
  validation keyword is not evidence by itself; the closure needs the command
  plus an outcome, exit code, output, or artifact, and negative phrases such as
  `not verified` or `没有运行` stay non-evidence.
- An explicit, in-scope user skill path is respected without re-routing.
- Pure question, explanation, or translation needs no routing.

The bootstrap keeps the same precision discipline as the rest of ChangeForge: a
possible engineering change triggers a preflight, a confirmed risk, stage, or
surface signal selects the skill path, and deep rules load only the selected
references. It never loads every skill and never loads every reference.

Bootstrap boundaries:

- The bootstrap does not replace `change-forge-router`. It reminds the agent to
  run the router; the router still classifies the change and selects the path.
- The bootstrap is advisory. It never blocks execution and never overrides an
  explicit in-scope instruction.
- The bootstrap reads no references, calls no LLM, makes no network call, and
  writes no project source.

Runtime support:

- Claude project hooks wire the bootstrap as a `SessionStart` hook
  (`changeforge_session_bootstrap.py`).
- Codex has no stable session-start hook, so the same guidance ships as an
  install-time fragment (`changeforge-route-preflight.md`). Reference it from
  the project's agent instructions to enable it.
- Any runtime can install the advisory fragment with
  `installers/install.py --with-bootstrap`.

## Codex Post-Execution Limitation

Codex project hooks currently operate as execution-time guardrails. For Codex,
ChangeForge relies on PostToolUse and Stop reminders rather than assuming a
stable pre-edit planning hook. Therefore, hooks cannot replace upfront routing or
implementation structure planning. They can only detect edited paths, patch
signals, and missing closure evidence after execution has begun. The session
bootstrap is the route preflight reminder; for Codex it ships as an install-time
fragment rather than a SessionStart hook.

## Hook Capability Boundary

Hooks can:
- remind on route preflight at session start (Claude SessionStart);
- remind on new file naming pattern mismatches;
- remind on structural path changes;
- remind on helper/common/utils/shared pollution risk;
- remind on reuse ladder evidence;
- remind on extension reuse safety;
- remind on advanced refactor evidence;
- remind on comment quality evidence;
- remind on Stop-stage closure evidence.

Hooks cannot:
- replace `change-forge-router`;
- replace `implementation-structure-design`;
- call LLMs;
- perform whole-repository complex AST analysis;
- automatically rename files;
- modify project source;
- access the network;
- read every compiled reference;
- prove semantic correctness.

## Recommended Hook Rollout

1. Start with `CHANGEFORGE_HOOK_MODE=warn`.
2. Collect false positives with fixture-backed tests.
3. Only enable `block` for high-confidence violations:
   - new common/utils/helper file without reuse evidence;
   - dependency file changes without dependency review;
   - Stop without validation evidence;
   - Stop without residual risk.
4. Keep fail-open behavior for hook runtime errors.
5. Do not enable broad block mode until warning behavior is stable.

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
dist/codex/project/.codex/changeforge-route-preflight.md
dist/codex/project/.codex/hooks/changeforge_common.py
dist/codex/project/.codex/hooks/changeforge_session_bootstrap.py
dist/codex/project/.codex/hooks/changeforge_post_edit_structure_gate.py
dist/codex/project/.codex/hooks/changeforge_risk_surface_gate.py
dist/codex/project/.codex/hooks/changeforge_stop_closure_gate.py

dist/claude/project/.claude/settings.changeforge-hooks.fragment.json
dist/claude/project/.claude/.changeforge-hook-manifest.json
dist/claude/project/.claude/changeforge-route-preflight.md
dist/claude/project/.claude/hooks/changeforge_common.py
dist/claude/project/.claude/hooks/changeforge_session_bootstrap.py
dist/claude/project/.claude/hooks/changeforge_post_edit_structure_gate.py
dist/claude/project/.claude/hooks/changeforge_risk_surface_gate.py
dist/claude/project/.claude/hooks/changeforge_stop_closure_gate.py

dist/universal/bootstrap/changeforge-route-preflight.md
```

The Codex hooks ship the session bootstrap script too, but Codex does not wire a
`SessionStart` hook; Codex enables the route preflight through the advisory
fragment instead. Do not install `src/hook-runtime` directly.

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

## Installer-Assisted Hook Enablement

The installer can also place hooks for Codex and Claude **project** scope. Hooks
are never installed by default; they require `--with-hooks` and are written only
when neither `--dry-run` nor `--hooks-dry-run` is set. Existing project hook
configuration is always preserved.

```bash
python3 scripts/build.py --profile full
# Show the merge plan without writing anything:
python3 installers/install.py --agent codex --scope project --target /path/to/project --profile full --with-hooks --hooks-dry-run
# Write hook scripts and merge config (preserving existing hooks):
python3 installers/install.py --agent codex --scope project --target /path/to/project --profile full --with-hooks
# Inspect installed hooks:
python3 installers/doctor.py --check-hooks --target /path/to/project
# Install only the advisory route-preflight fragment (any project install, incl. Codex):
python3 installers/install.py --agent codex --scope project --target /path/to/project --profile full --with-bootstrap
# Inspect the advisory bootstrap fragment:
python3 installers/doctor.py --check-bootstrap --target /path/to/project
```

For Codex, the installer merges ChangeForge hook groups into an existing
`.codex/hooks.json` without removing user hooks. For Claude, it places
`settings.changeforge-hooks.fragment.json` and never modifies an existing
`.claude/settings.json`; merge the fragment's `hooks` into `settings.json` by
hand, including the `SessionStart` bootstrap entry. The `--with-bootstrap` option
writes only the advisory fragment to `.changeforge/changeforge-route-preflight.md`
and never installs executable hooks. The installer never trusts hooks
automatically.

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
python3 scripts/eval-agent-behavior.py
python3 -m unittest discover -s tests
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
python3 scripts/validate-installation.py
```

`validate-hooks.py` checks script presence, Python compilation, template JSON,
required hook events, the Claude `SessionStart` bootstrap wiring, the absence of
a Codex `SessionStart` hook, the advisory bootstrap fragment, timeout limits,
Codex command protocol, Codex JSON warning output, Stop output separation, no
direct `src/` hook commands, no user-specific absolute paths, no network
imports, and no project-source writes. The `unittest` command exercises hook
behavior fixtures and must discover the hook runtime tests from the
repository-level `tests` directory.

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
