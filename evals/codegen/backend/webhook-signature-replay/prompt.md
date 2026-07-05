# Benchmark Prompt

## Task

Secure the inbound shipping webhook endpoint with HMAC signature verification,
timestamp tolerance, replay protection, and idempotent event processing.

## Context

The starter endpoint accepts any POST body and immediately updates shipment
state. The shipping provider sends headers for event id, timestamp, and
signature. The signing secret is configured by environment and can be rotated.

## Requirements

- Verify the HMAC SHA256 signature over the exact raw request body and timestamp.
- Reject timestamps outside a five minute window.
- Store processed provider event ids and skip duplicate processing safely.
- Return deterministic status codes for invalid signature, stale timestamp, and duplicate event.
- Add tests for valid delivery, tampered body, stale timestamp, missing secret, and replay.

## Constraints

- Do not parse and reserialize JSON before signature verification.
- Do not log the signing secret, full signature, or raw untrusted payload on failure.
- Do not update shipment state until signature and replay checks pass.

## Deliverables

- Updated webhook controller, verifier, event store, and tests.
- Configuration documentation for signing secret and rotation behavior.
- Operational note for duplicate event handling and failure diagnostics.

## Completion Evidence

- Passing tests for signature, replay, stale timestamp, and idempotent processing.
- Security review note for raw body verification and secret handling.
- Log examples showing safe diagnostic context without secret leakage.