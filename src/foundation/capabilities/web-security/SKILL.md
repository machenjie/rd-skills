---
name: web-security
description: "`analysis-agent`/`task-agent`/`review-agent`: use for render sinks, browser state, server fetch, upload, redirect, cross-origin, or embedding changes; skip without web exposure."
---

# web-security

## Registry Trigger

**Use when**

- review changed web routes from browser or server trust boundary to rendering state-changing fetch upload redirect cross-origin embedding or protected-action sinks

**Do not use when**

- no task-local reachable web boundary or sink behavior changes

## Skill Role

Trace web-controlled sources to render, navigation, state-change, fetch, upload, cross-origin, cookie, and embedding sinks with control-placement and bypass evidence. Exclude general permission and credential policy.

## High-Value Rules

- Map the changed web-controlled source through transformations and trust transitions.
- Classify its actual render, state-change, fetch, upload, navigation, cross-origin, embedding, or protected-action sink.
- Select the named decision or evidence Reference for controls and bypass proof.
- When the selected web-security decision remains active, load only its named Reference.

## Anti-Patterns

- Do not infer sink protection from a generic sanitizer, client/UI signal, hostname, extension, identity, framework default, or response header without final-context and deployment evidence.

## Stop Conditions

Escalate when source-to-sink reachability is unknown, state change lacks request integrity or object authorization, or server fetch can reach untrusted destinations. Also escalate when active-content handling is ambiguous, cross-origin credentials broaden, or deployed control and bypass behavior cannot be verified.

## Output Contract

- web-security decision with reachable sources and sinks, contextual controls, state-change integrity, fetch and upload boundaries, cross-origin behavior, denial and bypass evidence, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | competing render browser-state fetch upload navigation cross-origin embedding response-policy or protected-route patterns remain viable | one bounded web decision is already complete from the root contract | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | several reachable web surfaces and their handoffs must close together | one bounded web surface is already complete from the root contract | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | route reachability control placement framework behavior denial bypass deployment or residual-scope claims need fresh proof | no task-local web-security claim awaits proof | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
