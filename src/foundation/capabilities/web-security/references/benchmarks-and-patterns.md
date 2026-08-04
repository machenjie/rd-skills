# Web Security Benchmarks And Patterns

Load this reference when current route evidence leaves multiple render, browser-state, fetch, upload, navigation, cross-origin, embedding, response-policy, or protected-route patterns viable. Do not load it to copy a vulnerability taxonomy or fixed control catalog.

## Web Boundary Decisions

| Decision | Compare | Required proof |
| --- | --- | --- |
| Rendering sink | Framework-safe construction, context-specific encoding, inert representation, or removal of untrusted interpretation | Final browser context, helper contract, hostile value, context-switch path, and response transform |
| Browser state change | Explicit request authority, trusted origin or request binding, step-up owned elsewhere, or a flow that carries no ambient authority | Credential attachment behavior, navigation path, session context, retries, enforcement point, and denied cross-site case |
| Server-side connection | Current network-policy decision, intermediary fetch service, bounded connection class, or removal of caller influence | Input-owner accepted representation, canonical form, and response bounds plus name/address resolution-to-connect, redirects, egress authority, failure behavior, diagnostics, and owner |
| Upload storage and publication | Reject before storage, transform, isolate, inspect, store privately, or publish through a bounded representation | Input-owner byte/parser bounds plus storage identity, tenant binding, inspection/transformation state, active-content behavior, permission-owner publication decision, publication-state transition, and serving context |
| Navigation and browser policy | Same-site navigation, bounded external destination, cross-origin read/write, framed experience, or no browser exposure | Client contract, destination authority, credential behavior, effective response policy, intermediary transform, and bypass case |
| Protected route handoff | Existing authenticated-subject context plus resource/action decision owned by the permission boundary | Route-to-decision trace, subject provenance, object or tenant scope, wrong-subject case, denial contract, and audit owner |
| Closure and residual scope | Repair, containment, deployment proof, explicit non-applicability, or residual-risk handoff | Final-edit source, hostile or denied case, sibling scan, effective deployed artifact when relevant, proof limit, and owner |

## Selection Guardrails

- Select route-to-sink web-specific mechanisms from the actual browser or server path, selected boundary, authority, and failure contract; a shared label can require different behavior across frameworks, clients, proxies, and network environments.
- Keep input source, accepted representation, canonical form, structural/resource constraints, and external-response bounds with `input-validation`; authenticated-subject authority/derivation/propagation/handoff with `authentication-authorization`; credential/session/token lifecycle/replay/recovery/assurance/compromise with `authentication-security`; and subject-resource-action policy with `permission-boundary-modeling`.
- Keep cross-graph protected outcomes, abuse-path reachability/prioritization, and candidate control placement with `threat-modeling`; this Skill proves correctness and bypass resistance of the selected web mechanism from route to sink. Re-evaluate framework, middleware, proxy, generated route, redirect, resolver, cache, storage, and serving behavior when it can change that sink or boundary.

## Proof Limits

Scoped source, tests, browser artifacts, and deployment configuration prove their named routes, clients, intermediaries, environments, and time boundary. They do not establish undiscovered routes, production resolver or egress state, external consumers, proxy overrides, browser variants, live attacker behavior, or downstream permission policy unless independently verified.
