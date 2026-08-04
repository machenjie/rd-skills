# Trading State Review

Primary Professional Skill: `backend-change-builder`  
Selected Domain Skill: `payment-trading-extension`

## Hidden risks

- a fill can arrive after cancel acknowledgement and reopen terminated quantity
- a session sequence reset can hide missing or duplicate execution reports
- a stale risk dependency can leave the kill switch unavailable or fail open

## Required evidence

- partial-fill cancel-race state-machine test
- sequence-restart gap snapshot and drop-copy reconciliation test
- kill-switch activation and recovery exercise with stale risk input

## Handoff

- execution state and quantity invariants
- sequence recovery and reconciliation contract
- kill-switch authority verdict proof limits and residual owner

Preserve cumulative executed quantity across cancel races, recover session state from a venue-authoritative view plus independent execution evidence, and make kill-switch activation and recovery authority explicit under stale or unavailable risk inputs.
