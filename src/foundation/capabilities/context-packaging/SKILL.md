---
name: context-packaging
description: Packages relevant AI coding context with requirements, architecture, contracts, files, constraints, tests, and quality gates while preventing context drift.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "76"
changeforge_version: 0.1.0
---

# Mission

Produce the **smallest sufficient, freshness-dated, evidence-grounded context package** needed for an AI coding agent to act correctly and completely on a bounded task — without drifting into stale assumptions, irrelevant codebase detail, hallucinated constraints, or invented API contracts — so that every implementation decision can be traced to a named source and every completion criterion is objectively verifiable.

# When To Use

Use this capability when: preparing a task for an AI coding agent (initial handoff), refreshing stale context after requirements, code, or contracts have changed, transferring a task between agents or sessions, summarizing an active implementation for review handoff, recovering from a context-window overflow (re-establishing a clean minimal context), or coordinating multiple parallel agents working on parts of the same system (shared boundary contracts).

# Do Not Use When

Do not use this capability to dump an entire repository or codebase into context — **select and cite**, never broadcast. Do not use it to paraphrase source files when direct file references (path + line range) would be more accurate. Do not use it to preserve obsolete assumptions that contradict current source. Do not embed secrets, credentials, tokens, API keys, or personally identifying production data in context packages. Do not use it as a substitute for running the code, tests, or static analysis that prove behavior.

# Stage Fit

Use during planning, review handoff, repair handoff, validation freshness review, compaction recovery, and cross-agent coordination when the next agent needs bounded source evidence and execution constraints. Re-enter after source, contract, schema, generated artifact, registry, report, validation output, or route changes that can make a prior package stale. Skip when a small direct-source read already answers the question and no handoff, planning, or validation claim depends on packaged context.

# Non-Negotiable Rules

- **Source-grounded, not paraphrased.** Every factual claim in the context package must cite a specific file path, line range, ADR number, specification section, or test name. "The service uses JWT" is only acceptable if followed by `(src/auth/middleware.ts:12–28)`. Uncited claims are inferences, not facts; mark them as such.
- **Prefer generated repository intelligence when available.** Start from a fresh RepositoryGraph and TaskContextPack when the repository provides them, then inspect the selected files directly. A stale graph, missing changed path, mismatched commit, or changed repo hash invalidates the package until re-indexed.
- **Treat project memory as experience, not source.** Memory summaries may flag repeated failures, fragile files, or stale context, but every source fact must still come from current repository evidence, generated repository intelligence, or explicit user-provided material.
- **Minimum sufficient size.** Include only what the agent *must know* to act correctly on this task. Irrelevant context is not neutral — it competes with relevant context and degrades output quality. Omitting irrelevant information is as important as including relevant information.
- **Explicit non-goals and do-not-touch zones.** Every context package declares what the agent must NOT change, even if it appears related. Missing non-goals → scope creep → unintended side effects.
- **Freshness dates and drift triggers.** Each major context element is dated: "Schema as of commit `abc1234` (2026-05-10)" or "ADR-012 supersedes ADR-007 as of 2026-03-01." Context becomes unsafe when the sources it references change; list the specific events that invalidate it.
- **Contracts are included, not summarized.** API contracts (OpenAPI specs, gRPC proto files, AsyncAPI specs, JSON schemas), data contracts, and UI contracts are included by exact reference or excerpt; paraphrases of contracts are not contracts.
- **Unresolved questions are explicitly separated.** Context must distinguish: `FACT` (evidence-backed, citeable), `INFERENCE` (reasoned from evidence, not directly stated), `ASSUMPTION` (accepted without verification — must be labelled and justified), and `OPEN QUESTION` (must be resolved before acting). Burying open questions inside accepted facts produces invalid implementations.
- **Completion criteria are objectively verifiable.** A context package that says "implement correctly" has no completion criterion. Completion criteria name specific tests, specific quality gates, specific acceptance behaviors that can be checked mechanically or by review.
- **No secrets or production PII.** Context packages may be stored, transferred, logged, summarized, or shown to multiple people. Redact credentials, secrets, personal data, and internal IDs that expose production topology.
- **Ownership is declared.** Every change boundary, contract, and architectural constraint names an owner or owning team. The agent must know who to ask, not just what is true.
- **Context is scoped to a task, not to a project.** A "full project context" is not a valid context package. Each package is scoped to a named task (e.g., "implement `POST /payments` handler per contract v2.3").

