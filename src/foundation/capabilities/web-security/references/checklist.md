# Web Security Checklist

Load this reference when one change spans several reachable rendering, browser-state, fetch, upload, navigation, cross-origin, embedding, response-policy, or protected-route decisions. Do not load it when the root contract resolves one bounded web surface.

- Trace changed routes through middleware, framework helpers, parsers, policies, storage or transport, response transforms, and final browser or server sinks.
- Classify sibling, generated, admin, support, callback, import, preview, and externally owned routes as inspected, not applicable, or residual scope.
- Identify each final rendering context, the framework safety contract, context switches, and a hostile-value case.
- For browser-authorized state changes, define ambient credential behavior and the trusted request or origin signal.
- Define session, navigation, and retry behavior separately.
- Name the enforcement point and denied cross-site case.
- For server fetches, record the input owner’s accepted destination representation, canonical form, external-response bounds, resolution-to-connect owner, and redirect re-evaluation.
- Define egress authority, web failure behavior, and safe diagnostics.
- For uploads, require input-owner byte and parser-bound proof.
- Own storage identity, tenant binding, required inspection or transformation state, and active-content behavior.
- Define the publication-state transition and serving context after obtaining permission-owner actor, resource, and action evidence.
- Derive redirect, cross-origin, embedding, and response policy from trusted clients and effective-result evidence after middleware, proxy, cache, or hosting transforms.
- Map protected routes to authenticated-subject provenance and an owned resource/action decision before disclosure or effect.
- Select applicable hostile render, unintended browser action, destination-change, redirect/resolution, upload-before-publish, cross-origin, embedding, wrong-subject, and wrong-tenant cases.
- Record final-edit freshness, deployment evidence when required, explicit non-applicability, proof limits, unverified paths, and residual owners.
