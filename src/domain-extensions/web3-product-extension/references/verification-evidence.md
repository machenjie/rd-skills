# Verification Evidence Pattern

Use this evidence-pattern Reference only for the named Web3 verification-evidence decision.

## Decision Rules

- Bind each claim to its chain/network, actual asset/custody or deployed surface, configuration, transaction/block identity, and freshness.
- Include contract address/bytecode and proxy/implementation identity only when those mechanisms exist. Native-coin custody uses its actual wallet/key or script and spend-authority evidence.
- For deployed-code claims, trace source/build lineage through compiler settings, artifact, deployment transaction, and current bytecode; record unverified links as proof limits.
- For upgrades, compare old and new storage layouts from the bound build artifacts. Exercise authorized, denied, repeated, and out-of-order initializer paths plus migration and recovery order in a chain fork or equivalent simulation.
- For transaction and invariant behavior, record the property, scenario, command or test, environment and block, actual result, and owner. Include applicable reorg, replay, nonce, replacement, unknown-outcome, arithmetic, and external-call cases.
- For oracles and bridges, exercise trust-model-selected stale, manipulation, outage, delayed-finality, challenge, replay, duplicate, relayer/validator, and destination-completion cases.
- For custody and recovery, bind generation, storage, signing, authorization, denial, rotation, backup, recovery, and audit evidence without retaining secrets.
- Record production, chain-condition, economic-manipulation, audit, and privileged-actor limits for local tests, forks, simulations, source verification, and captured chain state.
