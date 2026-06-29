# Security Checks

## Threat Surface

Data shaping can accidentally include filtered records or leak missing-field defaults.

## Required Checks

- Reject fixes that include records that should be filtered.
- Fail if raw records are logged while debugging.

## Rejection Cases

- Reject hidden nested comprehension defaults.
- Reject returned-shape changes without approval.

