# Telemetry, Review, and Human Promotion

ChangeForge can observe real agent execution, review it offline, and let a human
promote the findings into golden cases. This closes the loop from runtime
behavior back into the skill system **without any online self-learning**.

```text
real Codex / Claude / Copilot usage
  -> hooks / stop gate record telemetry JSONL (facts only)
  -> review-agent-telemetry.py analyzes behavior offline
  -> telemetry report + suggestions.yaml (human-review-only)
  -> a human promotes selected suggestions
  -> promote-telemetry-suggestion.py writes candidate eval/fixture files
  -> validate / eval / build verify the change
  -> next usage is more stable
```

## Telemetry Is A Fact Log, Not Auto-Learning

Telemetry records what hooks observed during a turn. It never changes skills,
routing rules, or capabilities, and nothing in this pipeline edits `SKILL.md`,
`routing-rules.yaml`, or `capabilities.yaml`. Every improvement is proposed as a
candidate and only a human decides whether to apply it.

Telemetry, Project Memory, Validation Broker, repository graph, and adapter
facts are bounded evidence inputs. They are not raw prompt storage and not a
source-of-truth substitute for current repository files. Validation commands for
these surfaces are centralized in [VALIDATION.md](VALIDATION.md).

## Where Telemetry Lives

Telemetry is operational cache, not project source and not runtime skill content:

```text
${XDG_CACHE_HOME:-~/.cache}/changeforge/telemetry/<repo_hash>/
    sessions/    # append-only JSONL fact log written by hooks
    reports/     # generated review reports
    suggestions/ # generated, human-review-only suggestions
    promoted/    # audit trail of human-approved promotions
```

`<repo_hash>` is a SHA-256 prefix of the resolved repository root, never an
absolute path. Telemetry is never written into `dist/`, never installed into a
runtime skill folder, and never treated as a personal asset corpus.

## Privacy: What Telemetry Does Not Record

Each record is a small JSON object validated by
[../src/hook-runtime/schemas/telemetry-event.v1.schema.json](../src/hook-runtime/schemas/telemetry-event.v1.schema.json).
Telemetry deliberately omits sensitive content:

- no full prompts;
- no environment variables;
- no secrets;
- no full command output (stdout or stderr);
- no raw tool result output captured by hooks;
- only the leading program name of an observed command (for example `kubectl`),
  truncated, never full arguments;
- repository and working-directory identifiers are hashed, not absolute paths;
- no user absolute paths;
- changed paths are recorded as relative paths and capped in number and length.

Telemetry writing always fails open: any error is logged to the hook debug log
and never interrupts the agent. Set `CHANGEFORGE_TELEMETRY=off` (or `0`, `false`,
`no`) to disable telemetry writing entirely.

## The Route Manifest

`change-forge-router` emits a machine-readable `changeforge_route` YAML block in
addition to the human-readable routing result. The manifest is what hooks,
`doctor`, telemetry review, and the eval tools read. It carries
`selected_skills`, `selected_capabilities`, `selected_domain_extensions`,
`required_references`, `required_quality_gates`, `skipped_quality_gates` (each
with a reason), `blocking_questions`, `assumptions`, and `handoff_target`.
The Stop Closure Gate counts a route manifest as present only when it can parse
non-empty `selected_skills`, `selected_capabilities`, `required_references`, and
`required_quality_gates`; a bare `changeforge_route` string is not evidence.

The manifest does not replace the human-readable explanation and does not
authorize any tool to mutate skill rules. It exists so closure completeness can
be checked mechanically.

## Runtime Governance Facts

