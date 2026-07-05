# Context Package Checklist

Load this reference only when preparing large multi-file handoff context, cross-agent review packets, or L4/L5 change packages. This reference is for task-scoped context packages only; it does not authorize personal asset ingestion, archive mapping, or user-specific corpus discovery.

## Benchmark Anchors

Anchor against: **Anthropic "Effective Use of Claude in Coding" guidance** - minimal sufficient context, explicit task scope, structured fact/inference separation. **OpenAI GPT best practices** - clear instructions, structured formats, explicit constraints reduce hallucination. **LLM context-window research** (Liu et al. 2023, "Lost in the Middle") - models perform best on items at beginning and end of context; critical constraints should appear early. **Cognitive Load Theory (Sweller 1988)** - irrelevant information is not neutral; it increases load and degrades decision quality. **Architecture Decision Records (ADR)** (Michael Nygard, ADR GitHub, adr-tools) - structured decision format: title, status, context, decision, consequences; ideal context unit for architectural constraints. **RFC 2119 MUST/SHOULD/MAY** for expressing constraint strength. **MCP (Model Context Protocol, Anthropic)** - server-side context packaging and tool result annotation. **LlamaIndex / LangChain context summarization** - relevant for long-session context compression. **"Building LLM-Powered Applications" (Chip Huyen)** for grounding vs hallucination tradeoffs. **Google's "Chain of Thought" prompting research** - structured multi-step reasoning improves accuracy; context packages should structure problem decomposition, not leave it implicit. **Code ownership / CODEOWNERS** files for identifying change owners. **C4 Model** (Simon Brown) - context, container, component, code diagrams as levels of context granularity; use C4-level abstractions appropriate to the task scope. **RFC 7807 (Problem Details)** - precise error schema as contract reference pattern. **OpenAPI 3.x / AsyncAPI 2.x / Protobuf / JSON Schema** as canonical contract formats. **Test-Driven Development (TDD)** red/green/refactor model - completion criteria = tests pass, not behavior description.

## Context Package Structure

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
| **Freshness Markers** | Commit SHA, date, source system snapshot - per element | Per cited element |
| **Drift Triggers** | Events that invalidate this package (schema change, contract bump, requirement update) | Specific, not "if anything changes" |
| **Excluded Context** | What was deliberately omitted and why | Prevents "why didn't you use X?" confusion |
| **Owner** | Owner of the task; owners of contracts and boundaries | Named role or team |

## Fact / Inference / Assumption / Open Question Classification

```
FACT:        Citeable to source. File:line, spec section, test name.
             Example: "Service uses HS256 JWT signing. (src/auth/jwt.go:44)"

INFERENCE:   Reasoned from FACT but not directly stated.
             Example: "Adding a new endpoint likely requires the same JWT middleware
             (inference: all existing endpoints in src/api/ use it, lines 12-30)."

ASSUMPTION:  Accepted without verification. Must be labelled + owner notified.
             Example: "ASSUMPTION: Postgres version is >= 15 (unverified; check with
             @platform-team before using MERGE syntax)."

OPEN QUESTION: Must be resolved before implementation proceeds.
             Example: "OPEN: Does the /payments endpoint require idempotency key?
             (Product owner @alice must answer; blocks task start)."
```

## Context Sizing Decision Tree

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

## Anti-examples

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
