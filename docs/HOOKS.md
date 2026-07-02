# ChangeForge Hook Runtime

ChangeForge Hook Runtime is installed by default for supported Codex, Claude,
and Copilot project/user scopes unless `--without-hooks` is requested. It is
not a skill, does not replace `change-forge-router`, and does not read all
compiled skill references. Its job is to notice bounded runtime signals,
inject professional context, block user-owned SDD material choices before
mutation/handoff, and close the matching ChangeForge gate where the runtime
supports blocking.

## What Hook Runtime Does

The hook runtime is bounded runtime support for ChangeForge workflows. It:

- injects concise professional context for supported lifecycle events;
- reminds the agent to route engineering work through `change-forge-router`;
- records bounded read/edit/test/review/repair evidence for closure checks;
- blocks high-confidence user-owned SDD material choices before mutation or
  handoff when the adapter supports blocking;
- blocks Stop only when required closure evidence is missing and the runtime
  supports a blocking Stop decision.

The hook runtime is not a skill, not a router, not a replacement for direct
source inspection, and not a reader for every compiled skill reference.

## Defaults and Opt-out

Supported Codex, Claude Code, and GitHub Copilot project/user quickstart and
install paths enable the strongest supported hook/professional-injection mode by
default.

Use `--without-hooks` or `--activation-level none` to opt out of executable hooks
and professional injection. Use `--activation-level bootstrap` when you only
want the non-executable `.changeforge/changeforge-route-preflight.md` fragment.
`--with-hooks` remains accepted for backward compatibility, but users no longer
need to specify it for supported project/user installs.

Hook runtime files are built into `dist/` first. Do not install
`src/hook-runtime` directly.

## Supported Runtimes

Executable hook templates are emitted for:

- Codex project and user scopes;
- Claude Code project and user scopes;
- GitHub Copilot project and user scopes.

OpenAI API hosted skill zips do not install executable hooks. Cline, Roo,
OpenHands, Gemini CLI, and Goose entries in the adapter matrix are staged or
placeholder capability records unless their row explicitly says an executable
hook lifecycle is supported.

## Blocking vs Advisory Gates

Most hook output is advisory professional context. Unsupported checks degrade to
residual risk instead of pretending to pass. Blocking is reserved for conditions
where the runtime can make a high-confidence decision:

- user-owned SDD material choice before mutation or handoff;
- missing closure evidence at Stop where Stop blocking is supported;
- explicit stricter local policy selected by a maintainer.

Unsupported adapter events, missing visibility, stale validation, failed
validation, and unknown evidence must be reported as degraded or residual risk.
They should not be rewritten as `pass` by hand.

## SDD Material Choice Gate

The SDD material choice gate protects choices the user must own, such as adding
new structure, changing public contracts, introducing new runtime state,
choosing irreversible migration strategy, or changing release/security policy.
The hook can block before mutation or handoff when it sees a high-confidence
material choice without documented rationale.

## Pre-edit Structure Gate

Before structure-changing edits, the hook expects source-backed placement
rationale: what was inspected, where the change belongs, rejected locations,
reuse or new-code justification, same-pattern scan, validation plan, and rollback
or recovery note. This is evidence for review; it is not a replacement for
reading the target code.

## Stop Closure Gate

Stop closure checks whether the final handoff has fresh validation evidence,
route/stage evidence for non-trivial engineering work, residual risk, and a
rollback note when relevant. Free-form completion claims are weaker than bounded
Validation Broker facts.

## Telemetry / Privacy Boundaries

Hook state stores bounded operational facts such as stage, selected skill names,
capability names, gate names, paths, command kind/risk class, validation outcome,
and closure status. It must not store raw prompts, secrets, environment
variables, full command output, personal archives, or toolbox mappings.

## Runtime Protocol Boundaries

The hook runtime and adapter core provide an execution protocol, not an LLM, a
router, or a source of skill rules. Runtime adapters normalize supported agent
events into bounded facts, report adapter capabilities, and degrade explicitly
when an event or advisory output path is unsupported. Unsupported events follow
adapter policy: fail open for advisory reminders, fail closed only for
configured high-confidence closure gates, and record the limitation as residual
risk when it affects handoff evidence.

Codex, Claude, and Copilot use concrete hook-backed runtime translators behind
the shared adapter protocol. Cline, Roo, and OpenHands are staged adapter
targets only: Cline has skills/profile install support and Plan/Act mode
normalization, Roo has mode-policy normalization, and OpenHands has a backend
protocol event normalizer. They do not ship executable hook templates here.
Translators record only command kind and risk category, never full command
arguments, prompts, environment variables, or raw command output.

The adapter capability matrix is the single downstream source for runtime
differences. `scripts/validate-hooks.py` and `installers/doctor.py` print it as
part of hook validation. The broader developer command set lives in
[VALIDATION.md](VALIDATION.md); this document stays scoped to hook runtime
behavior, adapter support, telemetry boundaries, and closure semantics.