# Industry Benchmarks

Anchor context packaging on minimal sufficient context, source-grounded facts, freshness markers, explicit exclusions, and verifiable completion criteria. Use [references/checklist.md](references/checklist.md) as the quick checklist; load [references/context-package-checklist.md](references/context-package-checklist.md) only when preparing large multi-file handoff context, cross-agent review packets, or L4/L5 change packages.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities / gates | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| Initial coding handoff | New bounded implementation, bug-fix, or refactoring task. | Give the next agent enough current source truth to plan and edit. | Goal, non-goals, inspected files, contracts, owners, affected tests, validation commands. | `repository-context-map`, `acceptance-standard-definition` | Skip project-wide background and unrelated modules. |
| Stale context refresh | Requirements, schema, report, generated artifact, branch, or validation output changed after prior context. | Replace stale claims with current evidence before planning or closure. | Changed sources, freshness comparison, rejected old facts, direct-source reread, residual risk. | `project-memory-governance`, `execution-trajectory-analysis` | Skip claims that cannot be refreshed or downgrade them to assumptions. |
| Graph-built package | RepositoryGraph, TaskContextPack, caller/test graph, or generated-artifact graph is available. | Use graph evidence as a selector without copying the graph. | Selected nodes, omitted nodes, graph freshness, source-of-truth decision, validation candidates. | `repository-graph-analysis`, `validation-broker` | Skip whole-repository graph dumps. |
| Memory-informed package | Repeat failure, fragile file, stale context, or prior review memory affects scope. | Let memory widen inspection or validation without becoming source fact. | Memory signal, accepted/rejected/stale verdict, current-source confirmation, privacy boundary. | `project-memory-governance`, `security-privacy-gate` | Skip raw prompts, full logs, secrets, and personal archives. |
| Review or compaction handoff | Context-window overflow, session transfer, repair after review, or parallel-agent boundary. | Preserve decisions, constraints, and verification state without hidden assumptions. | Decision ledger, changed files, validation freshness, remaining open questions, next gate. | `ai-code-review-refactor`, `quality-test-gate` | Skip obsolete reasoning that is not tied to current evidence. |

# Selection Rules

Select this capability when **task context transfer to an AI coding agent** is primary. Adjacent routing:

- Prefer `task-dag-decomposition` when the work still needs sequencing, dependencies, and execution ordering.
- Prefer `requirement-clarification` when unresolved intent must be resolved before context can be packaged.
- Prefer `code-review` when evaluating a diff that has already been produced.
- Prefer `documentation-generation` when producing durable operator or user-facing documentation.
- Prefer `scenario-decomposition` when the context still needs to be broken into executable scenarios.
- Use **with** `acceptance-standard-definition` so completion criteria are acceptance-criteria-grade, not informal.
- Use **with** `repository-graph-analysis` when the package should be generated from a graph/context pack rather than a hand-built file list.
- Use **with** `project-memory-governance` when memory-derived repeat-failure, fragile-file, or stale-context signals influence risk, while keeping them out of source-fact sections.

# Risk Escalation Rules

Escalate when the context package: includes security-sensitive details (auth flows, privilege escalation paths, injection surfaces) that require a threat model review before implementation; contains contradictory requirements from different owners (contract ambiguity → implementation risk); is based on stale architecture that was superseded without the agent's knowledge; includes unverified generated claims from a prior agent that are being used as facts; references contracts that are in active draft (implementation against an unstable contract); covers a scope large enough that agent failure could cause data loss, security regression, or production incident; or cannot be produced without resolving an open question that blocks all sensible implementations.

# Proactive Professional Triggers

