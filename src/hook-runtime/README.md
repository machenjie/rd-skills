# ChangeForge Hook Runtime

ChangeForge Hook Runtime is not a skill.
It does not replace change-forge-router.
It adds execution-time reminders across the agent lifecycle: at session and
subagent start, per user prompt, before and after tools run, and before the
agent or a subagent stops.
Codex and Claude default to warn, not block. Copilot local hooks default to a
strict Stop closure gate while keeping context hooks advisory.

The hook runtime is a small project-level reminder layer for agent execution. It
does not route work, does not read all skill references, and does not become a
professional skill. The router remains the semantic source of truth for selecting
ChangeForge skills, capabilities, domain extensions, and quality gates.

## Scope

The runtime provides these reminder hooks:

- Session Bootstrap: at `SessionStart` (Codex, Claude, and Copilot, including
  the Codex `compact` source) and `SubagentStart`, remind the agent to run a
  `change-forge-router` preflight before engineering work. Copilot also receives
  the static ChangeForge skill summary as top-level `additionalContext` for
  these two events. Also ships as an advisory install-time fragment.
- Route Reminder: at Codex and Claude `UserPromptSubmit`, add a concise
  per-prompt reminder to route and emit a `changeforge_route` manifest. It
  reminds the agent to
  clarify requirements before action, inspect target-project code before
  planning, name TDD or validation evidence before implementation, assign
  action-specific owner and independent review skills, repair/re-review findings,
  and hand off with validation evidence and residual risk. Never reads or records
  the prompt text.
- Pre-Edit Risk Preview: at Codex and Claude `PreToolUse`, preview risk surfaces
  before an edit or command runs. Advisory only; never denies the tool call.
  Copilot templates do not wire `PreToolUse` because Copilot only consumes
  permission decisions or argument modifications for that event.
- Post-Edit Structure Gate: after edit tools run, detect structural code changes
  that should preserve reuse, placement, ownership, dependency direction, public
  API decisions, same-pattern scans, and nearby tests.
- Risk Surface Gate: after edit tools or shell commands run, detect high-risk
  surfaces such as auth, data contracts, cache, queue, Kubernetes, Helm, and big
  data work so the agent remembers the matching gate.
- Stop Closure Gate: before final handoff, remind the agent to include the
  ChangeForge path used, changed files, validation evidence, residual risk, and
  next actions.
- Subagent Closure Reminder: at Codex and Claude `SubagentStop`, remind the
  subagent to carry closure evidence back to the parent. Advisory only; never
  forces continuation and never touches the parent turn's closure state. Copilot
  templates do not wire `SubagentStop` because Copilot only consumes block/allow
  decision output for that event.

## Non-Goals

- Do not replace `change-forge-router`.
- Do not turn hooks into professional skills.
- Do not read every `references/` file.
- Do not read, record, log, or echo user prompt text.
- Do not choose the full route; the router remains the semantic source of truth.
- Do not block Codex or Claude by default. Copilot's strict Stop gate is an
  explicit local-hook policy for missing closure evidence.
- Do not install `src/hook-runtime` directly.
- Do not install `src/` or `src/registry` as runtime content.

## Runtime State

Per-turn state is stored outside the project source tree:

```text
${XDG_CACHE_HOME:-~/.cache}/changeforge/hooks/<repo_hash>/current-turn.json
```

If the cache cannot be written, hooks emit a warning and continue. Hook failures
must not interrupt normal agent execution.

## Build Output

`scripts/build.py` copies this runtime into project and user hook layouts:

```text
dist/codex/project/.codex
dist/codex/user/.codex
dist/claude/project/.claude
dist/claude/user/.claude
dist/copilot/project/.github
dist/copilot/user/.copilot
```

Project layouts resolve their command path from the project git root; user
layouts resolve it from the agent home (`${CODEX_HOME:-$HOME/.codex}`,
`${CLAUDE_CONFIG_DIR:-$HOME/.claude}`, `${HOME}/.copilot`). VS Code Copilot uses
the flat (matcher-less) hook config format with `version: 1` and `timeoutSec`
and loads every `*.json` in its hook folder, so its config is the dedicated
`changeforge-hooks.json` and the scripts, manifest, and bootstrap fragment live
in a `changeforge/` subfolder. Copilot context output is top-level
`additionalContext` for supported events; the Copilot Stop command sets
`CHANGEFORGE_HOOK_MODE=block` and emits top-level `decision`/`reason` only when
closure evidence is missing. Claude commands set `CHANGEFORGE_AGENT=claude` explicitly,
emit `hookSpecificOutput.additionalContext` for context-bearing events, and use
10-second `timeout` values because Claude Code measures timeout in seconds.
Each layout includes `.changeforge-hook-manifest.json` so installation
validation can prove which hook scripts and scope were emitted.

The installer can place these hooks for Codex, Claude, and Copilot project or
user scope with `installers/install.py --with-hooks`; existing hook
configuration is always preserved and hooks are never trusted automatically.

## Action-Aware Professional Injection

The hook runtime now adds an action-aware layer around the original reminders:

- `changeforge_action_classifier.py` classifies the current lifecycle stage
  (planning, read, edit, review, repair, test, permission, release, compaction,
  or subagent) and detects compact surface names only.
- `changeforge_skill_index.py` maps that stage and surface set to an owner
  professional skill, a separate reviewer skill, selected capability names,
  reference paths, and quality gates.
- `changeforge_runtime_adapters.py` isolates output protocol differences across
  Codex, Claude, Copilot, and generic text runtimes.
- `changeforge_professional_injector.py`, read/review/permission/compaction,
  and subagent gates update bounded cache-side state and emit advisory context.

The runtime stores only bounded facts such as stage, paths, skill names, gate
names, and compact signal names. It does not persist prompt text, secrets,
environment variables, full command arguments, command output, user archives, or
personal content indexes.

Additional install flags:

```bash
python3 installers/install.py --agent codex --scope project --target <repo> --with-hooks --professional-injection
python3 installers/install.py --agent codex --scope project --target <repo> --with-universal-bootstrap
python3 installers/install.py --agent copilot --scope project --target <repo> --with-hooks --with-copilot-instructions
```

`--professional-injection` implies hook installation. `--with-universal-bootstrap`
installs both the route preflight and professional bootstrap fragments under
`.changeforge/`. `--with-copilot-instructions` creates
`.github/copilot-instructions.md` only when that file does not already exist.
