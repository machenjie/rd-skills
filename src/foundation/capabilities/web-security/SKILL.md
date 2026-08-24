---
name: web-security
description: "Use analysis, task, or review agents for reachable web-sink changes; skip without web exposure."
---

# web-security

## Registry Trigger

**Use when**

- review changed web routes from browser or server trust boundary to rendering state-changing fetch upload redirect cross-origin embedding or protected-action sinks

**Do not use when**

- no task-local reachable web boundary or sink behavior changes

## Skill Role

Trace web sources to render, navigation, state-change, fetch, upload, cross-origin, cookie, embedding, or protected-action sinks. Own control-placement and bypass proof, not permission or credential policy.

## High-Value Rules

- Map the changed web source through trust transitions.
- Classify its effective web sink.
- Select the owning control or evidence Reference.
- While that decision is active, load only its named Reference.

## Anti-Patterns

- Reject generic sanitizer, UI signal, hostname, extension, identity, framework-default, or header claims without final-context and deployed-behavior evidence.

## Stop Conditions

- Escalate unknown reachability, missing request integrity/object authorization, or unbounded server-fetch destinations.
- Escalate ambiguous active content, broadened cross-origin credentials, or unverified deployed controls/bypasses.

## Output Contract

- web-security decision with reachable sources and sinks, contextual controls, state-change integrity, fetch and upload boundaries, cross-origin behavior, denial and bypass evidence, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | competing render browser-state fetch upload navigation cross-origin embedding response-policy or protected-route patterns remain viable | one bounded web decision is already complete from the root contract | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | several reachable web surfaces and their handoffs must close together | one bounded web surface is already complete from the root contract | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | route reachability control placement framework behavior denial bypass deployment or residual-scope claims need fresh proof | no task-local web-security claim awaits proof | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