- **Signal:** A handoff names files or decisions but omits searched paths, files read, source-of-truth status, or owners. **Hidden risk:** the next agent treats prompt memory as repository evidence. **Required professional action:** rebuild a bounded context package from current source and mark omitted areas. **Route to:** `repository-context-map`, `repository-graph-analysis`. **Evidence required:** inspected paths, searches run, accepted/rejected claims, owner or unknown-owner note.
- **Signal:** A prior summary, graph, report, validation pass, or compaction note is reused after later edits. **Hidden risk:** stale context drives planning, review, or completion. **Required professional action:** compare freshness, downgrade stale claims, and rerun or map validators after the final material edit. **Route to:** `execution-trajectory-analysis`, `validation-broker`. **Evidence required:** event order, changed paths, validation command, exit code or not-run status, residual risk.
- **Signal:** Project memory says a file is fragile, a path failed before, or context is stale. **Hidden risk:** memory either overrules source truth or is ignored when it should widen validation. **Required professional action:** classify memory as experience input, confirm or reject it against current source, and map any accepted signal to tests or review. **Route to:** `project-memory-governance`, `quality-test-gate`. **Evidence required:** memory signal, current-source check, accepted/rejected/stale verdict, affected test or review gate.
- **Signal:** A package includes raw repository graph, full command output, environment values, production examples, or broad private data. **Hidden risk:** context bloat and sensitive data leak into logs, memory, or downstream agents. **Required professional action:** redact, summarize as bounded facts, and keep graph output as selected nodes plus omissions. **Route to:** `security-privacy-gate`, `agent-tool-permission-sandbox`. **Evidence required:** retained fields, excluded sensitive fields, graph slice, telemetry boundary.
- **Signal:** Parallel agents, generated clients, contracts, or shared boundaries are involved but no conflict protocol is stated. **Hidden risk:** agents make incompatible edits or regenerate hand-written code. **Required professional action:** package producer/consumer ownership, contract version, permitted change zones, and merge/conflict protocol. **Route to:** `task-dag-decomposition`, `code-review`. **Evidence required:** boundary contract, owner, permitted files, do-not-touch zones, next handoff gate.

# Critical Details

A context package is both a **knowledge transfer artifact and a commitment about what the agent is authorized to change**. These refinements prevent the most common failures:

- **"Lost in the middle" mitigation.** Long context windows cause LLMs to under-attend to material in the middle (Liu et al. 2023). Place the most critical constraints at the **top** of the context package (task goal + hard constraints + non-goals), not buried mid-document. Restate key constraints in the completion criteria at the end.
- **The "no surprises" principle.** A well-packaged context produces no architectural surprises in the output. If the agent's output contains a choice that wasn't addressed by the context, the context was incomplete, not the agent.
- **Contracts vs summaries.** "The API returns a `User` object" is a summary. A contract is: `GET /users/{id} → 200 UserResponse | 404 ErrorResponse` per `api/openapi.yaml#/paths/~1users~1{id}/get`. Summaries drift; contracts are the ground truth.
- **Non-goals are the highest-return investment.** A missing `MUST NOT refactor the payment module` causes an agent to touch 15 files instead of 3. Non-goals are not obvious; they must be stated explicitly.
- **Context expiry on schema change.** A database schema change invalidates any context package that references the old schema. Drift triggers make this explicit; they are not "if anything changes" but "if `src/db/schema.sql` is modified at commit `>abc1234`."
- **Parallel agent coordination.** Multiple agents working on the same system need explicit shared contracts at their boundary. Overlapping change zones → merge conflict or silent behavioral divergence. Context packages for parallel agents should name: shared interface, who produces, who consumes, contract version, and conflict protocol.
- **Context for generated code.** If the agent generates code from an OpenAPI spec, the spec is a fact (cite path); the generated stub is an artifact; the hand-written extension logic is the actual task. Keep these categories distinct to prevent the agent from regenerating hand-written extensions.
- **Completion criteria ≠ acceptance criteria.** Completion criteria are mechanically checkable within the task scope (tests pass, lint clean, type-check passes, no new TODO). Acceptance criteria address user / product behavior. Both should be present for AI coding tasks; they serve different verification stages.
- **Session vs cross-session context.** Within a session, context accumulates; the agent can refer to earlier decisions. Across sessions (or after compaction), the context package is the only reliable record. Cross-session packages must be self-contained; they cannot rely on implied session memory.
- **Redaction of sensitive references.** Instead of a real DB connection string, use `$DB_URL (env var, see secret-configuration-security capability)`. Instead of a real user record, use a synthetic test fixture. Real production data in context = GDPR/compliance exposure.
- **Versioned context packages.** For long-running tasks, version the package itself: `context-v1.md` → `context-v2.md` (after schema bump). Enables rollback understanding and handoff audit trail.
- **Generated graph is a selector, not a payload.** Use graph walks and relevance ranking to choose source-of-truth files, callers, tests, validators, docs, and generated-artifact references. Do not paste the entire graph or repository inventory into an AI-agent handoff.

