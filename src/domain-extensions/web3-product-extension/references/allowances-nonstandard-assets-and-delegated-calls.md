# Allowances, Nonstandard Assets, and Delegated Calls

Use this Reference only for the named decision.

## Decision Rules

- **Protect external-call invariants**: prove state or value cannot be reused or observed inconsistently across reentrant calls.
- Define the scope of each allowance, permit, approval, or delegated spend.
- Define its nonce or replay state.
- Define validity and revocation behavior.
- Define its spender-change behavior.
- Define its residual authority behavior.
- Account for callbacks, hooks, fees, rebasing, return differences, and other nonstandard asset semantics.
- Cover reentrancy across callbacks in delegated-call evidence.
- Reject reuse of state or value assumptions after external control returns.
