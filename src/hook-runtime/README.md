# ChangeForge Hook Runtime

ChangeForge Hook Runtime is not a skill.
It does not replace change-forge-router.
It adds execution-time reminders across the agent lifecycle: at session and
subagent start, per user prompt, before and after tools run, and before the
agent or a subagent stops.
Supported default blocking covers high-confidence SDD material choice,
pre-edit structure, process phase, and Stop closure gates where the adapter has
the required hard-decision event. Unsupported adapters degrade explicitly
instead of claiming full enforcement, and ordinary advisory context remains
warning only.

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
- Pre-Edit Implementation Structure Gate: at Codex and Claude `PreToolUse`,
  check structural edit tools for read evidence and a
  `changeforge_implementation_preflight` summary before the first edit lands.
  It requires or reminds on placement, reuse, object/module boundary, test plan,
  residual risk, and rollback/revert path. The default gate mode is `block` for
  supported hooks. Set `CHANGEFORGE_PRE_EDIT_MODE=warn` to downgrade locally.
  Copilot templates do not wire unsupported `PreToolUse` advisory, so PostToolUse
  and Stop report preflight gaps for Copilot.
- Process Phase Gate: at Codex and Claude `UserPromptSubmit`, `PreToolUse`, and
  `Stop`, initialize a bounded process phase ledger for non-trivial engineering
  prompts, block `PreToolUse` mutation where the adapter supports pre-tool
  blocking until independent PDD/DDD/SDD/TDD phase reviews pass, and recheck
  phase, review, repair, re-review, and validation freshness before handoff. It
  stores digests, review IDs, status facts, and bounded findings only; reviewed
  phase status requires both an artifact digest and review ID. The
  `process_phase_ledger_seen`, `pdd_reviewed`, `ddd_reviewed`, `sdd_reviewed`,
  and `tdd_reviewed` booleans are telemetry shortcuts only; final closure proof
  comes from the latest ledger record plus digest/review ID, or
  `not_applicable` with a reason.
  Copilot cannot enforce `PreToolUse`, so it records degraded phase enforcement
  and relies on parent-context review evidence, PostToolUse facts, and Stop.
- Post-Edit Structure Gate: after edit tools run, detect structural code changes
  that should preserve reuse, placement, ownership, dependency direction, public
  API decisions, same-pattern scans, and nearby tests.
- Risk Surface Gate: after edit tools or shell commands run, detect high-risk
  surfaces such as auth, data contracts, cache, queue, Kubernetes, Helm, and big
  data work so the agent remembers the matching gate.
- Stop Closure Gate: before final handoff, require the agent to include the
  ChangeForge path used, implementation preflight evidence, changed files,
  validation evidence, residual risk, next actions, phase reviews, repair and
  re-review evidence for blocking findings, and validation freshness after the
  final edit. In block mode it blocks `Stop` where the adapter supports a hard
  Stop decision; unsupported adapters record degraded enforcement instead of a
  pass.
- Subagent Review Gate: at Codex and Claude `SubagentStart` and `SubagentStop`,
  provide bounded review capsule requirements and merge only structured
  `phase_review_result` records back into parent state. A passing phase review
  must match the current artifact digest from the review capsule or phase
  ledger. Raw subagent transcript, raw prompts, secrets, and implementer
  self-approval are not merged. Copilot
  receives `SubagentStart` capsule context but does not wire unsupported
  `SubagentStop`, so it records degraded enforcement and requires parent-context
  review evidence or CI validation.

## Non-Goals

- Do not replace `change-forge-router`.
- Do not turn hooks into professional skills.
- Do not read every `references/` file.
- Do not read, record, log, or echo user prompt text.
- Do not choose the full route; the router remains the semantic source of truth.
- Do not block unsupported or advisory-only gates by default.
- Do not fail closed on hook runtime errors unless explicitly configured.
- Do not turn hooks into router, skills, or source-of-truth.
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
`additionalContext` for supported events. Copilot cannot run Codex/Claude
`PreToolUse` blocking gates or `SubagentStop` review collection, so it relies on
PostToolUse, parent-context review evidence, and Stop closure compensation where
those facts are available. Missing hard-enforcement support is recorded as
degraded evidence rather than a pass. Claude commands set
`CHANGEFORGE_AGENT=claude` explicitly, emit `hookSpecificOutput.additionalContext`
for context-bearing events, and use 10-second `timeout` values because Claude
Code measures timeout in seconds.
Each layout includes `.changeforge-hook-manifest.json` so installation
validation can prove which hook scripts and scope were emitted.

Supported Codex, Claude, and Copilot project/user installs include hooks and
professional injection by default. Use `--without-hooks` or
`--activation-level none` to opt out. `--activation-level bootstrap` installs
only the non-executable route-preflight fragment. `--with-hooks` remains
accepted as a backward-compatible explicit enable, but is no longer required.
Existing hook configuration is always preserved and hooks are never trusted
automatically.

## Action-Aware Professional Injection

