# Security Checks

## Threat Surface

UI branch mistakes can misrepresent disabled or permission-adjacent states.

## Required Checks

- Reject truthiness that hides disabled or falsey states.
- Fail if raw API/user content is rendered unsafely while changing labels.

## Rejection Cases

- Reject nested ternary truthiness behavior.
- Reject shared helper changes that affect unrelated UI states.