# Failure Modes

- Agent invents API response shape because no contract was cited; integration test discovers mismatch at end of implementation sprint.
- Critical constraint buried in paragraph 12 of a long background section; agent never applies it; bug ships.
- Open question ("which database should new table live in?") not marked; agent picks one arbitrarily; decision causes data-tier policy violation.
- Context contains schema from 8 months ago; migration has happened; agent writes code against dropped columns.
- "Do Not Touch" not stated; agent helpfully refactors shared infrastructure; 5 unrelated tests break.
- Stale ADR included (superseded but not noted); agent implements a deprecated pattern.
- Completion criterion is "implement this feature"; agent declares done after first passing test; incomplete behavior ships.
- Secret (database password) included in context for "realism"; context stored in session logs; credential exposed.
- "Latest version" assumed; agent uses API from library v4; project pins v3; runtime error.
- Two parallel agents receive overlapping change zones; both modify the same file; changes conflict at merge.
- INFERENCE presented as FACT; agent builds further inferences on top of it; error compounds silently.
- Context package for AI agent reused 3 sprints later without refreshing; freshness dates not checked; stale.
- Completion criterion references a test file that was renamed; agent cannot verify completion; declares done anyway.

# Reference Loading Policy

- **L1 quick package:** Use this `SKILL.md` plus [references/checklist.md](references/checklist.md) for ordinary single-task handoff, compaction recovery, or review transfer.
- **L2 deep package:** Load [references/context-package-checklist.md](references/context-package-checklist.md) for large multi-file packages, cross-agent packets, high-risk boundary work, or L4/L5 changes.
- **L3 coupling:** Pair with `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `agent-tool-permission-sandbox` when graph freshness, memory projection, validation order, or tool-output sensitivity affects package trust.
- **Anti-bloat rule:** Do not load unrelated references, copy whole graphs, include personal corpora, or package user-specific archives; cite only task-relevant sources, omissions, validators, and residual risk.

# Output Contract

Return a context package with:

- `mode_selected` (initial coding handoff, stale context refresh, graph-built package, memory-informed package, or review/compaction handoff)
- `task_goal` (one sentence; objective; citable against requirement)
- `stage_and_handoff` (current stage, receiving owner/skill, next gate, and what the package enables or blocks)
- `repository_graph_evidence` (graph path or artifact id, repo hash, indexed commit or fallback mtime, indexed_at, and stale/re-index status)
- `source_evidence` (per item: source type, path/url, cited section/line, date/commit, fact_class: FACT/INFERENCE/ASSUMPTION)
- `relevant_files` (per file: path, purpose, permitted changes: read-only / modify / create)
- `architecture_boundaries` (per rule: boundary, constraint statement, source ADR/doc, owner)
- `contracts` (per contract: type — API/data/UI, reference path + version, critical operation or schema, owner)
- `constraints` (per constraint: statement, severity — MUST/SHOULD/MAY, source, owner)
- `non_goals` (per item: what must not be changed, reason)
- `open_questions` (per question: statement, blocking?, owner who must answer, deadline)
- `decisions` (per decision: statement, fact_class, citation)
- `affected_tests` (per test: file/test name, what it proves, must-not-regress flag)
- `quality_gates` (per gate: objective check, pass criterion, verification method)
- `freshness_markers` (per major element: commit SHA, date, source snapshot)
- `memory_experience_inputs` (optional repeat-failure, fragile-file, or stale-context signals, clearly labeled as non-source facts)
- `graph_memory_execution_coupling` (graph, memory, prior summary, and trajectory claims accepted, rejected, stale, partial, or not verified)
- `validation_freshness` (commands, tests, validators, reports, artifacts, exit code or not-run status, covered paths, and whether each ran after final material edits)
- `tool_permission_boundary` (read/write command classes, sandbox and approval status, sensitive output boundary, and excluded raw logs or secrets)
- `drift_triggers` (specific events that invalidate this package)
- `excluded_context` (what was deliberately omitted + reason)
- `what_evidence_proves` and `what_evidence_does_not_prove`
- `reuse_and_placement_rationale` (why included files, contracts, and references are sufficient; why excluded locations are out of scope)
- `behavior_preservation` (unchanged behaviors, contracts, tests, and do-not-regress boundaries)
- `residual_risk` (unknown owners, stale or low-confidence evidence, missing validators, and next professional gate)
- `owner` (task owner; contract owners; boundary owners)
- `package_version` and `created_at`

# Evidence Contract

Close a context package only when these answers are concrete: **boundaries inspected**; direct source, graph, memory, and trajectory claims accepted or rejected; **validation evidence** including command, validator, test, report, artifact, and exit code or not-run status; **what evidence proves** and **what evidence does not prove**; reuse / placement rationale for included and excluded files; behavior preservation and do-not-regress boundaries; residual risk; handoff owner; and next gate.

# Quality Gate

The context package passes only when:

1. Every factual claim cites a specific source (file:line, spec section, ADR number, test name).
2. Non-goals and do-not-touch zones are explicitly listed.
3. Open questions are separated and marked with owner and blocking status.
4. FACTs, INFERENCEs, and ASSUMPTIONs are classified and labeled.
5. Contracts are cited by exact reference, not paraphrased.
6. Completion criteria are objectively verifiable (named tests, gates, or mechanical checks).
7. No secrets, credentials, tokens, or production PII are present.
8. Freshness markers are present for schema, contracts, and architectural constraints.
9. Drift triggers are specific (not "if anything changes").
10. The package is scoped to a single named task; not a project-wide dump.
11. "Excluded context" section explains what was deliberately omitted.
12. Generated graph/context-pack facts are separated from agent inferences, assumptions, and open questions.
13. RepositoryGraph content is pruned by task relevance and graph distance; it is never copied as an all-files dump.
14. Memory summaries are labeled as experience inputs and never used as source facts without current-source confirmation.
15. Validation evidence names command/test/validator/report/artifact results, exit code or not-run status, covered paths, and whether proof is current after final material edits.
16. Graph, memory, prior-summary, and execution-trajectory claims are reconciled before they influence package trust, validation depth, or closure.
17. Tool output boundaries exclude raw prompts, secrets, environment values, credentials, personal data, full command output, personal archives, and private mapping artifacts.
18. Residual risk and next professional gate are explicit when evidence is stale, partial, unsupported, or outside the inspected boundary.

# Benchmark Coverage

This capability covers minimal-context AI coding handoff, source-grounded fact classification, graph-selected context packs, memory-as-experience governance, validation freshness, tool-output redaction, contract citation, non-goal enforcement, and anti-bloat exclusion discipline.

# Routing Coverage

Route here when task context must be transferred, compacted, refreshed, de-bloated, graph-selected, memory-informed, or made reviewable before implementation or handoff. Pair with `repository-context-map` for inspected-source mapping, `repository-graph-analysis` for graph slices, `project-memory-governance` for memory signals, `execution-trajectory-analysis` for validation order, `agent-tool-permission-sandbox` for tool-output boundaries, and `quality-test-gate` for proof mapping.

# Used By

- task-dag-planner
- ai-code-review-refactor

# Handoff

Hand off to `task-dag-decomposition` for execution planning and dependency sequencing; `requirement-clarification` for resolving open questions; `code-review` for diff assessment after implementation; `documentation-generation` for durable documentation from the implemented result; `acceptance-standard-definition` for converting completion criteria into acceptance-grade evidence.

# Completion Criteria

The capability is complete when **the AI coding agent receiving the package can determine: exactly what to change, exactly what to leave alone, exactly what contracts govern the change, exactly how to verify completion, and exactly when the package becomes stale** — with every constraint source-cited and every open question explicitly resolved or escalated before implementation begins.
