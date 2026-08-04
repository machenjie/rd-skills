---
name: web3-product-extension
description: "For analysis/task/review agents using a Professional Skill on wallets, signing, smart contracts, chain transactions, or custody; not for work with no chain behavior."
---

# web3-product-extension

## Role

Load this focused Layer 3 Domain Skill for affected on-chain behavior. Provide
`analysis-agent`, `task-agent`, and `review-agent` with custody, signing,
transaction, finality, contract, oracle, bridge, governance, and recovery
constraints for affected on-chain behavior.

## When To Use

- blockchain, smart contract, wallet, signing, chain transaction, bridge, oracle, or custody behavior

## Do Not Use

- ordinary application work or payment-only wallets with no chain behavior
- hash or signature terminology without chain or custody behavior

## Required Inputs

- chain identity, asset exposure, custody, signer, finality, upgrade, and recovery boundaries
- deployed code and configuration, oracle or indexer trust, threat model, and evidence

## Professional Decision Rules

- **Bind key controls to custody**: non-custodial secrets never reach application servers or logs. Approved custody proves generation, isolation, recovery, rotation, and audit boundaries.
- **Confirm irreversible intent before submission**: expose chain, asset, target, authority, amount, fees, and consequence. Scale confirmation and simulation to value and reversibility.
- **Protect external-call invariants**: prove state or value cannot be reused or observed inconsistently across reentrant calls.
- **Bind off-chain authorization**: signatures commit to action, domain, network, verifier, nonce, expiry, and version when relevant.
- **Scale independent assurance to exposure**: select review and verification depth from value, novelty, privilege, attack surface, and recoverability.
- **Use deployed arithmetic semantics**: prove overflow, precision, scaling, rounding, and exceptional arithmetic against the deployed compiler and assets.
- **Protect price-dependent actions**: prove oracle authority, freshness, manipulation cost, and fail-safe behavior.
- **Derive oracle windows from evidence**: use current market behavior instead of a preset duration.
- **Reconcile indexers to canonical state**: off-chain authorization or balances account for confirmation depth, reorg, replay, and finality.

## High-Value Gotchas

- replay succeeds because authorization omits domain or nonce binding
- custody recovery bypasses normal signing controls
- a fresh oracle remains economically manipulable
- an indexer reports state removed by reorganization
- an upgrade or bridge key concentrates loss exposure

## Execution Checklist

1. Trace asset authority, signer/custody, contract calls, chain identity, finality, and recovery.
2. Select controls from exposure, target-chain semantics, liquidity, and operational evidence.
3. Prove invariant, reorg, replay, oracle, upgrade, and recovery behavior.

## Stop / Escalation Conditions

- Stop when custody authority, deployed bytecode/configuration, chain identity, asset exposure, or recovery ownership is unknown.
- Escalate possible asset loss, privileged-key compromise, irreversible deployment, bridge/oracle uncertainty, and unsupported audit claims.

## Output Contract

- State the chain invariant, authority, selected control, finality limits, and residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | chain custody signing contract finality or indexer behavior needs domain risk closure | hash or signature terminology appears without chain or custody behavior | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
