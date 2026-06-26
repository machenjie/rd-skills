# Example Output

```markdown
## Extensibility Plan

mode_selected: create extension point
extension_decision: approved with conditions

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

Graph / Memory / Execution Validation:
- Graph evidence: checkout tax call site, tax provider interface, generated contract docs, and provider tests inspected.
- Memory evidence: old "future pricing hooks" note rejected because it has no current implementer or dated roadmap commitment.
- Execution evidence: compatibility test for both providers, invariant-bypass test, malformed evidence test, and provider outage isolation test required before handoff.

Extension To Validation Map:
- Tax provider contract -> two provider implementations -> compatibility test -> platform owner.
- Checkout invariants -> read-only cart/tax quote boundary -> invariant-bypass test -> checkout owner.
- Provider failure isolation -> retryable/non-retryable error split -> integration test -> reliability gate.

Evidence Limits:
- No third-party marketplace implementers inspected.
- No production latency profile authorized by this plan.
- Sandbox evidence remains required before external provider execution.
```
