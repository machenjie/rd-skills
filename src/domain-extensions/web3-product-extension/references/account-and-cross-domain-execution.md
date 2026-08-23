# Account and Cross-Domain Execution

Use this Reference only for the named decision.

## Decision Rules

- For account abstraction or intent execution, define account, entry-point, bundler, paymaster, solver, and sponsor authority. The boundary covers simulation, signature, nonce, policy, fees, validity, sponsorship, delegated effects, censorship, absent actors, malicious quotes, and substituted execution.
- For bridge, L2-settlement, or cross-domain messages, define source and destination finality, sequencer and challenge-window behavior, proof and message identity, and validator or relayer trust. The contract covers replay binding, duplicate control, reorg recovery, reconciliation, and distinct destination-completion evidence.
