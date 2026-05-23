# Security Checks

## Threat Surface

The webhook endpoint is internet reachable and can mutate shipment state.
Attackers may forge events, replay old events, tamper with payload bytes, or
probe error responses for secret and configuration details.

## Required Checks

- Use constant time comparison for expected and received signatures.
- Verify the exact raw body bytes and timestamp string used by the provider.
- Enforce timestamp tolerance before accepting the event.
- Store event ids durably before or inside the side effect transaction.
- Redact signature, signing secret, and raw payload from failure logs.

## Rejection Cases

- Any unsigned or stale event can update shipment state.
- Any solution accepts events when the signing secret is missing.
- Any solution stores replay protection only in process memory.
- Any log line includes signing secret or full signature value.