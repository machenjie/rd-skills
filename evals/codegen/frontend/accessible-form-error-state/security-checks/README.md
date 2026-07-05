# Security Checks

## Threat Surface

The form handles account identifiers and server validation messages. Security
risk is moderate, but unsafe rendering or client only validation can create
privacy and account workflow defects.

## Required Checks

- Treat backend validation as authoritative for uniqueness and account policy.
- Render server messages as text and never as raw HTML.
- Avoid leaking whether an email belongs to another account beyond approved backend wording.
- Prevent duplicate submit clicks while the request is in flight.
- Keep error telemetry free of entered email values unless explicitly redacted.

## Rejection Cases

- Any solution uses unsafe HTML rendering for server errors.
- Any solution removes backend validation handling because client validation exists.
- Any solution logs entered email addresses in client side diagnostics by default.