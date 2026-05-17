# Example Output

```markdown
## Refactor Plan

Target:
- Extract invoice total calculation from controller into domain service.

Preserved behavior:
- Existing rounding, tax inclusion, discount ordering, and error responses.

Characterization tests:
- Current invoice totals for taxable, tax-exempt, discounted, and invalid invoices.

Steps:
- Add characterization tests.
- Extract pure calculation function without changing controller response.
- Replace controller inline logic with function call.
- Run unit and route regression tests.

Out of scope:
- Changing rounding policy or response schema.
```
