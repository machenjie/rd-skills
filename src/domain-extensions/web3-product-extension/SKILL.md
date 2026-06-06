---
name: web3-product-extension
description: Adds professional product rules for Web3 changes involving wallets, signatures, smart contracts, blockchain transactions, token assets, chain data, custody, private keys, Web3 auth, and on-chain/off-chain consistency.
license: MIT
changeforge_kind: domain-extension
changeforge_version: 0.1.0
---

## Mission
Extend ChangeForge product and code change analysis with Web3 engineering discipline for smart contract security (reentrancy, integer overflow, access control), custody architecture safety, signature integrity (EIP-712, replay protection), on-chain/off-chain state consistency, MEV attack surface awareness, oracle manipulation risk, L2 rollup security, and formal verification requirements — ensuring that Web3 changes cannot drain user assets, forge authorization, or create irreversible financial loss due to implementation defects.

## Trigger Signals
- Any Solidity smart contract addition or modification.
- ERC-20, ERC-721, ERC-1155, or custom token contract changes.
- Wallet integration changes: MetaMask, WalletConnect, Coinbase Wallet, embedded wallet SDKs.
- Web3 authentication changes: SIWE (Sign-In With Ethereum), EIP-712 typed data signing, off-chain signature verification.
- Blockchain transaction submission or status monitoring changes.
- DeFi protocol integration: DEX interaction, liquidity pool changes, lending protocol calls.
- Multi-sig wallet configuration or transaction signing flow changes.
- Oracle integration: Chainlink price feed, TWAP oracle, custom oracle sources.
- L2 rollup integration: Optimism, Arbitrum, zkSync, Polygon zkEVM changes.
- Bridge or cross-chain asset transfer changes.
- Blockchain indexer, event listener, or subgraph changes.

## Do Not Use When
- The change is a standard web authentication or payment flow with no blockchain interaction, no smart contract calls, and no wallet integration.
- The change is a blockchain-themed UI with no actual on-chain operations.

## Non-Negotiable Rules
- **Private keys and seed phrases must never touch application servers, databases, logs, or network traffic**: any server-side exposure of a private key or mnemonic is an immediate and total loss of all assets controlled by that key — use non-custodial wallets or HSM-backed MPC custody; never receive, store, or transmit private keys.
- **On-chain transactions are irreversible after finality**: a blockchain state change has no `ROLLBACK` — design every on-chain action to be safe if executed; require explicit user confirmation with a human-readable summary of the action and its financial consequences before submission.
- **Reentrancy protection is mandatory for contracts that hold or transfer ETH or tokens**: a contract that calls an external address before updating its internal state is vulnerable to reentrancy — use checks-effects-interactions pattern; use `ReentrancyGuard` (OpenZeppelin); call external contracts last.
- **EIP-712 typed data signing is required for structured off-chain authorizations**: raw `eth_sign` of arbitrary bytes is vulnerable to signature hash collision attacks and provides no human-readable intent — use EIP-712 with a complete `domain` (name, version, chainId, verifyingContract) and full type specification.
- **Chain ID validation is required for all signature verification**: a signature without chain ID binding is replayable across all EVM-compatible networks — include `chainId` in the EIP-712 domain; verify it on-chain and off-chain.
- **Smart contracts that handle significant value require a third-party security audit**: self-review of contracts is insufficient for adversarial conditions — contracts handling > $100K in value must be audited by a reputable firm (Trail of Bits, Consensys Diligence, Spearbit, Code4rena) before deployment.
- **Integer arithmetic in Solidity must be checked for overflow/underflow**: Solidity < 0.8.0 does not check integer overflow by default — use Solidity ≥ 0.8.0 (built-in overflow revert) or OpenZeppelin `SafeMath` for < 0.8.0; never use unchecked arithmetic blocks on untrusted values.
- **Oracle price feed manipulation must be considered for any DeFi operation**: a spot price from a single DEX can be manipulated in a single block by a flash loan — use Chainlink price feeds for price-sensitive operations; use TWAPs (time-weighted average prices) with a minimum observation window of 30 minutes for on-chain oracles.

