# Worker and Persistent Channel Contracts

Use this Reference only for the named worker-and-persistent-channel-contracts decision.

## Decision Rules

- Bind worker message schema, transfer ownership, cancellation, termination, and error propagation; an object reference does not prove background persistence.
- Bind WebSocket and SSE authentication, ordering, reconnect cursor, duplicates, gaps, backpressure, visibility behavior, cleanup, and supported browser versions.
- Prevent reconnection from duplicating effects or silently dropping an interval.
- Treat browser scheduling, connection limits, and feature support as implementation- and version-dependent.

Return lifecycle and failure decisions, reconnect or cleanup evidence, validation plan, and residual risk.
