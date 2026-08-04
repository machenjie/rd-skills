# Native Boundary Review

Primary Professional Skill: `backend-change-builder`  
Selected Domain Skill: `low-level-systems-extension`

## Hidden risks

- exception or panic can unwind across the FFI boundary
- allocation in one runtime can be freed by an incompatible allocator
- relaxed publication can expose partially initialized shared state

## Required evidence

- cross-language unwind containment negative test
- allocator pairing and ownership transfer test
- happens-before litmus or sanitizer evidence for publication

## Handoff

- ABI ownership and error contract
- selected unwind allocator and publication controls
- platform proof limits and residual owner

Contain failure inside each runtime, translate it to the declared ABI result, pair allocation and destruction with an explicit owner, and derive acquire/release or stronger ordering from the required publication relationship.
