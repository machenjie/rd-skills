# Web3 Product Extension Checklist

This checklist groups chain custody and transactions with operational, upgrade, governance, and delegated-authority decisions.

## Custody and Chain Transactions

- Keep private keys, seed phrases, signing secrets, and recovery material inside the declared custody boundary and outside diagnostics. Prove non-custodial user secrets do not reach application servers.
- Derive custodial storage, signing, backup, recovery, and access controls from the selected custody model.
- Record chain, network, contract, code, asset, wallet, custody, privileged authority, and their change sources. Treat aliases, forks, proxies, and environments as explicit mappings, and define mismatch behavior with recovery evidence.
- Bind signatures to human-meaningful intent, chain or domain, verifier, actor, asset, amount or effect, replay state, validity, protocol version, and signer-verifiable approval evidence.
- Model reachable transaction states across prepared, submitted, pending, confirmed, failed, reverted, dropped, replaced, finalized, and reorganized outcomes. The lifecycle covers confirmation evidence, reorg rollback or replay, and user-visible recovery.
- Define submission uniqueness, nonce ownership, retry, unknown results, replacement and cancellation races, and result reuse. The contract spans clients, relayers, wallets, and backends without assuming one idempotency mechanism.
- Derive fees, resource estimates, replacement or cancellation economics, timeout, confirmation depth, finality, slippage, deadlines, quote freshness, extractable-value exposure, gas griefing, and work ceilings. Target-chain behavior and user loss govern the result. Oracle-dependent behavior records current authority, freshness-window evidence, manipulation controls, and fail-safe behavior.
- Define reconciliation across canonical chain state, receipts, logs, wallet or custody records, backend state, caches, and indexers. The contract covers lag, missed ranges, forks, replay, deletion, and authoritative rebuild behavior.
- Derive ownership, transfer, delegation, lock, escrow, custody, and stale-index decisions from current chain state and contract semantics. Asset authority remains distinct from UI or indexer visibility.

## Monitoring and Independent Assurance

- Monitor task-selected signing, submission, revert, replacement, finality, indexer, bridge, upgrade, governance, oracle, and custody failures.
- Record safe fields, authority, alert ownership, response action, and explicit telemetry gaps in one record for each selected signal.
- Scale independent assurance with exposure.
- Record the assurance owner, reviewed artifact, evidence freshness, and proof limits in one independent-assurance record.
- Avoid asserting audit completion from independent-assurance evidence.

## Upgrades and Deployed Behavior

- Prove storage-layout compatibility plus authorized and denied initializer or reinitializer behavior for an upgrade.
- Prove migration order and upgrade recovery behavior.
- Record deployed code/configuration identity with distinct proxy-admin and implementation ownership.
- Bind arithmetic, compiler, VM, asset-scale, and rounding semantics to the recorded deployed identity.

## Verification Evidence

- Bind each claim to chain/network, contract address, runtime bytecode, proxy/implementation, configuration, block/deployment reference, and freshness.
- Trace source/build lineage through compiler settings, artifact, deployment transaction, and current bytecode, with unverified links recorded as proof limits.
- For upgrades, compare old and new storage layouts from the bound build artifacts. Exercise authorized, denied, repeated, and out-of-order initializer paths plus migration and recovery order in a chain fork or equivalent simulation.
- For transaction and invariant behavior, record the property, scenario, command or test, environment and block, actual result, and owner. Include applicable reorg, replay, nonce, replacement, unknown-outcome, arithmetic, and external-call cases.
- For oracles and bridges, exercise trust-model-selected stale, manipulation, outage, delayed-finality, challenge, replay, duplicate, relayer/validator, and destination-completion cases.
- For custody and recovery, bind generation, storage, signing, authorization, denial, rotation, backup, recovery, and audit evidence without retaining secrets.
- Record production, chain-condition, economic-manipulation, audit, and privileged-actor limits for local tests, forks, simulations, source verification, and captured chain state.

## Governance Authority

- For governance, bind delegation, snapshot, quorum, proposal, cancellation, execution, timelock, emergency or bypass paths, pause, and recovery authority to current contracts and blast radius.

## Allowances, Nonstandard Assets, and Delegated Calls

- Define the scope of each allowance, permit, approval, or delegated spend.
- Define its nonce or replay state.
- Define validity and revocation behavior.
- Define its spender-change behavior.
- Define its residual authority behavior.
- Account for callbacks, hooks, fees, rebasing, return differences, and other nonstandard asset semantics.
- Cover reentrancy across callbacks in delegated-call evidence.
- Reject reuse of state or value assumptions after external control returns.

## Account and Cross-Domain Execution

- For account abstraction or intent execution, define account, entry-point, bundler, paymaster, solver, and sponsor authority. The boundary covers simulation, signature, nonce, policy, fees, validity, sponsorship, delegated effects, censorship, absent actors, malicious quotes, and substituted execution.
- For bridge, L2-settlement, or cross-domain messages, define source and destination finality, sequencer and challenge-window behavior, proof and message identity, and validator or relayer trust. The contract covers replay binding, duplicate control, reorg recovery, reconciliation, and distinct destination-completion evidence.
