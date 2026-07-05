# Benchmark Prompt

## Task

Implement a focused change to verify external webhook HMAC signatures against the raw request body before parsing or side effects.

## Context

The starter repo represents an integration endpoint processes payment status callbacks from a partner service. In its initial state, the starter behavior parses JSON first and verifies a normalized body after mutation. The implementation should be small enough to review but complete enough to prove the professional quality target.

## Requirements

- Valid signatures generated from raw bytes are accepted.
- Equivalent JSON with altered whitespace fails when the signature no longer matches raw bytes.
- Missing secrets or headers fail closed before business state changes.
- Rotation supports the active and previous secret without accepting unsigned events.

## Constraints

- Signature comparison uses constant time comparison.
- Verification happens before parsing and before idempotency side effects.
- Tests use raw byte fixtures from the partner contract.
- Preserve the existing public contract unless the prompt explicitly asks for a compatible addition.
- Do not replace the benchmark with documentation-only output.

## Deliverables

- Source changes in the starter repo that implement the requested behavior.
- Tests or executable checks that prove the required behavior and denial paths.
- A short implementation note describing important tradeoffs and residual risk.

## Completion Evidence

- `bash setup.sh`
- `bash ../test-suite/run.sh`
- `bash ../security-checks/run.sh`
- Review evidence that no automatic failure condition applies.
