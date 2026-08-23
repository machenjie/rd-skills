# Venue, Product, Monetary, and Calendar Contracts

Use this Reference only for the named venue, monetary, and calendar decision.

## Decision Rules

- Apply venue/product contracts for tick size, lot size, quantity and notional bounds, fee and funding semantics, price and quantity scale, precision, and rounding. The contract governs validation, execution, persistence, reporting, and reconciliation boundaries.
- Make currency exponent, conversion, tax, settlement calendar, cutoff, time zone, clock source and skew, provider or exchange timestamp, and business-date rules explicit at ingestion, ordering, accounting, reporting, and reconciliation boundaries.