The hook runtime now adds an action-aware layer around the original reminders:

- `changeforge_action_classifier.py` classifies the current lifecycle stage
  (`question`, `read`, `plan`, `edit`, `test`, `review`, `repair`, `refactor`,
  `release`, `skill_authoring`, `hook_runtime`, `permission`, `subagent`,
  `compaction`, or `unknown`) and detects compact source/reason/matcher names.
  Pure questions, explanations, translations, and no-action lifecycle events do
  not receive professional injection and do not create Stop closure surface.
- `changeforge_runtime_route_resolver.py` maps the action, canonical stage,
  product surfaces, language surfaces, risk surfaces, and domain extensions to
  the minimum owner/reviewer skill set, selected capabilities, reference paths,
  skipped rationale, and quality gates. `changeforge_skill_index.py` remains a
  compatibility wrapper and does not contain static edit/repair owner routing.
- `changeforge_runtime_adapters.py` isolates output protocol differences across
  Codex, Claude, Copilot, and generic text runtimes.
- `changeforge_professional_injector.py`, read/review/permission/compaction,
  and subagent gates update bounded cache-side state and emit advisory context.
  The injector never marks a route manifest as present; only parsed handoff text
  can prove a `changeforge_route` manifest.

The runtime stores only bounded facts such as stage, paths, skill names, gate
names, and compact signal names. It does not persist prompt text, secrets,
environment variables, full command arguments, command output, user archives, or
personal content indexes.

## Policy and State

Global hook mode remains:

```bash
CHANGEFORGE_HOOK_MODE=off|monitor|warn|block
```

Gate-specific modes override it:

```bash
CHANGEFORGE_PRE_EDIT_MODE=off|monitor|warn|block
CHANGEFORGE_SDD_CHOICE_MODE=off|monitor|warn|block
CHANGEFORGE_PROCESS_PHASE_MODE=off|monitor|warn|block
CHANGEFORGE_PERMISSION_MODE=off|monitor|warn|block
CHANGEFORGE_STOP_MODE=off|monitor|warn|block
CHANGEFORGE_SUBAGENT_REVIEW_MODE=off|monitor|warn|block
CHANGEFORGE_HOOK_FAILURE_MODE=fail_open|fail_closed
```

Default gate modes are `sdd_material_choice=block`,
`pre_edit_structure=block`, `process_phase=block`, and
`stop_closure=block`. Stop closure blocks non-trivial engineering handoff where
the adapter supports hard Stop decisions; unsupported adapters record degraded
closure instead of claiming enforcement. Unspecified gates fallback to `warn`,
and ordinary advisory gates default to `warn`. Hook runtime failures still fail
open unless explicitly configured fail-closed.
`changeforge_hook_policy.py` also exposes timeout, retry,
retry-delay, max-concurrency, and queue-limit policy fields for future lifecycle
adapters, without changing the synchronous script behavior.

`changeforge_state_reducer.py` owns state merge semantics. Lists are additive,
deduped, and capped; booleans use OR semantics; scalar stage/owner fields keep
the last non-empty value; and empty `active_skill_context` updates do not erase
existing compacted context. The runtime never stores raw prompts, secrets,
environment variables, full command output, or user-specific content corpora.

Example preflight:

```yaml
changeforge_implementation_preflight:
  stage: edit
  read_evidence:
    target_files:
      - src/module/file.py
    sibling_files:
      - src/module/sibling.py
    nearby_tests:
      - tests/test_file.py
  placement_decision:
    target_file: src/module/file.py
    owner_module: module
    reason: existing module owns this behavior and test boundary
    rejected_locations:
      - path: src/common/utils.py
        reason: wrong ownership
  reuse_decision:
    direct_reuse:
      - symbol_or_path: src/module/existing.py
        reason: existing behavior
    new_code_justification: no compatible extension point
  object_boundary:
    artifact_type: module
    owner: module
    state_or_invariant: module owns the changed behavior boundary
    public_api_change: false
    compatibility_notes: no public API change
  test_plan:
    validation_commands:
      - python3 -m unittest discover -s tests
  risk:
    rollback_or_revert_path: revert this patch
```

Additional install flags:

```bash
python3 installers/install.py --agent codex --scope project --target <repo>
python3 installers/install.py --agent codex --scope project --target <repo> --with-universal-bootstrap
python3 installers/install.py --agent codex --scope project --target <repo> --without-hooks
python3 installers/install.py --agent copilot --scope project --target <repo> --with-copilot-instructions
```

Supported project/user installs include hooks and professional injection by
default. `--without-hooks` installs skills without executable hooks.
`--with-hooks` and `--professional-injection` remain backward-compatible
explicit enables. `--activation-level bootstrap` installs only the
non-executable route-preflight fragment; `--with-universal-bootstrap` installs
both the route preflight and professional bootstrap fragments under
`.changeforge/`.
`--with-copilot-instructions` creates
`.github/copilot-instructions.md` only when that file does not already exist.