<!-- changeforge-adapter-capability-matrix:start -->
| Runtime | Supported events | Unsupported events | Advisory context | Stop block | Visibility | Failure/degraded policy | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Codex | `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `Stop`, `SubagentStart`, `SubagentStop`, `Compact` | `UserPromptExpansion`, `PostToolUseFailure`, `PostToolBatch`, `StopFailure`, `SessionEnd`, `TaskCreated`, `TaskCompleted`, `FileChanged`, `ConfigChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact` | yes | yes | read_paths=partial, changed_paths=partial, command_kind=partial, command_risk=partial, validation_outcome=partial, permission_decision=partial, rollback_checkpoint=none | fail_open=degraded_or_unsupported_checks_require_residual_risk; fail_closed_allowed=stop_closure | bounded adapter facts only; no raw prompt or command output |
| Claude | `SessionStart`, `UserPromptSubmit`, `UserPromptExpansion`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `Stop`, `StopFailure`, `SessionEnd`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `FileChanged`, `ConfigChanged`, `PreCompact`, `PostCompact`, `Compact` | `WorktreeCreate`, `WorktreeRemove` | yes | yes | read_paths=partial, changed_paths=partial, command_kind=partial, command_risk=partial, validation_outcome=partial, permission_decision=partial, rollback_checkpoint=none | fail_open=degraded_or_unsupported_checks_require_residual_risk; fail_closed_allowed=stop_closure | bounded adapter facts only; no raw prompt or command output |
| Copilot | `SessionStart`, `PostToolUse`, `Stop`, `SubagentStart` | `UserPromptSubmit`, `PreToolUse`, `SubagentStop`, `UserPromptExpansion`, `PermissionRequest`, `PostToolUseFailure`, `PostToolBatch`, `StopFailure`, `SessionEnd`, `TaskCreated`, `TaskCompleted`, `FileChanged`, `ConfigChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`, `Compact` | yes | yes | read_paths=partial, changed_paths=partial, command_kind=partial, command_risk=partial, validation_outcome=partial, permission_decision=none, rollback_checkpoint=none | fail_open=degraded_or_unsupported_checks_require_residual_risk; fail_closed_allowed=stop_closure | bounded adapter facts only; no raw prompt or command output |
| Generic fallback | `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop` | `UserPromptExpansion`, `PermissionRequest`, `PostToolUseFailure`, `PostToolBatch`, `StopFailure`, `SessionEnd`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `FileChanged`, `ConfigChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`, `Compact` | yes | no | read_paths=partial, changed_paths=partial, command_kind=none, command_risk=none, validation_outcome=none, permission_decision=none, rollback_checkpoint=none | fail_open=degraded_or_unsupported_checks_require_residual_risk; fail_closed_allowed=none | bounded adapter facts only; no raw prompt or command output |
| Cline staged target | none | `SessionStart`, `UserPromptSubmit`, `UserPromptExpansion`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `Stop`, `StopFailure`, `SessionEnd`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `FileChanged`, `ConfigChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`, `Compact` | no | no | read_paths=none, changed_paths=none, command_kind=none, command_risk=none, validation_outcome=none, permission_decision=none, rollback_checkpoint=none | fail_open=degraded_or_unsupported_checks_require_residual_risk; fail_closed_allowed=none | staged adapter target; no executable hook lifecycle |
| Roo staged target | none | `SessionStart`, `UserPromptSubmit`, `UserPromptExpansion`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `Stop`, `StopFailure`, `SessionEnd`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `FileChanged`, `ConfigChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`, `Compact` | no | no | read_paths=none, changed_paths=none, command_kind=none, command_risk=none, validation_outcome=none, permission_decision=none, rollback_checkpoint=none | fail_open=degraded_or_unsupported_checks_require_residual_risk; fail_closed_allowed=none | staged adapter target; no executable hook lifecycle |
| OpenHands backend target | `SessionStart`, `SessionEnd`, `TaskCreated`, `TaskCompleted`, `PostToolUse`, `PostToolUseFailure`, `FileChanged`, `Stop` | `UserPromptSubmit`, `UserPromptExpansion`, `PreToolUse`, `PermissionRequest`, `PostToolBatch`, `StopFailure`, `SubagentStart`, `SubagentStop`, `ConfigChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`, `Compact` | no | no | read_paths=partial, changed_paths=full, command_kind=partial, command_risk=partial, validation_outcome=partial, permission_decision=none, rollback_checkpoint=partial | fail_open=degraded_or_unsupported_checks_require_residual_risk; fail_closed_allowed=none | bounded adapter facts only; no raw prompt or command output |
| Gemini CLI placeholder | none | `SessionStart`, `UserPromptSubmit`, `UserPromptExpansion`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `Stop`, `StopFailure`, `SessionEnd`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `FileChanged`, `ConfigChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`, `Compact` | no | no | read_paths=none, changed_paths=none, command_kind=none, command_risk=none, validation_outcome=none, permission_decision=none, rollback_checkpoint=none | fail_open=degraded_or_unsupported_checks_require_residual_risk; fail_closed_allowed=none | placeholder only; no executable hook lifecycle |
| Goose placeholder | none | `SessionStart`, `UserPromptSubmit`, `UserPromptExpansion`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `Stop`, `StopFailure`, `SessionEnd`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `FileChanged`, `ConfigChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`, `Compact` | no | no | read_paths=none, changed_paths=none, command_kind=none, command_risk=none, validation_outcome=none, permission_decision=none, rollback_checkpoint=none | fail_open=degraded_or_unsupported_checks_require_residual_risk; fail_closed_allowed=none | placeholder only; no executable hook lifecycle |
<!-- changeforge-adapter-capability-matrix:end -->

Unsupported checks in the closure contract stay unsupported. A runtime that
cannot observe a lifecycle event or inject advisory context records a degraded
capability and residual risk; it is never treated as a full pass. `Compact`
remains a backward-compatible alias, while new adapters should prefer
`PreCompact` and `PostCompact` when the executor exposes direction-specific
compaction events.

Every gate that needs runtime facts builds a shared executor snapshot:
`snapshot_from_event_state(event, state, classification=..., read_evidence=...)`.
The snapshot contains adapter capabilities, a `NormalizedEvent`, the current
`LifecycleState`, an `EvidenceLedger`, a `GateResult`, and, for Stop, an
optional `ClosureContract`. Gates persist only bounded reducer facts derived
from that snapshot. They do not store raw hook payloads, raw prompts, full
commands, command output, secrets, environment variables, or personal content
corpus indexes.

Canonical evidence flow:

1. The runtime adapter normalizes executor-specific event names, tool names,
   paths, command program/risk class, validation outcome, permission decision,
   checkpoint/rollback markers, and capability degradation into bounded facts.
2. The hook gate evaluates policy using normalized facts plus local reducer
   state. Unsupported checks degrade to advisory residual risk unless the gate
   is explicitly configured to block a high-confidence condition.
3. The state reducer merges `runtime_adapter`, `normalized_events`, read,
   changed, deleted, generated, external, config, validation, review, repair,
   rereview, permission, command-risk, rollback, and structure-finding facts
   with caps, dedupe, and OR semantics.
4. Stop closure consumes the evidence ledger and Validation Broker result,
   not free-form validation claims alone. Free-form final text can satisfy
   handoff wording checks, but structured stale, failed, or unknown validation
   facts control validation closure.
5. For non-trivial engineering tasks, Stop closure also requires
   `changeforge_stage_route` / `stage_route` evidence unless the state carries a
   concrete skip reason in `stage_route_skip_reason` or
   `stage_route_not_required_reason`. Task classification fields such as
   `trivial_engineering_task` and `non_trivial_engineering_task` are not skip
   reasons. Missing stage route evidence is reported as missing closure
   evidence and cannot produce a `ready` verdict.

Repository graph and context-pack support are source-evidence helpers. They may
summarize symbol, import, reference, test, ownership, and generated-artifact
relationships, but they are not whole-repository dumps and do not replace direct
file inspection. Stale graph or context-pack evidence must be refreshed or
labeled as an assumption.

Project memory is human-governed operational memory. It can warn about repeated
failures, fragile files, and stale context, but it never auto-learns into skills,
registry rules, or capabilities. Memory summaries are experience evidence, not
source facts.

The Validation Broker owns validation freshness classification for closure
checks. It maps changed paths to candidate commands, parses bounded outcomes,
and rejects stale, failed, command-only, or negative validation evidence.

Trajectory inspection is an offline review view built from bounded telemetry,
memory, and validation facts. It checks stage order, repair/re-review,
validation freshness, and residual-risk closure without recording prompts,
secrets, environment variables, raw command output, or full command arguments.

## Runtime Gate Details

The first-stage runtime provides these reminder gates:

- Session Bootstrap (route preflight): runs at session start and reminds the
  agent to classify the change and run a `change-forge-router` preflight before
  engineering work, to require `implementation-structure-design` before new
  structure, and to bind any completion claim to `agent-execution-discipline`.
  It only emits a route preflight; it never selects a full route and never reads
  every reference. It is wired as a `SessionStart` hook for Codex, Claude, and Copilot
	  (Codex `SessionStart` also fires with the `compact` source after compaction,
	  so the runtime re-injects the latest bounded pre-compact snapshot and keeps
	  professional injection from overwriting restored context). Copilot
  `SessionStart` and `SubagentStart` also inject the static ChangeForge skill
  summary as top-level `additionalContext`. The same guidance also ships as an
  install-time bootstrap fragment for users who prefer not to trust executable hooks.
- Route Reminder (`UserPromptSubmit`, Codex and Claude): adds a concise per-prompt
  reminder to run `change-forge-router` and emit a `changeforge_route` manifest
  for any engineering change. It is advisory developer context, never reads or
  records the prompt text, and writes no telemetry. Copilot templates do not
  wire this event because Copilot does not process `userPromptSubmitted`
  advisory output. Pure questions, explanations, and translations do not create
  professional injection state and do not require a route manifest.
- Pre-Edit Risk Preview (`PreToolUse`, Codex and Claude): before an edit or command runs,
  it previews ChangeForge risk surfaces (auth, data contract, cache, queue,
  Kubernetes, Helm, big data) and reminds the agent to route first. It reuses
  the Risk Surface Gate matching, is advisory only, never denies the tool call,
  and never mutates per-turn state. The Permission Policy Gate also runs on
  Codex/Claude Bash `PreToolUse` as a warning-only check for destructive,
  release-sensitive, migration, and dependency mutation commands. Copilot
  templates do not wire this event because Copilot `preToolUse` supports
  permission decisions and argument modification, not advisory `additionalContext`.
- SDD Material Choice Gate (`PreToolUse` and `Stop`, Codex and Claude): before
  `apply_patch`, `Edit`, `Write`, `MultiEdit`, or material Bash mutation, it
  blocks when a material choice is detected and no qualified
  `changeforge_sdd_choice` or `design_decision_points` evidence exists. It also
  rechecks at Stop so an implementation that silently made the choice cannot be
  handed off as complete. Copilot does not run the SDD Material Choice Gate
  directly. It relies on `PostToolUse`/review findings and Stop closure
  compensation where those facts are available.
- Pre-Edit Implementation Structure Gate (`PreToolUse`, Codex and Claude):
  before `apply_patch`, `Edit`, `Write`, or `MultiEdit`, it checks for read
  evidence and a `changeforge_implementation_preflight` summary covering
  placement, reuse, object/module boundary, test plan, risk, and rollback. This
  moves the critical structure decision before the edit instead of relying only
  on post-edit review. Default mode is block for supported hooks; set
  `CHANGEFORGE_PRE_EDIT_MODE=warn` to downgrade. Copilot templates do not wire unsupported `PreToolUse`
  advisory and instead rely on PostToolUse and Stop compensation.

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
  skill path, `changeforge_stage_route` when engineering work was non-trivial,
  changed files, validation evidence, residual risk, next steps, and the
  implementation preflight summary plus structure-evidence records (file
  naming, reuse ladder, extension safety, advanced refactor, comment quality)
  for any structure sub-gate that fired.
- Subagent Closure Reminder (`SubagentStop`, Codex and Claude): reminds a stopping subagent
  to hand the parent the route manifest, validation evidence, and residual risk.
  It emits an advisory `systemMessage`, never forces the subagent to continue,
  and never touches the parent turn's closure state. Copilot templates do not
  wire this event because Copilot `subagentStop` supports block/allow decision
  control, not advisory `systemMessage`. The Session Bootstrap runs at
  `SubagentStart` so a spawned subagent inherits the route preflight and skill
  summary.

Codex and Claude default to strongest supported behavior: SDD material choice,
pre-edit structure, and Stop closure block by default, while most other context
remains advisory. Copilot defaults to strict Stop closure where supported and
keeps SessionStart, SubagentStart, and PostToolUse context advisory. A hook
failure still fails open unless a maintainer explicitly configures fail-closed.

## Hook Policy

Permission checks classify command risk as `safe`, `mutation`, `destructive`,
`release`, `migration`, `dependency`, `network`, or `unknown`. Safe commands
record bounded facts without warning unless another gate sees risk. Mutation
commands warn when plan/preflight evidence is missing. Destructive commands
warn or block according to configured mode and runtime blocking support.
Release and migration commands escalate delivery, security, and API/data gates;
dependency commands require dependency/security review; unknown commands warn
as residual risk. Only the program token and risk class are recorded.

The runtime still accepts the legacy global mode:

```text
CHANGEFORGE_HOOK_MODE=off|monitor|warn|block
```

It also accepts per-gate overrides:

```text
CHANGEFORGE_PRE_EDIT_MODE=off|monitor|warn|block
CHANGEFORGE_SDD_CHOICE_MODE=off|monitor|warn|block
CHANGEFORGE_PERMISSION_MODE=off|monitor|warn|block
CHANGEFORGE_STOP_MODE=off|monitor|warn|block
CHANGEFORGE_HOOK_FAILURE_MODE=fail_open|fail_closed
```

Default enforcement modes are:

```text
sdd_material_choice: block
pre_edit_structure: block
stop_closure: block
```

Precedence is gate-specific mode, then `CHANGEFORGE_HOOK_MODE`, then these
default gate modes, then `warn`.
Failure mode defaults to `fail_open`. The policy model also carries timeout,
retry, retry delay, max concurrency, and queue-limit fields for richer lifecycle
policy expression, while the shipped scripts remain synchronous and bounded.
Only configured enforcement gates block; ordinary hook errors fail open.

## SDD Material Choice Gate Reference

The material choice gate blocks by default when the wrong design answer could
change contract, architecture, data/security behavior, acceptance behavior, or
user-visible behavior. Blocking means the agent must stop and ask the user to
choose before editing or handing off.

Choice evidence can be recorded as either `changeforge_sdd_choice` or existing
SDD `design_decision_points`. A blocking `required` choice must wait for user
resolution. `resolved` must include concrete `resolution_evidence`.
`not_required` must cite a prompt, fixture, explicit user instruction,
repository convention, existing pattern, owner evidence, or reuse evidence.
`assumed_with_rationale` is accepted only for local, reversible, conventional,
acceptance-neutral choices, and never for security, data, API, migration,
rollback, auth, payment, privacy, irreversible, or user-visible changes.

Requires user choice by default:

- New public API, public export, interface, or protocol.
- New module, directory, service, shared package, common helper, utility, plugin, or registry.
- Reuse existing owner versus new boundary.
- Function versus class/object hierarchy, inheritance versus composition, adapter, wrapper, factory, or strategy.
- Cache, queue, worker, async job, external dependency, provider, SDK, schema, data model, migration, or rollback.
- Security, auth, permission, tenant, privacy, payment, irreversible operation, or user-visible acceptance behavior.
- Broad "optimize", "enhance", "refactor", "professionalize", or architecture-adjustment requests where cost/benefit depends on user preference.

Does not require user choice by default:

- Typo, formatting, or docs-only edits.
- Read-only, test-only, and review-only turns with no requested mutation.
- Local reversible same-file fixes that follow repository convention and do not change acceptance.
- Prompts, fixtures, explicit instructions, or existing owner conventions that already decide the only valid design.

Downgrade only when intentionally collecting false positives:

```text
CHANGEFORGE_SDD_CHOICE_MODE=warn
CHANGEFORGE_SDD_CHOICE_MODE=off
CHANGEFORGE_PRE_EDIT_MODE=warn
CHANGEFORGE_STOP_MODE=warn
CHANGEFORGE_HOOK_MODE=warn
```

## State Reducer

Hook state is merged through explicit reducers:

- `runtime_adapter` stores adapter name plus supported, unsupported, and
  degraded checks;
- `normalized_events` stores compact event summaries such as event, stage,
  tool category, risk class, and path count;
- list fields such as `changed_paths`, `read_paths`, `risk_surfaces`, and
  `implementation_preflights` are additive, deduped, and capped;
- material and external-change lists include `deleted_paths`,
  `generated_paths`, `external_file_changes`, and `config_changes`;
- closure evidence lists include `validation_results`, `review_findings`,
  `repair_events`, `rereview_events`, `permission_decisions`, `command_risks`,
  `rollback_points`, and `post_edit_structure_findings`;
- SDD choice lists include `choice_ids`, `choice_triggers`, `choice_status`,
  `material_choice_surfaces`, `blocked_tool_category`, and `bounded_paths`;
- SDD choice booleans include `choice_gate_seen`, `choice_gate_blocked`, and
  `choice_resolution_evidence_seen`;
- booleans such as `read_evidence_seen`, `review_evidence_seen`, and
  `implementation_preflight_required` use OR semantics, so `False` cannot erase
  a prior `True`;
- stage and owner fields keep the last non-empty value;
- `active_skill_context` is replaced only by a non-empty mapping, so compaction
  reinjection cannot erase the previous active context with an empty update.

State remains cache-side only and stores bounded facts, not raw prompts,
environment variables, secrets, full command output, or personal archives.
If a material change is recorded after a validation command, the reducer adds a
stale validation result so Stop closure cannot treat the earlier command as
fresh evidence.

## Implementation Preflight Manifest

For structural edits, the agent should emit a compact preflight before editing:

```yaml
changeforge_implementation_preflight:
  stage: edit
  target_change:
    summary: "..."
    intended_files:
      - "src/module/file.py"
  read_evidence:
    target_files:
      - "src/module/file.py"
    sibling_files:
      - "src/module/sibling.py"
    caller_callee_paths:
      - "src/app.py"
    nearby_tests:
      - "tests/test_file.py"
    configs_or_docs:
      - "README.md"
  placement_decision:
    target_file: "src/module/file.py"
    owner_module: "module"
    owner_object_or_function: "ExistingOwner"
    reason: "..."
    rejected_locations:
      - path: "src/common/utils.py"
        reason: "Would hide module ownership."
  reuse_decision:
    direct_reuse:
      - symbol_or_path: "src/module/existing.py"
        reason: "..."
    extension_reuse:
      - symbol_or_path: "src/module/base.py"
        behavior_preservation: "..."
    new_code_justification: "..."
  object_boundary:
    artifact_type: module
    owner: "module"
    state_or_invariant: "..."
    public_api_change: false
    compatibility_notes: "..."
  test_plan:
    test_files:
      - "tests/test_file.py"
    validation_commands:
      - "python3 -m unittest discover -s tests"
    regression_scope: "..."
  risk:
    compatibility_risk: "..."
    rollback_or_revert_path: "revert this patch"
    unverified_items:
      - "..."
