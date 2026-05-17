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

# Non-Negotiable Rules

- **Source-grounded, not paraphrased.** Every factual claim in the context package must cite a specific file path, line range, ADR number, specification section, or test name. "The service uses JWT" is only acceptable if followed by `(src/auth/middleware.ts:12–28)`. Uncited claims are inferences, not facts; mark them as such.
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

Anchor against: **Anthropic "Effective Use of Claude in Coding" guidance** — minimal sufficient context, explicit task scope, structured fact/inference separation. **OpenAI GPT best practices** — clear instructions, structured formats, explicit constraints reduce hallucination. **LLM context-window research** (Liu et al. 2023, "Lost in the Middle") — models perform best on items at beginning and end of context; critical constraints should appear early. **Cognitive Load Theory (Sweller 1988)** — irrelevant information is not neutral; it increases load and degrades decision quality. **Architecture Decision Records (ADR)** (Michael Nygard, ADR GitHub, adr-tools) — structured decision format: title, status, context, decision, consequences; ideal context unit for architectural constraints. **RFC 2119 MUST/SHOULD/MAY** for expressing constraint strength. **MCP (Model Context Protocol, Anthropic)** — server-side context packaging and tool result annotation. **LlamaIndex / LangChain context summarization** — relevant for long-session context compression. **"Building LLM-Powered Applications" (Chip Huyen)** for grounding vs hallucination tradeoffs. **Google's "Chain of Thought" prompting research** — structured multi-step reasoning improves accuracy; context packages should structure problem decomposition, not leave it implicit. **Code ownership / CODEOWNERS** files for identifying change owners. **C4 Model** (Simon Brown) — context, container, component, code diagrams as levels of context granularity; use C4-level abstractions appropriate to the task scope. **RFC 7807 (Problem Details)** — precise error schema as contract reference pattern. **OpenAPI 3.x / AsyncAPI 2.x / Protobuf / JSON Schema** as canonical contract formats. **Test-Driven Development (TDD)** red/green/refactor model — completion criteria = tests pass, not behavior description.

### Context Package Structure

A complete context package has the following sections, in order (omit sections only when genuinely irrelevant, with a note):

| Section | Purpose | Precision standard |
| --- | --- | --- |
| **Task Goal** | One-sentence outcome; what done looks like | Objective; citable against requirements |
| **Source Evidence** | Explicit files, commits, specs, ADRs, test cases that govern this task | Path + line range + date |
| **Relevant Files** | Files the agent should read and may modify | Explicit list with purpose |
| **Architecture Boundaries** | Layer rules, service boundaries, module contracts the agent must respect | Cite ADR or architecture doc |
| **API / Data / UI Contracts** | Exact contract references; not paraphrases | OpenAPI path + operation, proto message, JSON Schema |
| **Constraints** | Hard constraints: security, performance budget, backwards compatibility, legal | Cite source; severity: MUST / SHOULD |
| **Non-goals (Do Not Touch)** | Explicit list of what the agent must not change | Named files, behaviors, patterns |
| **Open Questions** | Unresolved decisions that may block or affect implementation | Question + who must answer + deadline |
| **Decisions (FACT / INFERENCE / ASSUMPTION)** | Accepted decisions with source type and citation | Labelled per type |
| **Affected Tests** | Tests that prove completion; tests that must not regress | Named test file + purpose |
| **Quality Gates** | Mechanical / reviewable pass criteria | Specific, checkable |
| **Freshness Markers** | Commit SHA, date, source system snapshot — per element | Per cited element |
| **Drift Triggers** | Events that invalidate this package (schema change, contract bump, requirement update) | Specific, not "if anything changes" |
| **Excluded Context** | What was deliberately omitted and why | Prevents "why didn't you use X?" confusion |
| **Owner** | Owner of the task; owners of contracts and boundaries | Named role or team |

### Fact / Inference / Assumption / Open Question Classification

