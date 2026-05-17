# Example Output

```markdown
## Extensibility Plan

Extension point: Tax calculation provider.

Known variation:
- US and EU tax providers differ by jurisdiction and evidence requirements.

Invariant rules:
- Checkout must receive a deterministic tax quote.
- Authorization, audit, and order total validation stay in the core domain.

Contract:
- calculate_tax(cart, jurisdiction, evidence) -> tax_quote
- Errors must classify retryable provider outage versus non-retryable invalid evidence.

Rejected abstraction:
- Generic checkout rule plugin.
Reason: Too broad and would allow extensions to bypass pricing invariants.

Quality gate: Two providers can implement the contract without internal model access.
```
