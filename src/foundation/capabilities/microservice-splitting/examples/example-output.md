# Example Output

```markdown
## Service Split Assessment

Decision: Defer split; strengthen module boundary first.

Proposed boundary: Invoice generation service.

Justification tested:
- Independent scaling: credible but not current.
- Independent deployment: not possible because checkout and invoicing still release together.
- Fault isolation: useful, but retry and reconciliation are not designed.
- Team ownership: same team owns both sides.

Blocking gaps:
- Shared invoice and order tables.
- No stable invoice API contract.
- No degraded checkout behavior if invoice generation is unavailable.

Mitigation:
- Isolate invoice module, define contract, introduce outbox events, then reassess extraction.
```