Executor adapters expose a runtime protocol surface: adapter capabilities,
normalized event facts, lifecycle state, gate results, evidence-ledger entries,
and closure-contract support. The adapter core is not an LLM and not the router.
When a runtime cannot emit or consume an event, telemetry records the bounded
capability limitation so closure can degrade explicitly instead of pretending the
gate was observed.
Stop telemetry records adapter/closure-contract facts as bounded strings:
`adapter_name`, `adapter_supported_checks`, `adapter_unsupported_checks`,
`adapter_degraded_capabilities`, `closure_contract_verdict`, and
`closure_contract_residual_risk`. These fields let review and trajectory tools
distinguish `ready` from `degraded_ready` when a runtime could not observe a
check such as Copilot `PreToolUse` advisory context. Stop telemetry also writes
a bounded `changeforge_closure` object. It contains adapter, verdict,
supported/unsupported checks, degraded capabilities, present/missing/negative
evidence, validation outcome/freshness/scope/command kind, review repair and
re-review state, changed/deleted/generated path sets, residual risk, and next
owner. `closure_contract_verdict` can be `ready`, `needs_validation`,
`needs_review`, `needs_repair`, `degraded_ready`, or `blocked`.

Repository graph evidence may feed context packs and validation candidates, but
it is a source-evidence helper only. It should name bounded symbols, imports,
references, tests, owners, and generated artifacts relevant to the task; it must
not become a full-repository dump or a substitute for direct source inspection.
Freshness markers decide whether the graph can be treated as current.

Project memory facts are append-only and human-governed. Memory can report repeat
failure, fragile-file, and stale-context signals, but it never modifies skills,
routes, capabilities, or registry data without a human promotion flow.

Tool-output boundary facts are telemetry-safe. Post-tool hooks may record
`tool_output_boundaries` and `artifact_references`, but those fields contain only
tool/event name, output size class, byte/line counts, digest, bounded summary,
truncation advice, context policy, privacy status, unsupported reason, and a
repo-relative or cache-scoped artifact reference. Hooks do not store raw
`stdout`, `stderr`, full command output, prompts, environment values, full diffs,
full files, secrets, or personal archives. If a full log is needed, the user or
agent must explicitly create an artifact by redirecting output or writing a
slice/report, then cite that path and validation status separately.

Branch route-repair facts are telemetry-safe. Hooks may record
`branch_route_repair_summaries` and `route_repair_forbidden_retries` when a
route is abandoned, repaired, switched, or blocked from repeating the same path.
Those fields contain only summary ids, trigger names, bounded route/validation
facts, file path references, reusable findings, forbidden retry labels,
replacement-route facts, residual risk, and privacy status. They do not contain
raw prompts, raw output, full diffs, full file contents, environment values, or
secrets.

Validation Broker facts classify validation command selection and freshness. A
command without outcome, a failed command, a negative validation disclosure, or a
command that finished before the last material edit remains non-closure evidence.
The broker closure outcome is one of `ready`, `needs_validation`,
`degraded_ready`, or `blocked`; the closure contract may further distinguish
`needs_review` and `needs_repair` when review findings, repair evidence, or
missing re-review prevent a ready closure. Degraded adapter coverage is reported
as residual risk instead of a pass.

Trajectory facts are review-only. The trajectory inspector reconstructs stage
order and evidence freshness from bounded telemetry and memory fields, and it
does not record prompts, secrets, environment variables, raw command output, or
full command arguments.

## Hooks Record, They Do Not Route

The Pre-Edit Implementation Structure Gate, Post-Edit Structure Gate, Risk
Surface Gate, Tool Output Boundary Gate, and Stop Closure Gate write telemetry
in addition to their warning-only reminders. The pre-edit gate records only bounded facts such as
changed paths, added paths, missing preflight fields, and whether read evidence
was seen. It does not record the assistant message or raw manifest body. The
tool-output gate records bounded output facts only and degrades to
`unsupported_runtime` when a runtime does not expose output metadata. The
Stop Closure Gate records completeness facts only: whether a complete parseable
`changeforge_route` manifest, changed files, validation evidence, residual risk,
required references, and implementation preflight evidence were present.
When Validation Broker is available, Stop telemetry also records bounded result
facts: validation outcome, evidence strength, negative reason, command kind,
freshness after the last material edit, coverage alignment, and covered path/risk
patterns. It also records optional bounded broker facts:
`validation_broker_closure_outcome`, `validation_broker_selected_scope`,
`validation_broker_negative_evidence`, `validation_broker_residual_risk`, and a
sanitized `validation_broker_command_ledger` whose command display is normalized
or registry-derived. It does not record raw stdout, prompts, secrets,
environment variables, full command output, or dangerous full command arguments.
Stop telemetry also records adapter closure-contract facts. Unsupported adapter
checks are residual-risk evidence and do not satisfy a full validation or
closure pass. The structured `changeforge_closure` object intentionally keeps
validation metadata separate from present closure evidence so a targeted,
stale, failed, or no-outcome validator cannot be inflated into a ready verdict.