```

Read-only, review-only, and educational question turns do not require this
manifest when no files changed.

`object_boundary` is considered complete only when it names at least
`artifact_type` and `owner`, plus either `state_or_invariant` or
`compatibility_notes`. Scalar placeholders such as `object_boundary: yes` do
not satisfy the pre-edit gate.

## Telemetry

In addition to their reminders, runtime gates append a small telemetry record
to the user cache after each watched event. Telemetry is a runtime fact log used
for offline review; it is never written into project source or `dist/`, and it
records no prompts, environment variables, secrets, or full command output. The
Tool Output Boundary Gate records only bounded tool-output metadata and
repo-relative/cache-scoped artifact references. It never stores raw stdout,
stderr, prompts, environment values, full diffs, full files, secrets, or personal
archives; full logs must be explicitly redirected or sliced by the user/agent and
then cited as artifacts.
The Stop Closure Gate records closure-completeness facts only: whether a complete
parseable `changeforge_route` manifest, changed files, validation evidence,
residual risk, and required references were present. A prose mention of
`changeforge_route`, or a YAML block missing `selected_skills`,
`selected_capabilities`, `required_references`, or `required_quality_gates`, is
not counted as route-manifest evidence.
The Stop closure contract also records `adapter`, `supported_checks`,
`unsupported_checks`, `degraded_capabilities`, `verdict`, and residual-risk
labels so unsupported runtime paths degrade explicitly instead of being counted
as observed checks. Stop telemetry also includes a bounded `changeforge_closure`
object with adapter, verdict, supported/unsupported checks, present/missing/
negative evidence, validation outcome/freshness/scope, review repair and
re-review state, changed/deleted/generated path sets, residual risk, and next
owner. Closure verdicts may be `ready`, `needs_validation`, `needs_review`,
`needs_repair`, `degraded_ready`, or `blocked`; a broker-degraded validation
result can populate validation metadata without being counted as present
closure evidence.

Telemetry is enabled by default and can be disabled with `CHANGEFORGE_TELEMETRY=off`.
See [TELEMETRY.md](TELEMETRY.md) for the data model, the offline review tool, and
the human promotion workflow.

## Project Memory In Hooks

Project memory is a lightweight layer on top of hook telemetry. When telemetry
is enabled, selected bounded telemetry records are mirrored into
`${XDG_CACHE_HOME:-~/.cache}/changeforge/memory/<repo_hash>/events/` as
append-only `MemoryEvent` JSONL records. Memory can be disabled separately with
`CHANGEFORGE_MEMORY=off`.

Hook integration is intentionally narrow:

- Stop closure telemetry can append a memory event after a turn closes.
- Pre-edit implementation structure checks can query cache-side memory for
  fragile-file and repeat-failure warnings.
- Memory hints are warning-only and fail-open; they do not downgrade the default
  blocking modes for SDD material choice, pre-edit structure, or Stop closure.
- Memory never changes skills, routing rules, capabilities, registry files, or
  `dist/`.

Memory hits are experience evidence only. A hit is not current source evidence
unless the adapter can compare its stored `source_evidence.source_hash` with the
current repository file and the hit also carries current validation or review
freshness. Stale, missing, deleted, unknown, legacy hashless, or generated
artifact hits are returned as `historical_hint` or `warning_only` with
`source_status` and residual risk; they cannot by themselves satisfy closure or
justify editing a generated artifact. Generated artifact memory requires an
explicit source-of-truth reference before it can be considered beyond a warning.

The pre-edit fragile-file warning requires the same evidence expected by the
offline memory gate: read-file evidence, nearby-test evidence, memory summary
evidence, an implementation preflight, and current source freshness. If the
only matching memory is stale or legacy hashless, the hook emits a warning and
residual risk but does not add blocking `missing` items. Blocking is reserved
for current, high-confidence fragile memory plus the existing pre-edit hook
mode.

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
- Validation evidence is evaluated by the Validation Broker when available:
  changed paths and risk surfaces resolve to narrow/full command candidates,
  command summaries are parsed into bounded result facts, and Stop closure checks
  whether the command finished after the latest material edit.
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

## Validation Broker

The Validation Broker is a deterministic support package used by scripts and the
Stop Closure Gate. It does not execute tests by itself. It recommends validation
commands from changed paths, risk surfaces, stage, and optional context-pack
validation candidates, then evaluates bounded result facts:

- known rd-skills paths map to narrow commands and full fallback commands;
- unknown paths return a conservative recommendation instead of passing;
- command text without an outcome is weak evidence;
- `not run`, `unable to run`, `未验证`, `无法运行`, and equivalent disclosures are
  negative evidence;
- a validation command observed before the latest material edit is stale and
  cannot prove the final patch;
- coverage that does not align with changed paths or risk surfaces is surfaced
  as a broker issue.
- repair evidence without a later re-review remains open closure work, and
  review findings without repair cannot close as ready.

Hook post-tool validation detection records structured `validation_results`
when a validation-looking command is observable. If the executor exposes an
exit code or explicit outcome, the result is `pass` or `fail`; otherwise it is
`unknown`. Any material edit, generated file change, deletion, external file
change, or config change after validation marks that validation stale. Stop
closure carries this freshness through the ledger and closure contract.

Stop closure remains warning/fail-open by default. In block mode, the gate may
block high-confidence validation failures such as stale validation, failed
validation, or command-without-outcome. Broker telemetry records only bounded
fields such as outcome, freshness, command kind, and covered path/risk patterns;
it never records raw stdout, prompts, secrets, environment variables, or full
command output.

Trajectory inspection consumes these bounded broker fields alongside hook
telemetry and optional memory facts. It reconstructs an ordered evidence view
for offline review, including whether validation ran after the final material
edit, whether repair was followed by re-review, and whether final handoff named
residual risk. It does not execute validation commands, alter hook state,
promote candidates, or edit skills.

Repository-intelligence preflight facts should be passed in bounded form when
available:

```yaml
repository_context:
  context_pack: "/tmp/changeforge-context-pack.json"
  source_of_truth:
    - src/hook-runtime/scripts/changeforge_stop_closure_gate.py
  reuse_candidates:
    - src/runtime_governance/closure.py
  # Use no_reuse_candidate_found: true only after checking local reuse paths.
  validation_candidates:
    - python3 scripts/validate-hooks.py
  rejected_locations: []
  graph_freshness: current
  residual_risk:
    - none
