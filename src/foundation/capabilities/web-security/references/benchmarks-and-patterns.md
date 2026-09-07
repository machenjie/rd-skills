# Web Security Benchmarks And Patterns

Load when multiple web-boundary patterns remain viable; never as a vulnerability catalog.

## Web Boundary Decisions

| Decision | Compare | Proof |
| --- | --- | --- |
| Render | Safe construction, contextual encoding, inert/no interpretation. | Final context/helper, hostile/context-switch path, response transform. |
| State change | Request authority, trusted origin/binding, owned step-up, no ambient authority. | Credentials/navigation/session/retry/enforcement; denied cross-site. |
| Server connection | Network policy, intermediary fetch, bounded class, no caller influence. | Accepted/canonical input, bounds, resolution-to-connect, redirects, egress, failure, diagnostics owner. |
| Upload/publication | Reject/transform/isolate/inspect/private/bounded publish. | Byte/parser bounds, storage/tenant identity, inspection, active content, permission, transition, serving. |
| Navigation/policy | Same-site, bounded external, cross-origin, framed, no exposure. | Client/destination authority, credentials, effective policy/transform, bypass. |
| Protected route | Authenticated subject plus permission-owned resource/action. | Trace/provenance, object/tenant scope, wrong subject, denial, audit owner. |
| Closure | Repair, containment, deployment proof, non-applicability, residual handoff. | Final source, hostile/denied case, sibling scan, relevant artifact, limit, owner. |

## Selection Guardrails

- Select from the current browser/server path, boundary, authority, and failure contract.
- Apply framework-, client-, proxy-, and network-specific behavior behind shared labels.
- Route input source/representation/canonical form/constraints/response bounds to `input-validation`.
- Route subject authority/derivation/propagation/handoff to `authentication-authorization`.
- Route credential/session/token lifecycle/replay/recovery/assurance/compromise to `authentication-security`.
- Route subject-resource-action policy to `permission-boundary-modeling`.
- Route cross-graph outcomes/reachability/prioritization/control placement to `threat-modeling`.
- Prove route-to-sink correctness/bypass resistance in `web-security`.
- Re-evaluate framework, middleware, proxy, route, redirect, resolver, cache, storage, or serving changes affecting the sink/boundary.

## Proof Limits

Named source, tests, browser artifacts, and deployment configuration prove only inspected routes, clients, intermediaries, environments, and time. They exclude undiscovered routes, production resolver/egress state, external consumers, proxy overrides, browser variants, live attackers, and downstream permission policy without independent evidence.