Hooks still cannot replace `change-forge-router`. They never call a model, never
reach the network, never modify project source, and never load every compiled
reference. See [HOOKS.md](HOOKS.md). Block mode remains reserved for the
high-confidence violations listed there (stop without validation evidence, stop
without residual risk, new common/utils/helper without reuse evidence, and
dependency file changes without dependency review).

## Step 1: Review Telemetry

`scripts/review-agent-telemetry.py` reads the JSONL fact log, groups it by
session, and writes a report plus a suggestions file. It never edits
`src/registry` or `SKILL.md`.

```bash
python3 scripts/review-agent-telemetry.py
python3 scripts/review-agent-telemetry.py --repo-hash <repo_hash> --since 2026-06-01
python3 scripts/review-agent-telemetry.py --format json --output-dir ./telemetry-out
python3 scripts/review-agent-telemetry.py --recency-half-life-days 2
```

Options: `--telemetry-root`, `--repo-hash`, `--since`, `--until`, `--output-dir`,
`--format markdown|json|yaml`, `--recency-half-life-days`, and the optional CI
guard `--fail-on-high-severity`. With no telemetry it prints `no samples found`
and exits 0.

It detects, among others: `missed_router`, `missed_implementation_structure`,
`missed_reuse_evidence`, `missed_language_capability`,
`missed_middleware_capability`, `missed_validation_evidence`,
`validation_command_without_outcome`, `missed_residual_risk`,
`degraded_runtime_adapter_closure`, `unverified_completion_claim`,
`possible_over_routing`,
`hook_false_positive_candidate`, and `hook_false_negative_candidate`. Every
suggestion carries `id`, `type`, `severity`, `priority_score`, `recency_weight`,
`recent_24h`, `evidence`, `affected_session`, `suggested_action`,
`promotion_target`, and `requires_human_review: true`.

The review summary separates `code_change_closures` from
`engineering_surface_closures`. Risk surfaces that came only from read-only
commands such as `sed`, `rg`, or `cat` are counted under
`read_only_risk_surface_closures` and are not treated as code changes or missing
router evidence. Risk surfaces from changed paths or mutating commands remain
closure-relevant. Recency weighting uses the latest reviewed telemetry timestamp
as the reference point and applies the configured half-life to produce
`priority_score`, `weighted_issue_scores`, and `recent_24h_issue_counts`.

## Trajectory Inspector

`scripts/inspect-trajectory.py` builds an ordered route/read/plan/edit/test/
review/repair/stop trajectory from bounded telemetry facts, optional memory
events, and validation-evidence signals. It is a runtime-evidence review view,
not an automatic learning system and not a source of skill-rule mutation.

```bash
python3 scripts/inspect-trajectory.py --telemetry-root <path> --memory-root <path> --repo-hash <repo_hash> --session <session-id>
python3 scripts/inspect-trajectory.py --repo-hash <repo_hash> --format markdown
python3 scripts/inspect-trajectory.py --repo-hash <repo_hash> --format json
python3 scripts/inspect-trajectory.py --repo-hash <repo_hash> --generate-candidates
```

With no matching telemetry, it prints `no samples found` and exits 0. Markdown
reports include the stage timeline, changed/read path summary, validation
freshness, review/repair status, issues, and suggested next gates. JSON reports
emit both `trajectory` and `trajectory_report` objects. The trajectory object
includes derived `ordered_events`, `changed_paths`, `read_paths`,
`validation_timeline`, `review_repair_timeline`, `memory_hits`, and
`adapter_degradations` summaries. The report includes a closure `verdict`,
normalized `findings`, validation freshness, repair/re-review status, residual
risk status, and human-review-only candidate fixture metadata.

