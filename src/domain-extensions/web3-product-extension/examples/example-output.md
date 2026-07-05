# Example Output

## Web3 Domain Findings
- Blocking: signature request must use typed, human-readable fields with chain id, contract address, action, nonce, expiry, and replay protection.
- Required state model: requested, wallet-opened, signed, submitted, pending, confirmed, failed, reverted, replaced, reorged.
- Consistency requirement: backend ownership must reconcile contract events with indexer lag and never treat cached ownership as final during pending transfer.

## Verification
- Unit tests for nonce reuse, wrong chain, expired signature, duplicate submit, and revert handling.
- Integration test against a test network or deterministic contract simulator.
- Monitoring for transaction id, wallet address hash, chain id, finality delay, and revert reason without key material.
