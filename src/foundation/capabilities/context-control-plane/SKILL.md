---
name: context-control-plane
description: Controls ChangeForge runtime context budgets, selected references, JIT repository retrieval, tool-output boundaries, compaction snapshots, branch summaries, route repair, and overhead evidence for routing decisions.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "128"
changeforge_version: 0.1.0
---

# Mission

Select, cap, preserve, and verify the smallest high-signal ChangeForge context needed for the current engineering decision by coordinating route budgets, selected references, just-in-time repository reads, tool-output boundaries, compaction snapshots, branch route-repair summaries, and overhead evidence.

# When To Use

Use this capability when a ChangeForge route, hook runtime, eval fixture, benchmark, compaction handoff, branch summary, or context package can fail because the context window is too large, too stale, too sparse, privacy-sensitive, or missing a record of why references were selected or skipped.

# Do Not Use When

Do not use this capability for ordinary small edits where the selected professional skill and one or two direct source reads are enough. Do not use it to create a generic context-engineering top-level skill, install foundation capabilities directly, ingest personal archives, dump repository graphs, store raw prompts, preserve secrets, copy environment variables, save full command output, or treat hook runtime context as a source corpus.

# Stage Fit

Use during routing, planning, skill-authoring, hook-runtime review, eval design, validation, code review, compaction recovery, branch handoff, and final closure when route context must be bounded and auditable. Re-enter after material edits that change selected skills, selected capabilities, required references, generated route outputs, benchmark evidence, or validation status. Skip when no context-risk signal exists and the route can stay L1/L2 without additional control.

# Non-Negotiable Rules

- Route context is a decision aid, not a data lake. Include only what the current route, gate, validator, or handoff needs.
- Every selected reference must have a reason tied to the task, risk trigger, stage, product surface, or changed path.
- Every skipped relevant reference must have a short reason, especially when it would otherwise be expected by a selected capability.
- Repository graphs, generated reports, and command outputs are selectors; do not paste them as whole artifacts into route context.
- Use just-in-time retrieval for source files, contracts, tests, and docs after the route identifies the need; do not preload broad repository content.
- Tool output passed to downstream context must be bounded to outcome, relevant excerpt, artifact path, and residual risk.
- Compaction snapshots preserve route, stage, validation, review, and open-risk state, not hidden chain-of-thought or raw command streams.
- Branch route-repair summaries preserve what changed, what was re-routed, what was revalidated, and what remains unverified.
- Hook runtime injection remains advisory and fail-open; it must not block tool execution unless a maintainer explicitly enables stricter behavior.
- Privacy boundaries exclude raw prompts, secrets, environment values, credentials, production personal data, full diffs, full files, personal archives, and private mapping artifacts.
- Live Codex or agent-behavior benchmark execution requires an explicit maintainer flag; structural fixtures may run without live model calls.

# Industry Benchmarks

Anchor context control on retrieval-augmented generation discipline, context-window budget management, source-grounded evidence selection, privacy-minimal telemetry, replayable evaluation fixtures, fail-open developer tooling, and explicit cost/quality tradeoff records. Load the references only for the active control mode.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities |
| --- | --- | --- | --- | --- |
| Route budget control | Context budget, reference bloat, over-routing, under-routing, token overhead. | Cap selected capabilities and references while preserving required risk coverage. | Budget mode, selected/skipped refs, route rationale, residual risk. | `change-forge-router`, `skill-efficacy-benchmark` |
| JIT repository retrieval | Repo graph, context pack, changed path, source-truth uncertainty. | Use graph and route signals to read only needed files at the right time. | Selector signal, paths read, paths skipped, freshness note. | `repository-context-map`, `repository-graph-analysis` |
| Tool-output boundary | Long command output, benchmark report, validation log, hook trace. | Preserve proof without polluting route context or leaking sensitive material. | Command, outcome, relevant excerpt, artifact path, excluded output. | `validation-broker`, `agent-tool-permission-sandbox` |
| Compaction snapshot | Context lost after compaction, session transfer, stale prior summary. | Preserve route/stage/validation/review state in bounded form. | Snapshot fields, accepted/stale claims, next gate, residual risk. | `execution-trajectory-analysis`, `plan-execution-consistency` |
| Branch route repair | Branch switch, rebase, merge, repaired route, changed fixture output. | Rebuild route assumptions after branch context changes. | Previous route, changed files, reroute result, validation delta. | `agent-execution-discipline`, `quality-test-gate` |