## Industry Benchmarks
- **Solidity Security Best Practices (Consensys — smart-contract-best-practices.com)**: Reentrancy, tx.origin misuse, delegatecall risk, unchecked return values, integer overflow, front-running, DoS by block gas limit, improper access control. The baseline checklist for Solidity review.
- **OpenZeppelin Contracts**: Battle-tested implementations of ERC-20, ERC-721, ERC-1155, access control (`Ownable`, `AccessControl`), security primitives (`ReentrancyGuard`, `Pausable`), and upgrade patterns (transparent proxy, UUPS). Use these rather than custom implementations.
- **SWC Registry (Smart Contract Weakness Classification)**: 36 classified smart contract weaknesses with test cases, analogous to CWE for smart contracts. Map all findings to SWC IDs during review.
- **EIP-712: Typed Structured Data Hashing and Signing**: The standard for human-readable, replay-protected off-chain authorizations. Required for any off-chain signature that authorizes an on-chain action.
- **Formal Verification Tools (Certora Prover, Echidna Fuzzer, Mythril)**: Certora for specification-based formal verification; Echidna for property-based fuzzing; Mythril for symbolic execution vulnerability detection. Required for high-value contract changes.
- **MEV (Maximal Extractable Value) — Flashbots Research**: Front-running, sandwich attacks, and backrunning in public mempools. Use Flashbots Protect RPC for private transaction submission; use commit-reveal schemes for auction contracts; use slippage limits for DEX swaps.
- **L2 Security Models**: Optimistic rollup fraud proofs (7-day challenge window, Arbitrum/Optimism); ZK rollup validity proofs (immediate finality, zkSync/StarkNet). Understand the finality and challenge period implications for your bridge and cross-chain flows.
- **Chainlink Oracle Security**: DON (Decentralized Oracle Network) aggregation, minimum heartbeat verification, `latestRoundData` return value validation (check `answeredInRound`, `updatedAt` for staleness). Never use stale oracle data.

### Smart Contract Vulnerability Classification

| Vulnerability | SWC ID | Severity | Prevention |
|---|---|---|---|
| Reentrancy | SWC-107 | Critical | Checks-effects-interactions; ReentrancyGuard |
| Integer overflow/underflow | SWC-101 | Critical | Solidity ≥ 0.8.0; SafeMath |
| tx.origin authentication | SWC-115 | High | Use `msg.sender` not `tx.origin` |
| Unprotected SELFDESTRUCT | SWC-106 | Critical | `onlyOwner` on destructible functions |
| Oracle manipulation | SWC-136 | High | Chainlink DON; TWAP with 30-min window |
| Front-running (price slippage) | SWC-114 | High | Slippage tolerance; commit-reveal |
| Delegatecall to untrusted contract | SWC-112 | Critical | Whitelist delegatecall targets |
| Signature replay | SWC-121 | High | EIP-712 with chainId + nonce |
| Access control missing | SWC-105 | Critical | `onlyOwner`/`AccessControl` on admin functions |
| Unchecked return value | SWC-104 | Medium | Always check `bool success` from `call()` |

## Domain Risk Model
- **Reentrancy drains contract funds**: a malicious contract calls back into the victim contract's withdraw function before the balance is updated — each reentrant call withdraws the full balance; total loss.
- **Integer overflow bypasses token balance check**: in Solidity < 0.8.0, `uint256 balance - amount` underflows to `type(uint256).max` when `amount > balance` — effectively grants unlimited balance.
- **Signature replay on different chain drains user funds**: a permit signature valid on Ethereum mainnet is replayed on Polygon — the same signed message authorizes a spend on a chain the user did not intend.
- **Oracle price manipulation via flash loan sandwich**: an attacker takes a flash loan, manipulates the spot price of a token on a DEX, triggers a liquidation or price-sensitive operation in the victim protocol, and repays the flash loan in the same block — net gain at the victim's expense.
- **Leaked private key on server drains custody wallet**: a hot wallet private key is stored in an environment variable; the server is compromised; the attacker calls `transferAll` and drains all assets in seconds — no rollback possible.
- **Reorg invalidates assumed confirmed state**: a transaction is confirmed at block N; the off-chain system grants an entitlement; a chain reorganization removes block N; the on-chain state reverts; the off-chain entitlement remains.
- **Upgrade proxy storage collision**: a UUPS or transparent proxy upgrade deploys a new implementation with a different storage layout — existing state variables are read at wrong offsets; contract state is corrupted.
- **MEV sandwich attack on DEX transaction**: a user submits a DEX swap with high slippage tolerance; an MEV bot front-runs with a buy order, executes the user's transaction at a manipulated price, and back-runs with a sell — user receives significantly less than expected.