The analyzer checks deterministic execution-quality gaps: edit before read,
plan before repository context, missing implementation preflight, missing or
stale validation, validation command without outcome, implementer self-review,
repair without re-review, stop without residual risk, incomplete route manifest,
repeat failure without route repair, and fragile-file changes without memory,
preflight, read, and test evidence. Unsupported adapter closure overclaims are
reported as degraded evidence, not as pass. If a high-severity issue appears,
candidate skeletons may be generated for pressure scenarios, agent-behavior
samples, hook fixtures, validation broker fixtures, and trajectory fixtures.
Skeletons are marked `generated_from_telemetry: true` and
`requires_human_review: true` and must be completed and reviewed by a maintainer
before promotion.

## Evidence Levels

Telemetry and trajectory reports can feed scorecards, but they do not all carry
the same proof strength. Reports must keep these levels distinct:

| Evidence | Meaning |
| --- | --- |
| `structural fixture` | Local deterministic fixture or schema sample passed. This proves shape and policy wiring only. |
| `runtime telemetry fixture sample` | Deterministic executor-adapter fixture-derived bounded facts. This proves sample shape only, not live runtime behavior. |
| `live runtime telemetry sample` | Actual hook runtime fact sample was observed. It may still require human review. |
| `promoted golden case` | A human-reviewed case was admitted to regression coverage. |
| `live pass-rate` | Measured real-task success rate. If not collected, render `not_collected`. |
| `token overhead` | Measured additional token cost. If not collected, render `not_collected`. |
| `turn overhead` | Measured additional turn cost. If not collected, render `not_collected`. |

Generated candidates are never measured evidence until a maintainer reviews and
promotes them. Missing live runtime telemetry, live pass-rate, token overhead,
or turn overhead data must remain `not_collected`; it must not be inferred from
structural fixtures, fixture telemetry, or local validator success.

### Completion-Evidence Detection Family

A completion claim must rest on fresh validation evidence. A validation-looking
command observed earlier in the turn is recorded only as command presence; the
stop closure still needs a strong evidence signal such as the command plus an
outcome, exit code, output, or artifact. Text that says validation was not run
(`not verified`, `not run`, `unable to run`, `未验证`, `没有运行`, `无法运行`) is
treated as negative validation evidence. The Validation Broker adds a bounded
freshness check using hook event order when available: validation must finish
after the latest material edit, or the broker records stale negative evidence.
The stop gate records a presence-only `completion_language_detected` fact, and
the review tool pairs it with the absence of validation evidence. The
completion-evidence family is:

- `unverified_completion_claim` — fact-detected: the stop closure used completion
  language after an engineering surface but recorded no validation evidence. Routed to
  `agent-execution-discipline` and `quality-test-gate`.
- `success_language_without_evidence`, `partial_validation_overclaimed`,
  and `delegated_agent_report_trusted_without_independent_check` — recognized
  categories that fact-only telemetry cannot reliably detect because it does not
  capture raw claim wording or delegation chains. `stale_validation_reused` is
  now detected when hook event order proves validation finished before the latest
  material edit; older sessions without order facts remain human-review cases.

Fact telemetry never records prompts or output, so the family deliberately
auto-detects only what the recorded facts support and leaves the rest to pressure
evals and human judgement.

Review reports and doctor summaries surface `unverified_completion_claims`,
`validation_command_without_outcome`, `incomplete_required_references`, and
`pressure_candidate_suggestions` directly in their summaries so these closure
gaps are visible without digging through `issue_counts`.

## Step 2: Review Suggestions By Hand

Open `suggestions/<date>-suggestions.yaml`. Each entry is a candidate, not a
verdict. Decide which are real, which are noise, and which point at a hook false
positive or false negative. The review tool cannot and does not apply anything.

## Step 3: Promote A Suggestion Into A Candidate