# Selection Rules

Select this capability when a prompt or route mentions context budget, token overhead, reference bloat, selected references, skipped references, just-in-time retrieval, graph-as-selector, tool-output boundary, artifact reference, compaction snapshot, branch summary, route repair, lost context, stale route, output truncation, hook injection overhead, benchmark overhead, over-routing, or under-routing.

Use it with `context-packaging` when a context package is built, compacted, reused after edits, or included in route closure. `context-packaging` owns the task handoff package; `context-control-plane` owns budget mode, selected/skipped references, just-in-time retrieval, tool-output boundary, snapshot requirements, route-repair summary, and overhead evidence.

Use it with `validation-broker` when validation output or benchmark reports would otherwise enter context as full logs. Use it with `execution-trajectory-analysis` when prior commands, compaction, repair, or final material edits determine freshness. Use it with `skill-efficacy-benchmark` when a routing or reference-loading change claims better professionalism or efficiency.

# Risk Escalation Rules

Escalate when: a selected route requires many foundation references; a generated graph or report is treated as payload instead of selector; validation evidence is too long to quote safely; a compaction summary omits route, stage, changed paths, validation, review, or residual risk; a branch change invalidates selected references; benchmark overhead is unknown while claiming improvement; hook runtime injection stores raw prompt or command output; or a small change starts selecting broad professional surfaces without a concrete risk trigger.

# Proactive Professional Triggers

- **Signal:** Selected capabilities or references exceed the route budget. **Hidden risk:** context bloat hides the decisive source facts. **Required professional action:** switch to staged-plan or full mode only with rationale, record skipped references, and keep JIT reads. **Route to:** `skill-efficacy-benchmark`, `plan-execution-consistency`. **Evidence required:** budget mode, selected/skipped counts, over-budget reason, residual risk.
- **Signal:** A repository graph, context pack, or generated report is available. **Hidden risk:** the graph becomes a dumped corpus. **Required professional action:** use it as a selector and read only source files needed by the route. **Route to:** `repository-graph-analysis`, `repository-context-map`. **Evidence required:** selected nodes, omitted nodes, freshness, direct reads.
- **Signal:** Tool output is long, sensitive, or mostly irrelevant. **Hidden risk:** logs, secrets, environment values, or full outputs enter handoff context. **Required professional action:** keep outcome, relevant excerpt, artifact path, and excluded-output rationale. **Route to:** `agent-tool-permission-sandbox`, `validation-broker`. **Evidence required:** command, outcome, bounded summary, privacy exclusions.
- **Signal:** Context was compacted or a prior summary is reused. **Hidden risk:** route, validation, review, and open risks are silently stale. **Required professional action:** create a compaction snapshot and verify final material edits after the snapshot. **Route to:** `execution-trajectory-analysis`, `validation-broker`. **Evidence required:** snapshot fields, stale claims, rerun or not-run validators.
- **Signal:** A branch, rebase, merge, or route repair changed the working context. **Hidden risk:** previous routing decisions no longer match files or fixtures. **Required professional action:** write a branch route-repair summary and rerun mapped route/registry validators. **Route to:** `agent-execution-discipline`, `quality-test-gate`. **Evidence required:** changed paths, previous route, repaired route, validation delta.

# Critical Details

Budget modes are `minimal`, `single-stage`, `staged-plan`, and `full`. `minimal` is for L1/L2 direct fixes; `single-stage` is for one professional stage and selected references; `staged-plan` is for multi-surface or staged work; `full` is exceptional and must name why smaller modes are unsafe. The route may select many capabilities, but the loaded reference set should stay below the budget unless the risk trigger explains the expansion.

The control plane does not make repository facts true. It records why a source, graph node, test, validator, or reference was read, skipped, summarized, or deferred. It also records what the evidence does not prove so final handoff cannot inflate bounded context into full verification.

# Failure Modes

- A route selects every plausible foundation capability and the decisive validation rule is lost in a long context window.
- A context package includes an entire repository graph instead of selected files, tests, and contracts.
- A command log with secrets, environment values, or unrelated failures is pasted into a handoff.
- A compaction summary preserves the goal but omits changed files, route state, validation status, and open risks.
- A branch switch keeps stale selected references and misses a new registry or fixture requirement.
- A benchmark claims reduced overhead while token, turn, selected-reference, and skipped-reference fields are absent.
- A hook runtime prompt stores raw user text or full command output as persistent state.

