# Test Suite

## Required Checks

- Signatures are bound to the expected chain id and domain separator.
- Nonces are single use and expire according to policy.
- Replay across chain, domain, account, or timestamp is rejected.
- Errors are deterministic and do not reveal sensitive session material.

## Fixtures

- Fixture data for eip-712 domain validation.
- Fixture data for chain id binding.
- Fixture data for nonce replay protection.
- At least one denied or failure fixture that proves the implementation does not take a forbidden shortcut.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Reject shortcut: Recovering an address without validating chain id and domain.
- Reject shortcut: Storing nonces only in process memory.
- Existing successful behavior remains available after the new guard or compatibility path is added.