## Linked Foundation Capabilities
- secret-configuration-security
- authentication-authorization
- permission-boundary-modeling
- state-machine-modeling
- idempotency-retry-design
- transaction-consistency
- domain-event-modeling
- logging-error-handling
- observability
- threat-modeling

## Linked Professional Skills
- security-privacy-gate
- backend-change-builder
- integration-change-builder
- data-middleware-change-builder
- reliability-observability-gate
- quality-test-gate
- delivery-release-gate

## Critical Details
- **Checks-effects-interactions (CEI) pattern is the primary reentrancy defense**: (1) CHECK preconditions; (2) UPDATE all state (EFFECTS); (3) call external contracts (INTERACTIONS) — never call external contracts before updating state.
- **Gas limit considerations for on-chain operations**: all on-chain operations have a gas cost ceiling — unbounded loops (`for (uint i = 0; i < users.length; i++)`) will run out of gas with a large enough array; use pagination or off-chain computation.
- **Event emission is the audit trail**: Solidity events are the only persistent, queryable record of on-chain actions — emit events for all state changes; include indexed parameters for efficient filtering; never rely on transaction receipt analysis as the only audit mechanism.
- **Proxy upgrade governance must be timelocked**: an immediately executable upgrade with no timelock allows a compromised admin key to silently upgrade a contract to a malicious implementation — use OpenZeppelin TimelockController with a minimum 48-hour delay for production contracts.
- **`latestRoundData` oracle staleness check**: Chainlink returns `(roundId, answer, startedAt, updatedAt, answeredInRound)` — always validate `updatedAt > block.timestamp - MAX_STALENESS` and `answeredInRound >= roundId` before using the price; stale prices produce incorrect valuations.
- **Tenderly / Hardhat fork simulation**: test all contract interactions against a mainnet fork before deploying to mainnet — forked simulations catch gas estimation errors, slippage issues, and integration failures that testnets cannot replicate.

### Anti-Examples

| Web3 Pattern | Problem | Corrected Approach |
|---|---|---|
| `require(tx.origin == owner)` | tx.origin is exploitable by proxy contracts; phishing risk | `require(msg.sender == owner)` |
| `(bool success,) = addr.call{value: amount}("")` before balance update | Reentrancy: external call before state update | Update balance first (effects before interactions); add `ReentrancyGuard` |
| `eth_sign(bytes32 hash)` for authorization | No human-readable intent; no chain ID; replay risk | EIP-712 typed data with domain (name, version, chainId, verifyingContract) |
| Spot DEX price as oracle input | Single-block manipulation via flash loan | Chainlink price feed + staleness check, or TWAP with 30-min observation window |
| Private key in `.env` file in repository | Leaked key drains all controlled assets immediately | AWS Secrets Manager / Vault + hardware wallet for production signing |

## Failure Modes
- **Reentrancy drains ETH from liquidity pool**: a reentrancy vulnerability in a custom vault allows a recursive `withdraw` call — entire ETH balance drained in a single transaction; no recovery possible.
- **Integer underflow bypasses balance check in Solidity 0.7**: `balance - withdrawAmount` underflows — attacker receives 2^256 tokens; token economics destroyed.
- **Cross-chain signature replay loses user funds**: a gasless approval signature for Mainnet is replayed on Arbitrum — user's allowance is set on Arbitrum without consent; attacker executes a transferFrom.
- **Flash loan oracle manipulation causes bad debt**: a lending protocol uses spot price; attacker manipulates price via flash loan; executes an undercollateralized borrow; price returns to normal; protocol has bad debt.
- **Reorg removes confirmed deposit**: an exchange credits a user's deposit after 1 block confirmation; a 2-block reorg removes the deposit transaction; the credit has already been granted; funds are spent that never settled.
- **Upgrade proxy storage collision corrupts all user balances**: a contract upgrade adds a state variable at the same storage slot as an existing mapping — all user balances are overwritten with the new variable's default value (zero).

