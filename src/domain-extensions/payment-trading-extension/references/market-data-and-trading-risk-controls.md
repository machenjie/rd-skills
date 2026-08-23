# Market Data and Trading-Risk Controls

Use this Reference only for the named market-data and trading-risk decision.

## Decision Rules

- Gate price-sensitive execution on market-data authority, freshness, sequence continuity, venue and instrument status, halt or auction state, and snapshot recovery. Derive fat-finger, price-collar, slippage, and unavailable-evidence behavior from current risk policy.
- Derive refund, adjustment, payout, trading override, self-trade prevention, pre-trade limit, and kill-switch authority from current risk policy. The policy governs stale input, fail-safe behavior, activation, recovery, user impact, and tamper evidence.
- For leveraged products, model collateral, maintenance margin, margin call, liquidation, insurance or loss allocation, and auto-deleveraging states. Authoritative risk inputs bind triggers and position priority; outcomes cover partial execution, halt, stale price, appeal, and reconciliation.