`scripts/promote-telemetry-suggestion.py` turns one reviewed suggestion into a
candidate golden routing case, hook fixture, agent-behavior sample, or pressure
scenario. It is a dry run by default and only writes with `--write`. It refuses
to target skill rule files even when `--target` is passed.

```bash
python3 scripts/promote-telemetry-suggestion.py --id <suggestion-id> --suggestions <path>
python3 scripts/promote-telemetry-suggestion.py --id <suggestion-id> --suggestions <path> --write
# Promote a suggestion into a pressure scenario instead of its default target:
python3 scripts/promote-telemetry-suggestion.py --id <suggestion-id> --suggestions <path> --target evals/pressure --write
```

Suggestions whose type is `missed_router`, `missed_implementation_structure`,
`missed_validation_evidence`, `missed_residual_risk`, or
`unverified_completion_claim` are marked `pressure_candidate: true`, signalling
that a human may promote them into a pressure scenario under `evals/pressure/`.
Promotion is always human-driven; the review tool never sets a pressure target on
its own.

Generated files carry `generated_from_telemetry: true`,
`requires_human_review: true`, and `source_suggestion_id`. They are skeletons
with TODOs. Complete them by hand, then:

1. for `evals/routing/<case>.yaml`, fill the prompt and expected route, then run
   `python3 scripts/eval-routing.py`;
2. for `evals/agent-behavior/samples/<case>.yaml`, fill the expected route and
   captured manifest, then run `python3 scripts/eval-agent-behavior.py`;
3. for `evals/pressure/<case>.yaml`, name the pressure type, fill the prompt and
   the required and forbidden behaviors, move it into the right area subfolder,
   then run `python3 scripts/eval-pressure-behavior.py`;
4. for `tests/fixtures/hooks/<case>.json`, wire it into a hook test and run
   `python3 -m unittest discover -s tests`.

Only commit a candidate after it is complete and the relevant validator passes.

## Step 4: Agent Behavior Eval

`scripts/eval-agent-behavior.py` scores captured, human-reviewed agent outputs
against their expected route manifest. See
[../evals/agent-behavior/README.md](../evals/agent-behavior/README.md). It never
calls a model and prints `no samples found` (exit 0) when empty.

## How This Fits The Validation Workflow

| Tool | Question it answers |
| --- | --- |
| `eval-routing.py` | Do golden routing specs (and optional captured outputs) match the rules? |
| `eval-agent-behavior.py` | Does a captured agent output satisfy its expected route manifest? |
| `eval-pressure-behavior.py` | Does a captured agent result hold up under a declared pressure scenario? |
| `review-agent-telemetry.py` | What did real agent runs miss? (advisory only) |
| `inspect-trajectory.py` | Did a session follow a coherent, evidence-backed execution trajectory? |
| `index-repository.py` | Did repository intelligence produce a current graph for context-pack validation? |
| `validate-repository-graph.py` | Does the repository graph satisfy schema, path, and generated-artifact safety rules? |
| `build-context-pack.py` | Can a bounded task context pack be built from the repository graph? |
| `validate-context-pack.py` | Does the task context pack satisfy source-of-truth, freshness, validation, and safety rules? |
| `validate-project-memory.py` | Do Project Memory schemas, privacy rules, and repeat-failure gates remain valid? |
| `validate-validation-broker.py` | Do Validation Broker registry, parser, freshness, and closure policy rules remain valid? |
| `validate-trajectory.py` | Are trajectory schemas, analyzer rules, renderers, and promotion skeletons valid? |
| `validate-hooks.py` | Are hook scripts safe, offline, and protocol-correct? |
| `validate-installation.py` | Are built `dist/` outputs and hook artifacts correct? |

`doctor` can summarize a review report with `--telemetry-report` or
`--telemetry-root`, and inspect installed project hooks with `--check-hooks`. It
never fixes telemetry and never promotes anything.

## What Stays Manual

- deciding a suggestion is real;
- completing and committing a promoted candidate;
- editing any skill rule, routing rule, or capability;
- enabling hook block mode.

Telemetry makes the loop observable. Humans keep the authority.

## Project Memory Governance