```

These fields are context selectors, not completion evidence. A stale graph,
unknown source-of-truth, rejected location, or missing validator remains residual
risk until the source files are inspected and the Validation Broker has fresh
outcomes for the final material diff.

Runtime support:

- Codex, Claude, and Copilot project hooks all wire the bootstrap as a
  `SessionStart` hook (`changeforge_session_bootstrap.py`), and also at
  `SubagentStart` so spawned subagents inherit the preflight. Codex
  `SessionStart` additionally fires with the `compact` source, re-injecting the
  preflight after compaction.
- Compaction reinjection uses `changeforge_compaction_contract.py` and
  `schemas/compaction-context.schema.json` to preserve only bounded fields:
  route id, selected skills/capabilities/gates, current stage, PDD/DDD/SDD/TDD
  summaries, changed/read paths, validation freshness, review/repair/re-review
  state, residual risk, memory references, repo graph references, and active
  skill context. Snapshot v2 also records typed context-control fields,
  selected/skipped reference policy, omitted-context reasons, branch route-repair
  summaries, and nullable runtime metadata (`tokens_before`,
  `first_kept_entry_id`) when the runtime exposes it. The snapshot rejects or
  redacts raw prompts, raw assistant messages, raw command output, environment
  variables, secrets, API keys, local absolute paths, full file contents, and
  full diff bodies.
- Compaction event responsibilities are split deliberately:
  `PreCompact` is the only snapshot-writing phase; `PostCompact` and
  `SessionStart` with `source=compact` re-inject from the latest snapshot; an
  unknown `Compact` event is a fallback reinject and must not overwrite the
  latest good snapshot.
- The same guidance also ships as an install-time fragment
  (`changeforge-route-preflight.md`) for users who prefer not to trust an
  executable hook, or to reference from the project's agent instructions.
- Any runtime can install the advisory fragment with
  `installers/install.py --with-bootstrap`.

## Agent Event Coverage

Codex and Claude expose the full lifecycle set ChangeForge uses. VS Code
Copilot exposes several of the same events, but ChangeForge wires only the
events whose advisory output Copilot actually consumes:

- `SessionStart` (Codex also with the `compact` source) and `SubagentStart`
  inject the route preflight. On compact sources reinjection uses the latest
  existing snapshot; it does not write a new pre-compact snapshot. Latest active
  snapshots and unresolved review/repair/validation state are preserved by
  priority-aware reducers, and the professional injector does not replace the
  prior active context. Copilot also injects the static ChangeForge skill summary
  on these two events.
- `UserPromptSubmit` adds a per-prompt route reminder for Codex and Claude.
  Copilot templates omit the event because Copilot does not process its
  advisory output.
- `PreToolUse` previews risk surfaces before an edit or command runs for Codex
  and Claude, runs the Pre-Edit Implementation Structure Gate before edit tools,
  and runs the Permission Policy Gate for Bash warnings. Copilot templates omit
  the event because Copilot `preToolUse` does not consume advisory
  `additionalContext`; PostToolUse and Stop report any preflight gap.
- `PostToolUse` runs the read-context, tool-output-boundary, structure, and
  risk-surface gates after edits and commands. Claude also wires the
  tool-output-boundary gate for `PostToolUseFailure` and `PostToolBatch`; Copilot
  uses only its supported `PostToolUse` event.
- `Stop` runs the closure gate. Copilot Stop is strict by default and emits
  top-level `decision`/`reason` only when evidence is missing. `SubagentStop`
  emits an advisory reminder only where supported by Codex and Claude.

The shared hook scripts recognize both Codex/Claude tool names
(`edit`, `write`, `apply_patch`, `bash`) and VS Code Copilot tool names
(`editFiles`, `create_file`, `replace_string_in_file`, `insert_edit_into_file`,
`runTerminalCommand`), so the structure and risk gates fire under every runtime.
VS Code Copilot uses the flat (matcher-less) hook config format with
`version: 1` and `timeoutSec`. It uses PascalCase event names so payloads carry
VS Code-compatible snake_case fields. ChangeForge emits top-level
`additionalContext` only for Copilot context-capable events such as
`SessionStart`, `SubagentStart`, and `PostToolUse`; Copilot Stop uses top-level
`decision`/`reason` in strict mode. Codex and Claude use
`hookSpecificOutput.additionalContext` for context hooks and `systemMessage` for
warning-only Stop/SubagentStop output; Stop block output uses top-level
`decision`/`reason` for both.

These remain execution-time guardrails. They detect edited paths, patch signals,
risk surfaces, and missing closure evidence, and they remind the agent to route;
they never select a complete route and never replace `change-forge-router` or
`implementation-structure-design`. Codex and Claude block SDD material choice,
pre-edit structure, and Stop closure gaps by default. Copilot's blocking is
limited by its supported events; it cannot enforce Codex/Claude-style
PreToolUse gates.

## Hook Capability Boundary

Hooks can:
- remind on route preflight at session start, subagent start, and after
  compaction (`SessionStart`/`SubagentStart`);
- inject the static Copilot skill summary at Copilot `SessionStart` and
  `SubagentStart`;
- remind on routing per user prompt (Codex and Claude `UserPromptSubmit`;
  Copilot does not wire this unsupported advisory path);
- preview risk surfaces before an edit or command runs (Codex and Claude
  `PreToolUse`; Copilot cannot consume advisory preview context);
- require or remind on implementation preflight evidence before structural edits
  (Codex and Claude `PreToolUse`; Copilot compensates after edit and at Stop);
- block material SDD choices before mutation and recheck unresolved choices at
  Stop when the runtime supports those events;
- remind on new file naming pattern mismatches;
- remind on structural path changes;
- remind on helper/common/utils/shared pollution risk;
- remind on reuse ladder evidence;
- remind on extension reuse safety;
- remind on advanced refactor evidence;
- remind on comment quality evidence;
- remind on Stop-stage closure evidence;
- remind a stopping subagent to carry closure evidence (`SubagentStop`, Codex
  and Claude; Copilot does not wire this unsupported advisory path).

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

1. Keep the supported default: hooks plus professional injection, with each
   runtime's supported SDD material choice, pre-edit structure, and Stop closure
   gates in block mode.
2. Use `CHANGEFORGE_SDD_CHOICE_MODE=warn` or `off` only when collecting
   false positives or running a controlled migration.
3. Keep most non-material advisory gates in warn mode until fixture-backed
   evidence proves they are high confidence.
4. Keep fail-open behavior for hook runtime errors unless a maintainer
   explicitly enables fail-closed for a narrow gate.

## Supported Runtime Layouts

Build output supports Codex, Claude, and Copilot project and user scope:

- Codex project hooks: `dist/codex/project/.codex`
- Codex user hooks: `dist/codex/user/.codex`
- Claude project hooks: `dist/claude/project/.claude`
- Claude user hooks: `dist/claude/user/.claude`
- Copilot project hooks: `dist/copilot/project/.github`
- Copilot user hooks: `dist/copilot/user/.copilot`

Project hooks resolve their command path from the project git root; user hooks
resolve it from the agent home directory (`${CODEX_HOME:-$HOME/.codex}` for
Codex, `${CLAUDE_CONFIG_DIR:-$HOME/.claude}` for Claude, `${HOME}/.copilot` for
Copilot) so they apply across every project. VS Code Copilot loads every `*.json`
in its hook folder, so the managed config is a dedicated
`.github/hooks/changeforge-hooks.json` (project) or
`~/.copilot/hooks/changeforge-hooks.json` (user) and the scripts live in a
`changeforge/` subfolder. Admin hook scope is intentionally out of scope.

## Hook Modes

Set `CHANGEFORGE_HOOK_MODE` to control runtime behavior:

- `off`: do nothing.
- `monitor`: update per-turn state without emitting reminders.
- `warn`: emit reminders and continue.
- `block`: emit a block decision. This is the default for SDD material choice,
  pre-edit structure, and Stop closure on supported hook runtimes.

## Build Hooks

Build any runtime profile. Hook artifacts are profile-independent and are
refreshed by each build:

```bash
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
```

Expected hook outputs (project and user scope):

```text
dist/codex/project/.codex/hooks.json
dist/codex/project/.codex/.changeforge-hook-manifest.json
dist/codex/project/.codex/changeforge-route-preflight.md
dist/codex/project/.codex/hooks/changeforge_common.py
dist/codex/project/.codex/hooks/changeforge_session_bootstrap.py
dist/codex/project/.codex/hooks/changeforge_user_prompt_route_reminder.py
dist/codex/project/.codex/hooks/changeforge_pre_tool_risk_preview.py
dist/codex/project/.codex/hooks/changeforge_post_edit_structure_gate.py
dist/codex/project/.codex/hooks/changeforge_risk_surface_gate.py
dist/codex/project/.codex/hooks/changeforge_subagent_stop_reminder.py
dist/codex/project/.codex/hooks/changeforge_stop_closure_gate.py

