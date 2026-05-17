# Example Output

```markdown
## Unit Test Plan

Behavior: Discount policy for annual subscription renewal.

Cases:
- Applies 10 percent discount for active annual accounts.
- Applies no discount for monthly accounts.
- Rejects negative renewal amount.
- Rounds half-up at the currency boundary.
- Raises policy error when account is suspended.

Controls:
- Fixed clock at renewal date.
- Table-driven inputs for boundary amounts.
```
