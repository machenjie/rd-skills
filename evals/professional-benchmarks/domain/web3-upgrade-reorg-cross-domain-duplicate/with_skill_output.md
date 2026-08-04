# Web3 Integration Review

Primary Professional Skill: `integration-change-builder`  
Selected Domain Skill: `web3-product-extension`

## Hidden risks

- proxy upgrade can corrupt storage layout or rerun initialization
- a reorg can invalidate the source event after the destination effect
- duplicate cross-domain delivery can execute the same effect twice

## Required evidence

- storage-layout diff initializer and rollback proof
- fork and reorg fixture through confirmation and reconciliation
- duplicate message identity and destination replay negative test

## Handoff

- chain and cross-domain invariant
- upgrade ordering finality and duplicate-execution controls
- deployment identity proof limits and residual owner

Block the change until deployed-code identity and storage compatibility are proven, initializer authority is one-time and ordered, source and destination finality are modeled independently, and the destination records message identity before applying the effect.