Project Memory Governance extends telemetry with a cache-side engineering memory
layer. It is not an online learning system and it does not replace telemetry,
repository graph, context packs, or human review.

The intended flow is:

```text
hook telemetry facts
  -> optional project memory events in the user cache
  -> deterministic projection and retrieval
  -> warning-only memory gates
  -> review-project-memory.py suggestions
  -> human promotes selected candidates
  -> validation/eval/build verify any authored change
```

Project memory inherits telemetry boundaries:

- It is append-only operational memory, not automatic skill improvement.
- It never auto-edits `SKILL.md`, `src/registry/*.yaml`, routing rules, or
  capabilities.
- Runtime memory writes only under
  `${XDG_CACHE_HOME:-~/.cache}/changeforge/memory/<repo_hash>/`.
- It stores repo/workdir hashes, relative paths, bounded symbols, skill names,
  outcomes, confidence, promotion status, evidence references, and optional
  `source_evidence` hashes for current repository files.
- It does not store raw prompts, environment variables, secrets, full command
  stdout/stderr, user absolute paths, personal archives, or toolbox mappings.

The memory cache layout is:

```text
${XDG_CACHE_HOME:-~/.cache}/changeforge/memory/<repo_hash>/
  events/       # append-only JSONL MemoryEvent records
  projections/  # generated MemorySummary JSON projections
  suggestions/  # human-review-only candidate suggestions
  promoted/     # optional audit trail for approved promotions
```

Memory events use
[`memory-event.v1.schema.json`](../src/project_memory/schemas/memory-event.v1.schema.json).
Memory projections use
[`memory-projection.v1.schema.json`](../src/project_memory/schemas/memory-projection.v1.schema.json).
Memory summaries use
[`memory-summary.v1.schema.json`](../src/project_memory/schemas/memory-summary.v1.schema.json).
The first implementation uses deterministic retrieval only; no vector database
or embedding index is introduced.

`MemoryEvent` v1 keeps legacy `type`, `paths`, and `created_at` for old readers
and adds canonical governed fields:

- `commit_sha`
- `timestamp`
- `kind`
- `bounded_paths`
- `summary`
- `privacy_class`
- `retention_policy`
- `source`
- optional `source_evidence` containing `repo_rel_path`, full sha256
  `source_hash`, `hash_algorithm`, `observed_at_event_id`,
  `observed_at_timestamp`, `graph_freshness`, and `validation_freshness`

Allowed `kind` values are `fragile_file`, `repeat_failure`,
`validation_pattern`, `review_finding_pattern`, `module_convention`,
`generated_source_mapping`, `route_correction`, `false_positive_hook`, and
`false_negative_hook`. The projection records included and excluded event ids,
the retrieval key, stale-context status, residual risk, and
`source_check_required: true`. Retrieval hits expose `source_status`,
`evidence_role`, and retrieval confidence. Memory is never source truth; agents
must still read current repository files before acting. A memory hit can become
closure evidence only when the current file hash matches and current
validation/review freshness exists. Stale, deleted, missing, unknown, generated,
or legacy hashless memory is historical or warning-only.

### Memory Review And Promotion

Use the memory review command to generate projections and candidate
suggestions:

```bash
python3 scripts/review-project-memory.py
```

Use promotion only after human review:

```bash
python3 scripts/promote-memory-candidate.py --id <id> --suggestions <path> --write
```

Promotion can generate only candidate skeletons under:

- `evals/agent-behavior/samples`
- `evals/pressure`
- `tests/fixtures/hooks`
- `tests/project_memory/fixtures`

Promotion refuses direct skill, registry, routing, capability, `dist/`, or
runtime skill edits. Promotion also requires explicit `promotion_type`
(`success_rule`, `failure_pattern`, `fragile_file`, `anti_pattern`, or
`routing_hint`), current `source_evidence` hash validation, current
validation/review evidence, residual-risk classification, and
`requires_human_review: true`. It refuses raw prompt/output/secret-like data,
stale memory, unverified success rules, and generated artifacts without an
explicit source-of-truth reference.

