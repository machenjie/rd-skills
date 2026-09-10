# Service Worker and Cache Contracts

Use this Reference only for the named service-worker-and-cache-contracts decision.

## Decision Rules

- Treat service workers as interruptible event handlers: bind registration scope, version, install, activation, client handoff, cache keys, freshness, fallback, and deletion.
- Prevent old and new code from consuming incompatible cache contents; define bounded offline fallback and recovery.
- Do not depend on persistent execution or infer that BFCache performs network revalidation.
- Bind lifecycle and cache claims to current target-browser tests and application-owned version evidence.

Return the service-worker state decision, cache recovery, exercised failure paths, validation plan, and residual risk.
