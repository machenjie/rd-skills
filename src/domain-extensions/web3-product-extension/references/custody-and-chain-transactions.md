# Custody and Chain Transactions

Use this Reference only for the named decision.

## Decision Rules

- **Bind key controls to custody**: when the selected custody model is non-custodial, require evidence that custody secrets never reach application servers or logs. Approved custody proves generation, isolation, recovery, rotation, and audit boundaries.
- **Confirm irreversible intent before submission**: expose chain, asset, target, authority, amount, fees, and consequence. Scale confirmation and simulation to value and reversibility.
- **Bind off-chain authorization**: signatures commit to action, domain, network, verifier, nonce, expiry, and version when relevant.
- **Protect price-dependent actions**: prove oracle authority, freshness, manipulation cost, and fail-safe behavior.
- **Derive oracle windows from evidence**: use current market behavior instead of a preset duration.
- **Reconcile indexers to canonical state**: off-chain authorization or balances account for confirmation depth, reorg, replay, and finality.
- replay succeeds because authorization omits domain or nonce binding
- custody recovery bypasses normal signing controls
- a fresh oracle remains economically manipulable
- an indexer reports state removed by reorganization
- Keep private keys, seed phrases, signing secrets, and recovery material inside the declared custody boundary and outside diagnostics. Prove non-custodial user secrets do not reach application servers.
- Derive custodial storage, signing, backup, recovery, and access controls from the selected custody model.
- Record chain, network, contract, code, asset, wallet, custody, privileged authority, and their change sources. Treat aliases, forks, proxies, and environments as explicit mappings, and define mismatch behavior with recovery evidence.
- Bind signatures to human-meaningful intent, chain or domain, verifier, actor, asset, amount or effect, replay state, validity, protocol version, and signer-verifiable approval evidence.
- Model reachable transaction states across prepared, submitted, pending, confirmed, failed, reverted, dropped, replaced, finalized, and reorganized outcomes. The lifecycle covers confirmation evidence, reorg rollback or replay, and user-visible recovery.

### Submission, Fees, Reconciliation, and Asset-State Decisions

- Define submission uniqueness, nonce ownership, retry, unknown results, replacement and cancellation races, and result reuse. The contract spans clients, relayers, wallets, and backends without assuming one idempotency mechanism.
- Derive fees, resource estimates, replacement or cancellation economics, timeout, confirmation depth, finality, slippage, deadlines, quote freshness, extractable-value exposure, gas griefing, and work ceilings. Target-chain behavior and user loss govern the result. Oracle-dependent behavior records current authority, freshness-window evidence, manipulation controls, and fail-safe behavior.
- Define reconciliation across canonical chain state, receipts, logs, wallet or custody records, backend state, caches, and indexers. The contract covers lag, missed ranges, forks, replay, deletion, and authoritative rebuild behavior.
- Derive ownership, transfer, delegation, lock, escrow, custody, and stale-index decisions from current chain state and contract semantics. Asset authority remains distinct from UI or indexer visibility.
