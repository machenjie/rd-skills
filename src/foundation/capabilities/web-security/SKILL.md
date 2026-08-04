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

- **Trace changed routes from source to sink.** Identify attacker-controlled values, browser or server transformations, framework defaults, trust transitions, reachable sinks, and alternate encoded or nested paths before selecting a control.
- **Match rendering protection to context.** Preserve contextual escaping, sanitization, trusted-template boundaries, URL and style handling, and script or markup policy for the actual sink; avoid decoding or concatenation after validation.
- **Protect state-changing requests at the authority boundary.** Combine authenticated context with current request-integrity, origin, cookie, method, and object-authorization controls without treating browser UI or route guards as enforcement.
- **Constrain server-side fetching and navigation.** Validate destinations against owned policy, re-check redirects and resolved addresses, block credential forwarding and internal reachability, and preserve safe recovery for rejected targets.
- **Treat uploads and downloads as active content boundaries.** Bound type, size, name, path, archive expansion, scanning, storage authority, rendering disposition, and retrieval authorization according to reachable abuse.
- **Define cross-origin and embedding behavior narrowly.** Derive origin, credential, header, method, framing, opener, and message-channel policy from current consumers and reject ambient wildcard trust.
- **Prove denial and bypass paths.** Exercise alternate encodings, redirects, stale sessions, direct routes, nested payloads, mixed content, unauthorized objects, and deployment policy relevant to the changed sink.

## Anti-Patterns

- Apply one generic sanitizer or allowlist before later decoding, templating, redirect, or parser transformations change the context.
- Trust client validation, hidden UI, same-origin appearance, internal hostnames, file extensions, or authenticated identity as sufficient sink protection.
- Claim a framework default or response header is deployed protection without route and environment evidence.

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