# Reference Loading Policy

- **L1 budget check:** Use this `SKILL.md` plus [references/checklist.md](references/checklist.md) to decide whether context control is needed and to close ordinary route records.
- **L2 route budget:** Load [references/context-budget-policy.md](references/context-budget-policy.md) and [references/reference-signal-density-policy.md](references/reference-signal-density-policy.md) when selected references, skipped references, over-routing, or under-routing are at issue.
- **L3 retrieval/output control:** Load [references/jit-retrieval-policy.md](references/jit-retrieval-policy.md) and [references/tool-output-boundary-policy.md](references/tool-output-boundary-policy.md) when repository graph, generated reports, command output, validation logs, or tool traces influence context.
- **L4/L5 continuity:** Load [references/compaction-snapshot-policy.md](references/compaction-snapshot-policy.md), [references/branch-route-repair-summary.md](references/branch-route-repair-summary.md), and [references/overhead-evidence-policy.md](references/overhead-evidence-policy.md) when session continuity, route repair, benchmark overhead, or release evidence depends on preserved context state.
- Do not load unrelated references, personal corpora, private archives, full diffs, full files, or all hook runtime state.

# Output Contract

Return a `context_control` record with:

- `budget_mode` (`minimal`, `single-stage`, `staged-plan`, or `full`).
- `budget_rationale`.
- `max_selected_capabilities` and `max_required_references`.
- `selected_capabilities` and `selected_references` with one-line reasons.
- `skipped_references` with one-line reasons.
- `jit_retrieval_required` and `jit_retrieval_plan`.
- `tool_output_boundary_required` and `tool_output_boundary`.
- `compaction_snapshot_required` and `compaction_snapshot_fields`.
- `branch_route_repair_summary_required` and `branch_route_repair_summary_fields`.
- `overhead_evidence_required` and `overhead_evidence`.
- `privacy_exclusions`.
- `validation_commands`.
- `what_evidence_proves` and `what_evidence_does_not_prove`.
- `residual_context_risk`.

# Evidence Contract

Close context control only when these answers are concrete: route budget mode; selected and skipped references; JIT retrieval plan; tool-output boundary; compaction snapshot requirement; branch route-repair summary requirement; overhead evidence status; privacy exclusions; validation commands; what evidence proves; what evidence does not prove; rollback or reroute note; residual risk; and next gate.

# Quality Gate

1. Context budget mode matches task complexity, stage, risk triggers, and selected capabilities.
2. Selected references are task-relevant, bounded, and justified.
3. Skipped relevant references have reasons and residual-risk status.
4. Graphs, generated reports, and command outputs are selectors or bounded artifacts, not context dumps.
5. JIT retrieval reads current source before using repository facts.
6. Tool-output summaries exclude raw prompts, secrets, environment values, full command output, full diffs, full files, personal archives, and private mapping artifacts.
7. Compaction snapshots preserve route, stage, changed paths, validation, review, open questions, and residual risk.
8. Branch route-repair summaries compare previous and repaired route state.
9. Overhead evidence includes selected/skipped reference counts and token/turn fields or `not_collected`.
10. Hook runtime support remains advisory and fail-open.
11. Validation commands run or are explicitly marked not-run with evidence limits.
12. Final handoff states what context was inspected, what remains unknown, and validation limits.

# Used By

- change-forge-router
- quality-test-gate
- ai-code-review-refactor
- change-documentation-gate
- skill-authoring-expert
- agent-execution-discipline

# Handoff

Hand off budget and selected-reference decisions to `change-forge-router`, validation evidence boundaries to `validation-broker`, benchmark overhead records to `skill-efficacy-benchmark`, review concerns to `ai-code-review-refactor`, and durable documentation changes to `change-documentation-gate`.

# Completion Criteria

The capability is complete when route context is bounded, selected references are justified, skipped references are explained, JIT retrieval and tool-output boundaries are explicit, compaction or branch-repair state is preserved when needed, privacy exclusions are enforced, overhead evidence is recorded, and validation evidence cannot be overstated.

# Benchmark Coverage

This capability covers route budget selection, reference signal density, selected/skipped reference records, JIT repository retrieval, tool-output summarization, compaction continuity, branch route repair, hook-runtime overhead boundaries, over-routing guards, under-routing guards, and privacy-safe structural fixtures.
