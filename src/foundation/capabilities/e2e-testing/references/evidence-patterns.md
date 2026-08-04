# E2E Testing Evidence Patterns

These records distinguish assembled-journey proof from lower-level and production claims.

## Journey Claim

- Name the journey, role, tenant, starting state, route or entry point, assembled dependencies, and critical branch.
- Link the changed behavior to the test path and explain why component, API, integration, or contract proof leaves material risk.
- Record the user-visible oracle, authoritative durable-state oracle, forbidden effects, and readiness condition.

## Execution Claim

- For a run, record the scoped command, environment, selected browser/device/version, result, final-edit freshness, and the artifacts actually used to diagnose or support the claim.
- Record each retained screenshot, trace, video, console, or network artifact's classification, minimized capture scope, redaction, access boundary, retention expiry, disposal owner, and deletion status.
- For planned or unavailable execution, record the reason, missing environment or authority, release consequence, owner, and next gate without inventing output.
- Mark evidence stale after material route, fixture, selector, stub, environment, test-config, generated-input, or asserted-behavior changes.

## Isolation And Flake Claim

- Name run-owned data/session keys, setup source, cleanup path, and behavior on assertion failure, timeout, and cancellation.
- For intermittent failure, retain the signature and first failing result; record diagnostic reruns separately.
- A quarantine record names affected journey, observed signature, owner, release consequence, current workaround, and repair or removal trigger.

## Proof Limits

- State untested roles, branches, browsers/devices, versions, locales, external behavior, and production-only conditions.
- State diagnostic artifacts not inspected for sensitive content, redaction not verified, and retention or disposal not executed.
- Route backend authorization completeness, contract compatibility, capacity, and lower-level boundary behavior to their owning proof.