```
FACT:        Citeable to source. File:line, spec section, test name.
             Example: "Service uses HS256 JWT signing. (src/auth/jwt.go:44)"

INFERENCE:   Reasoned from FACT but not directly stated.
             Example: "Adding a new endpoint likely requires the same JWT middleware
             (inference: all existing endpoints in src/api/ use it, lines 12–30)."

ASSUMPTION:  Accepted without verification. Must be labelled + owner notified.
             Example: "ASSUMPTION: Postgres version is ≥ 15 (unverified; check with
             @platform-team before using MERGE syntax)."

OPEN QUESTION: Must be resolved before implementation proceeds.
             Example: "OPEN: Does the /payments endpoint require idempotency key?
             (Product owner @alice must answer; blocks task start)."
```

### Context Sizing Decision Tree

```
Will including this element change what the agent implements?
├─ No  → EXCLUDE. Note it in "Excluded Context" if a reviewer might ask.
└─ Yes →
    Is the element fresh (source unchanged since cited date)?
    ├─ No  → UPDATE before including, or mark as STALE and add to Open Questions.
    └─ Yes →
        Is it directly citeable (file:line, spec:section, ADR:number)?
        ├─ Yes → Include as FACT with citation.
        └─ No  → Classify as INFERENCE or ASSUMPTION; label accordingly.
```

### Anti-examples

| Anti-pattern | Consequence |
| --- | --- |
| "The API returns user data" (no spec, no schema reference) | Agent invents response shape; contract mismatch discovered at integration |
| Full `src/` directory listed as "relevant files" | Agent reads 200 files; critical constraint buried; ignored |
| Open question buried in "Background" section | Agent assumes an answer; implements against a wrong constraint |
| Schema from 6 months ago, no freshness date | Agent implements against a schema that was migrated away; migration work repeated |
| "Implement this correctly" as completion criterion | No objective way to know when done; review is subjective |
| "The auth flow uses OAuth" (no cited file) | Agent may implement a different OAuth flow than the one in use |
| No "Do Not Touch" section | Agent refactors shared util; breaks 12 other modules |
| Secrets or API tokens in context package | Leaked in logs, summaries, transferred sessions; credential exposure |
| "Assume latest library version" without checking lockfile | Agent generates code for an API that doesn't exist in the pinned version |

# Selection Rules

Select this capability when **task context transfer to an AI coding agent** is primary. Adjacent routing:

- Prefer `task-dag-decomposition` when the work still needs sequencing, dependencies, and execution ordering.
- Prefer `requirement-clarification` when unresolved intent must be resolved before context can be packaged.
- Prefer `code-review` when evaluating a diff that has already been produced.
- Prefer `documentation-generation` when producing durable operator or user-facing documentation.
- Prefer `scenario-decomposition` when the context still needs to be broken into executable scenarios.
- Use **with** `acceptance-standard-definition` so completion criteria are acceptance-criteria-grade, not informal.

# Risk Escalation Rules

Escalate when the context package: includes security-sensitive details (auth flows, privilege escalation paths, injection surfaces) that require a threat model review before implementation; contains contradictory requirements from different owners (contract ambiguity → implementation risk); is based on stale architecture that was superseded without the agent's knowledge; includes unverified generated claims from a prior agent that are being used as facts; references contracts that are in active draft (implementation against an unstable contract); covers a scope large enough that agent failure could cause data loss, security regression, or production incident; or cannot be produced without resolving an open question that blocks all sensible implementations.

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

# Output Contract

Return a context package with:

- `task_goal` (one sentence; objective; citable against requirement)
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
- `drift_triggers` (specific events that invalidate this package)
- `excluded_context` (what was deliberately omitted + reason)
- `owner` (task owner; contract owners; boundary owners)
- `package_version` and `created_at`

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

# Used By

- task-dag-planner
- ai-code-review-refactor

# Handoff

Hand off to `task-dag-decomposition` for execution planning and dependency sequencing; `requirement-clarification` for resolving open questions; `code-review` for diff assessment after implementation; `documentation-generation` for durable documentation from the implemented result; `acceptance-standard-definition` for converting completion criteria into acceptance-grade evidence.

# Completion Criteria

The capability is complete when **the AI coding agent receiving the package can determine: exactly what to change, exactly what to leave alone, exactly what contracts govern the change, exactly how to verify completion, and exactly when the package becomes stale** — with every constraint source-cited and every open question explicitly resolved or escalated before implementation begins.
