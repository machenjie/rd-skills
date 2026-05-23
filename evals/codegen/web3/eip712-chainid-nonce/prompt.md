# Benchmark Prompt

## Task

Implement a focused change to verify EIP-712 signatures with chain id, domain separator, nonce, and replay protection.

## Context

The starter repo represents a wallet login endpoint accepts typed signatures to establish a session. In its initial state, the starter behavior validates the recovered address but ignores chain id and nonce reuse. The implementation should be small enough to review but complete enough to prove the professional quality target.

## Requirements

- Signatures are bound to the expected chain id and domain separator.
- Nonces are single use and expire according to policy.
- Replay across chain, domain, account, or timestamp is rejected.
- Errors are deterministic and do not reveal sensitive session material.

## Constraints

- Typed data validation matches the declared domain and message schema.
- Nonce persistence is durable enough for concurrent login attempts.
- Tests include wrong chain, wrong domain, reused nonce, and expired nonce.
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