## Output Contract
Return Web3 change assessment with:
- **Smart contract security review**: SWC vulnerability mapping, reentrancy analysis, access control audit, integer arithmetic safety.
- **Signature integrity**: EIP-712 domain completeness, chain ID binding, nonce/replay protection, human-readable intent display.
- **Custody architecture**: key management model, HSM/MPC usage, signing authorization chain.
- **Transaction lifecycle model**: pending, confirmed (with block depth), finalized, failed, reverted, reorg states.
- **Oracle security**: price feed source, staleness check, manipulation resistance.
- **L2 finality implications**: fraud proof window, bridge challenge period, cross-chain state consistency.
- **Audit obligations**: contract value threshold, required audit firm, formal verification requirements.
- **Observability plan**: on-chain event indexing, balance monitoring, anomaly alerting.
- **Block/pass decision** with required conditions for approval.

## Evidence Contract
Close a Web3 change only when all five canonical answers are concrete (answer schema: `agent-execution-discipline`), because the loss path is irreversible asset drain:
- **Basis**: the SWC entry, EIP-712 domain rule, or custody policy the change rests on.
- **Files and boundaries inspected**: the contract, signing path, and chain-data boundary read, with the on-chain/off-chain trust boundary and the network/chain-ID binding confirmed.
- **Placement rationale**: why signing authority, nonce/replay protection, and slippage/MEV defenses live where they do, and that no private key or seed ever reaches a server, log, or network path.
- **Validation commands**: the contract tests, fork/reorg simulation, signature-replay test, and upgrade storage-layout check run, each with its outcome.
- **Residual risk**: the reorg-depth, oracle-staleness, upgrade, or asset freeze/recovery path that remains, with the named owner and the audit gate.

## Quality Gate
1. All contracts use Solidity ≥ 0.8.0 or SafeMath; no integer overflow/underflow risk.
2. Reentrancy protection is implemented (CEI pattern + ReentrancyGuard) for all ETH/token transfers.
3. Off-chain signatures use EIP-712 with complete domain (name, version, chainId, verifyingContract).
4. All on-chain state changes are logged with Solidity events including indexed fields.
5. Oracle integrations use Chainlink DON with staleness check; no single-block spot price manipulation risk.
6. Private keys are managed by HSM/MPC or hardware wallet; never server-side.
7. Upgrade proxies have TimelockController with ≥ 48-hour delay.
8. Contracts handling > $100K equivalent require third-party audit before deployment.
9. Transaction lifecycle model covers reorg, pending, confirmed (depth), reverted, and failed states.
10. MEV exposure is assessed; slippage limits are configured; high-value operations use private RPC (Flashbots Protect).

## Handoff
- **security-privacy-gate** — for private key custody, signature security, OWASP-equivalent Web3 vulnerabilities, and regulatory compliance.
- **quality-test-gate** — for smart contract test coverage (≥ 90%), formal verification obligations, fork simulation tests, and reorg test scenarios.
- **reliability-observability-gate** — for on-chain event indexing SLI, transaction confirmation latency, and balance anomaly alerting.
- **integration-change-builder** — for oracle integration, cross-chain bridge calls, and on-chain/off-chain state consistency.
- **delivery-release-gate** — for mainnet deployment sequencing, contract upgrade governance, and timelock execution.

## Completion Criteria
The Web3 change is approved when smart contracts use Solidity ≥ 0.8.0 with overflow protection, reentrancy guards are in place, EIP-712 signatures include complete domain with chain ID, all state changes emit events, oracle integrations include staleness validation, private keys are HSM/MPC-managed, upgrade proxies are timelocked, contracts above the value threshold have third-party audits, and the transaction lifecycle model handles reorg, pending, confirmed, and reverted states.
