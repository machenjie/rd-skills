# Security Checks

## Threat Surface

Cancellation touches authorization and refund-adjacent state. The primary risk
for this benchmark is not a new external security surface; it is that excessive
file split hides authorization and refund decisions across tiny files.

## Required Checks

- Authorization remains visible before cancellation mutation.
- Refund-hold decisions do not trust caller-supplied disputed or premium flags.
- Logs and errors do not expose sensitive customer or payment details.
- Review rejects splits that hide security-relevant decisions behind pass-through
  helpers.

## Rejection Cases

- Fail any solution where denied authorization is checked after helper files
  mutate state or decide refund behavior.
- Reject any solution that lets request data override premium or disputed status.
- Reject any solution that hides authorization or refund-hold decisions across
  micro-file sprawl without a real boundary.
