# Example Output

```markdown
## SDK Contract Plan

Package: @example/payments-client
Change class: minor

Contract surface:
- New `refunds.create` operation generated from OpenAPI commit abc123.
- New `RefundError` union member `refund_amount_exceeds_captured`.

Compatibility:
- Node 20+ and TypeScript strict mode supported.
- Server API v1 remains compatible; no removed fields.

Generation:
- OpenAPI Generator 7.8.0 pinned.
- Generated diff reviewed for exported type changes.

Consumer tests:
- Fixture project compiles with previous and current package.
- Contract test covers create refund success and error response.

Migration:
- No removal in this release.
- Existing `payments.refund` helper is deprecated until 2.0 with replacement guidance.
```
