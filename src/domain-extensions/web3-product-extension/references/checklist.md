# Web3 Product Extension Checklist

- Private keys, seed phrases, signing secrets, and recovery material are never logged, stored insecurely, exposed to clients, or copied into diagnostics.
- Wallet, chain id, network, contract address, token standard, asset identifier, and custody boundary are explicit.
- Signature payloads are human-readable, scoped to one intent, time or nonce bounded, replay protected, and validated server-side.
- Transaction state includes pending, confirmed, failed, reverted, dropped/replaced, and reorg-aware recovery behavior.
- Transaction submission is idempotent across retries, refreshes, and duplicate client requests.
- Nonce, gas, replacement, timeout, and finality assumptions are defined.
- On-chain source of truth, off-chain cache/indexer, and backend state have a reconciliation plan.
- Asset ownership checks account for transfer, approval, delegation, lock, escrow, and stale index data.
- Network mismatch blocks unsafe actions and tells the user what chain is expected.
- Monitoring covers failed submissions, revert reasons, indexer lag, reorg handling, suspicious signature failures, and custody access.
