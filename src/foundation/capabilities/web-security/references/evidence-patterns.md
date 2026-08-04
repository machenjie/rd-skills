# Web Security Evidence Patterns

Load this reference when route reachability, control placement, framework behavior, denial, bypass, deployment, or residual-scope claims require fresh proof. Do not use it as a vulnerability or mechanism checklist.

| Claim | Minimum fresh evidence | Proof limit |
| --- | --- | --- |
| Reachable web graph is bounded | Current routes, middleware order, framework helpers, transforms, final sinks, sibling scan, and unknown-path classification | Does not establish generated, deployed, or externally owned paths not inspected |
| Rendering protection matches the sink | Final interpretation context, helper or construction contract, hostile value, context-switch case, and effective response artifact | Does not prove sibling contexts, browser variants, or proxy transformations |
| Browser state change is request-bound | Credential attachment behavior, session context, trusted request or origin signal, navigation/retry path, enforcement point, and denied cross-site case | Does not prove credential or session lifecycle controls owned elsewhere |
| Server connection is destination-bounded | Input-owner accepted destination/canonical form/response bounds plus name/address resolution-to-connect, redirect behavior, egress decision, failure case, and diagnostics sample | Does not prove production resolver, proxy, network policy, or future destination state |
| Upload publication is separated | Input-owner byte/parser-bound proof plus storage identity, tenant binding, inspection/transformation state, active-content case, permission-owner publication decision, publication-state transition, and serving context | Does not prove external scanner quality or uninspected storage and delivery paths |
| Browser and response policy is effective | Redirect/cross-origin/embedding/client contract, configured policy, middleware/proxy diff, browser or protocol case, and bypass check | Does not prove CDN overrides, unrelated clients, or browser behavior outside inspected cases |
| Protected route handoff is enforced | Subject provenance, route-to-permission-decision trace, object or tenant scope, wrong-subject or wrong-tenant case, denial result, and audit owner | Does not establish the complete permission model or credential lifecycle |

## Freshness And Closure

- Treat prior reviews, framework defaults, scanner output, browser captures, generated routes, architecture notes, and compaction summaries as search leads until current routes, sinks, configuration, owner, and environment match.
- Re-run applicable hostile and denied cases after the final route, template, helper, middleware, resolver, redirect, upload, storage, permission handoff, response-policy, or deployment edit.
- Map final confidence to current source/config paths, parsed outcomes, browser or deployment artifacts when relevant, sibling-scan scope, owner evidence, and explicit residual paths.
- Keep production resolver/egress state, external storage or delivery, proxy overrides, undiscovered routes, live attacker behavior, authentication lifecycle, and permission-policy completeness outside the proven boundary unless independently verified.
