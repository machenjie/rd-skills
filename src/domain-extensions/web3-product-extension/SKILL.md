---
name: web3-product-extension
description: "Use for confirmed on-chain custody, signing, transaction, contract, bridge, oracle, or wallet behavior."
---

# web3-product-extension

## Role

This focused Layer 3 Domain Skill gives `analysis-agent`, `task-agent`, and `review-agent` the Web3 kernel and named References.

## When To Use

- confirmed on-chain behavior

## Do Not Use

- no chain or custody behavior; payment-only wallets; hash or signature terminology alone

## Required Inputs

- authority, identity, exposure, recovery, and evidence boundaries

## Professional Decision Rules

- Preserve the accepted on-chain invariant.
- Load each named Reference whose decision problem is active.

## High-Value Gotchas

- Hash or signature terms can falsely trigger Web3 without chain or custody evidence.

## Execution Checklist

1. Trace asset authority, signer/custody, contract calls, chain identity, finality, and recovery.
2. Select controls from exposure, target-chain semantics, liquidity, and operational evidence.
3. Prove invariant, reorg, replay, oracle, upgrade, and recovery behavior.

## Stop / Escalation Conditions

- Stop on unknown authority or material loss, privileged-key, irreversible, bridge/oracle, or audit uncertainty.

## Output Contract

- Invariant, authority, control, limits, and residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [custody and chain transactions](references/custody-and-chain-transactions.md) | targeted | custody, signing, chain transaction, finality, oracle, indexer, or asset-authority behavior needs a decision | hash or signature terminology appears without chain or custody behavior | analysis-agent, task-agent, review-agent | boundary-decision, selected-approach, failure-decision, residual-risk |
| [monitoring and independent assurance](references/monitoring-and-independent-assurance.md) | targeted | selected Web3 failure monitoring, response, or independent-assurance scope is open | no Web3 monitoring, response, or assurance claim exists | analysis-agent, task-agent, review-agent | decision-record, validation-plan, proof-limit, residual-risk |
| [upgrades and deployed behavior](references/upgrades-and-deployed-behavior.md) | targeted | contract upgrade, storage migration, deployed identity, or arithmetic behavior is open | deployed code, configuration, upgrade, storage, and arithmetic behavior are unchanged | analysis-agent, task-agent, review-agent | release-decision, residual-risk |
| [verification evidence](references/verification-evidence.md) | evidence-pattern | a Web3 claim needs source, build, deployment, fork-simulation, chain-state, or proof-limit closure | no Web3 claim or evidence decision exists | analysis-agent, task-agent, review-agent | evidence-record, validation-plan, proof-limit, residual-risk |
| [governance authority](references/governance-authority.md) | targeted | on-chain governance, privileged upgrade, or bridge authority is open | governance, privileged upgrade, and bridge authority are unchanged | analysis-agent, task-agent, review-agent | boundary-decision, residual-risk |
| [allowances nonstandard assets and delegated calls](references/allowances-nonstandard-assets-and-delegated-calls.md) | targeted | allowance, permit, approval, delegated spend, nonstandard asset, callback, or reentrancy behavior is open | none of those allowance, delegated-call, nonstandard-asset, callback, or reentrancy behaviors changes | analysis-agent, task-agent, review-agent | boundary-decision, failure-decision, residual-risk |
| [account and cross domain execution](references/account-and-cross-domain-execution.md) | targeted | account abstraction, intent, bridge, L2 settlement, or cross-domain authority is open | none of account abstraction, intent, bridge, L2 settlement, or cross-domain authority changes | analysis-agent, task-agent, review-agent | boundary-decision, failure-decision, residual-risk |