### Memory Gates

Memory gates are pure decision logic with hook runtime integration kept
warning-first and fail-open.

- Repeat Failure Gate: when the same `repo_hash + task_fingerprint +
  primary_path + owner_skill` has two consecutive `failed` or `blocked`
  outcomes, the third same-path strategy must route through failure diagnosis,
  `quality-test-gate`, or `architecture-impact-reviewer`. In block mode it may
  continue only with new evidence or a repair route manifest.
- Fragile File Gate: a file with repeated `review_finding`,
  failed/blocked `validation_result`, `repair_attempt`, or `fragile_file`
  events requires read-file evidence, owner/source-of-truth check,
  same-pattern scan, validator mapping, nearby-test evidence, memory summary
  evidence, and an implementation preflight before edit.
- Stale Context Gate: a context pack whose freshness marker predates changed
  files or a drift trigger cannot be treated as fact. The agent must refresh the
  repository graph/context pack or label the old content as a stale assumption.

Memory evidence is experience evidence. It cannot override repository source,
fresh context packs, validation output, or human review.

## Action-Aware Fields

The v1 telemetry schema is extended compatibly with action-aware hook facts:

- `turn_stage`, `owner_skill`, and `reviewer_skill` identify the active stage
  and skill handoff selected by the runtime.
- `read_evidence_seen`, `review_evidence_seen`, `repair_evidence_seen`,
  `permission_gate_seen`, and `professional_contract_seen` record whether the
  corresponding lifecycle gate observed a bounded fact.
- `professional_injector`, `pre_edit_structure_gate`, `read_context_gate`,
  `review_gate`, `permission_policy_gate`, `subagent_skill_contract`, and
  compaction hooks are accepted `hook_name` values.
- Implementation preflight state is stored as compact summaries and booleans:
  `implementation_preflights`, `implementation_preflight_seen`,
  `implementation_preflight_complete`, `implementation_preflight_required`,
  `edit_without_preflight_seen`, and `post_edit_confirmed_preflight_gap`.
  `implementation_preflight_seen` only means the manifest appeared;
  `implementation_preflight_complete` means the manifest satisfied the fields
  required for the observed edit.
- Risk-surface state is split compatibly:
  `risk_surfaces` remains the legacy field, while
  `changed_path_risk_surfaces`, `command_risk_surfaces`, and
  `closure_risk_surfaces` separate path matches, command matches, and
  closure-relevant engineering risk. Read-only command matches are retained in
  telemetry for review but excluded from code-change closure risk.
- Context-control state is stored in bounded `context_control_records`,
  `tool_output_boundaries`, `artifact_references`,
  `branch_route_repair_summaries`, `route_repair_forbidden_retries`,
  `context_budget_findings`, and `skipped_references` fields.
- `validation_command_detected` records that a validation-looking command was
  observed; it is separate from `validation_evidence_detected`, which requires a
  stop-closure outcome or artifact signal.
- Stop closure can record project-memory facts without blocking by default:
  `project_memory_available`, `project_memory_projection_key`,
  `project_memory_included_events`, `project_memory_excluded_events`,
  `project_memory_stale_context_gate`, and `project_memory_residual_risk`.
  Memory disabled by user policy is recorded as not applicable, while expected
  but unreadable memory remains degraded residual risk. Memory never becomes a
  pass condition.

### Telemetry Memory Candidates

`scripts/review-agent-telemetry.py` emits a `memory_candidates` section in the
report and suggestions file. These candidates are human-review-only and may
point to `memory`, `hook_fixture`, `eval`, `docs`, or `none` as a promotion
target. They are derived from bounded facts such as stale validation, repeated
same-path failures, repair without re-review, fragile-file signals, and hook
false-positive/false-negative candidates. The reviewer does not auto-promote or
edit skills, routing, registries, or capabilities.

These fields are facts about hook behavior, not content capture. Telemetry still
records only path-like facts, compact signal names, command program names, gate
names, and booleans. It must not record prompt text, environment variables,
secrets, full command arguments, command output, absolute paths, or
user-specific archives.