dist/codex/user/.codex/...        # same Codex layout, CODEX_HOME-resolved paths

dist/claude/project/.claude/settings.changeforge-hooks.fragment.json
dist/claude/project/.claude/.changeforge-hook-manifest.json
dist/claude/project/.claude/changeforge-route-preflight.md
dist/claude/project/.claude/hooks/changeforge_common.py
dist/claude/project/.claude/hooks/changeforge_session_bootstrap.py
dist/claude/project/.claude/hooks/changeforge_user_prompt_route_reminder.py
dist/claude/project/.claude/hooks/changeforge_pre_tool_risk_preview.py
dist/claude/project/.claude/hooks/changeforge_post_edit_structure_gate.py
dist/claude/project/.claude/hooks/changeforge_risk_surface_gate.py
dist/claude/project/.claude/hooks/changeforge_subagent_stop_reminder.py
dist/claude/project/.claude/hooks/changeforge_stop_closure_gate.py

dist/claude/user/.claude/...      # same Claude layout, CLAUDE_CONFIG_DIR-resolved paths

dist/copilot/project/.github/hooks/changeforge-hooks.json
dist/copilot/project/.github/hooks/changeforge/changeforge_common.py
dist/copilot/project/.github/hooks/changeforge/changeforge_copilot_skill_summary.md
dist/copilot/project/.github/hooks/changeforge/...   # scripts, manifest, bootstrap

dist/copilot/user/.copilot/hooks/changeforge-hooks.json
dist/copilot/user/.copilot/hooks/changeforge/changeforge_copilot_skill_summary.md
dist/copilot/user/.copilot/hooks/changeforge/...     # $HOME/.copilot-resolved paths

dist/universal/bootstrap/changeforge-route-preflight.md
```

Codex, Claude, and Copilot all wire the session bootstrap as a `SessionStart`
hook and ship the hook runtime scripts in the project and user layouts. Codex
and Claude emit `hookSpecificOutput.additionalContext` for context-bearing
events; Claude commands explicitly set `CHANGEFORGE_AGENT=claude` because Claude
Code hook input also uses snake_case fields. Claude `timeout` values are seconds
and stay within the 10-second budget. The Copilot layout wires only
`SessionStart`, `SubagentStart`, `PostToolUse`, and `Stop`; it emits top-level
`additionalContext` for session/subagent start and post-tool gates, and the Stop
command sets `CHANGEFORGE_HOOK_MODE=block` for missing closure evidence. VS Code Copilot loads every
`*.json` in the hook folder, so its managed config is the dedicated
`changeforge-hooks.json` and the scripts plus manifest live in a `changeforge/`
subfolder VS Code does not scan for config. Do not install `src/hook-runtime`
directly.

## Manually Enable Hooks

Manual enablement remains supported for users who do not want the installer to
write hook files:

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

The installer can place hooks for Codex, Claude, and Copilot in **project** or
**user** scope. Hooks install by default for supported project/user scopes and
are written only when neither `--dry-run` nor `--hooks-dry-run` is set.
Existing hook configuration is always preserved. Use `--without-hooks` to
install skills without executable hooks or professional injection runtime.
`--with-hooks` remains accepted for backward compatibility but is no longer
required.

The quickstart wrapper has an activation selector:
`--activation-level none|bootstrap|hooks|professional-injection`, plus
`--without-hooks`. Hook-capable project/user scopes default to
`professional-injection`. `none` and `--without-hooks` opt out; `bootstrap`
installs only the non-executable `.changeforge/changeforge-route-preflight.md`
fragment.

Project hooks install under the project root's `.codex`/`.claude`/`.github`; user
hooks install under the agent home (`~/.codex`, `~/.claude`, `~/.copilot`) and
apply to every project, so `--target` does not relocate them. Sandbox a
user-scope install by pointing `HOME` (or `CODEX_HOME`/`CLAUDE_CONFIG_DIR`) at a
scratch directory.

```bash
python3 scripts/build.py --profile full
# Project scope: show the merge plan, then write and merge config:
python3 installers/install.py --agent codex --scope project --target /path/to/project --profile full --hooks-dry-run
python3 installers/install.py --agent codex --scope project --target /path/to/project --profile full
# User scope: hooks install under ~/.codex and apply to every Codex project:
python3 installers/install.py --agent codex --scope user --profile full
python3 installers/install.py --agent claude --scope user --profile full
# Copilot (VS Code): project hooks in .github/hooks, user hooks in ~/.copilot/hooks:
python3 installers/install.py --agent copilot --scope project --target /path/to/project --profile full
python3 installers/install.py --agent copilot --scope user --profile full
# Skills only / no hooks:
python3 installers/install.py --agent codex --scope user --profile full --without-hooks
# Inspect installed project hooks:
python3 installers/doctor.py --check-hooks --target /path/to/project
# Install only the advisory route-preflight fragment (any project install, incl. Codex):
python3 installers/install.py --agent codex --scope project --target /path/to/project --profile full --with-bootstrap
# Inspect the advisory bootstrap fragment:
python3 installers/doctor.py --check-bootstrap --target /path/to/project
```

For Codex, the installer merges ChangeForge hook groups into an existing
`hooks.json` without removing user hooks. For Claude, it places
`settings.changeforge-hooks.fragment.json` and never modifies an existing
`settings.json`; merge the fragment's `hooks` into `settings.json` by hand,
including the `SessionStart` bootstrap entry. For Copilot, it writes the
dedicated `changeforge-hooks.json` into `.github/hooks` (project) or
`~/.copilot/hooks` (user) and leaves any other hook JSON in that folder
untouched; VS Code loads it automatically. The `--with-bootstrap` option
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
required hook events, `SessionStart` bootstrap wiring, the advisory bootstrap
fragment, 10-second timeout limits, Codex and Claude command protocol, Copilot
`version: 1` and `timeoutSec`, JSON warning output, Stop output separation, no
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

## Action-Aware Injection Runtime

The hook runtime includes a professional injection layer in addition to the
original reminder gates.

| Lifecycle area | Scripts | Purpose |
| --- | --- | --- |
| Executor adapter core | `changeforge_adapter_capabilities.py`, `changeforge_normalized_event.py`, `changeforge_lifecycle_state.py`, `changeforge_evidence_ledger.py`, `changeforge_gate_result.py`, `changeforge_closure_contract.py`, `changeforge_executor_adapter_core.py` | Normalize runtime events, expose runtime capabilities, wrap reducer state, collect closure evidence, and share gate/closure result objects without changing hook entrypoints. |
| Action classification | `changeforge_action_classifier.py`, `changeforge_runtime_route_resolver.py`, `changeforge_skill_index.py` | Classify action, resolve canonical stage/surfaces, and select minimum owner/reviewer skill context without static backend defaults. |
| Runtime output | `changeforge_runtime_adapters.py` | Keep Codex/Claude hook-specific context, Copilot top-level context, and generic text output separate through explicit adapter capabilities. |
| Professional context | `changeforge_professional_injector.py` | Emit compact active skill context for engineering stages only and record selected gates/references without marking a route manifest present. |
| Read/review evidence | `changeforge_read_context_gate.py`, `changeforge_review_gate.py` | Preserve read/search, MCP/GitHub/Fetch/PR diff evidence, and separate review intent from artifact evidence. |
| Permission policy | `changeforge_permission_policy_gate.py` | Warn on Bash `PreToolUse` and warn/block permission events for high-risk destructive, release, migration, and dependency commands according to hook mode. |
| Compaction/subagent | `changeforge_compaction_snapshot.py`, `changeforge_compaction_reinject.py`, `changeforge_branch_route_summary.py`, `changeforge_subagent_skill_contract.py` | Preserve active context across compaction and subagent starts, and preserve bounded branch/route-repair summaries for abandoned repair paths. |

Codex and Claude templates wire `PermissionRequest`, prompt, pre-tool,
post-tool, subagent, stop, and session events. Claude templates also include
`UserPromptExpansion` and `PostToolBatch` advisory entries, with `PostToolBatch`
recording read context before review context. Copilot templates stay on
supported flat events only: `SessionStart`, `PostToolUse`, `SubagentStart`, and
`Stop`.

Normalized runtime events expose only bounded fields: lifecycle cadence,
executor event name and phase, tool category, command risk/outcome, exit code,
read/changed/deleted/generated paths, validation status, permission decision,
checkpoint/rollback signals, and privacy redaction markers. They must not carry
raw prompts, full commands, command output, secrets, environment variables, or
personal corpus indexes.

The runtime support files are:

- `changeforge_professional_contract.md` for common professional injection
  guidance;
- `changeforge_copilot_professional_contract.md` for Copilot fallback guidance;
- `templates/bootstrap/changeforge-professional-contract.md` for runtimes where
  executable hooks are not enabled.

Hook state remains cache-local and bounded. It records stage, owner/reviewer
skill, selected capability/gate names, paths, compact signals, and closure
booleans. It must not contain prompts, secrets, environment variables, full
command arguments, command output, user archive indexes, or personal corpus
content.
