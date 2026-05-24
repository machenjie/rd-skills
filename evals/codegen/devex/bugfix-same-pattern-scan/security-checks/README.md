# Security Checks

## Threat Surface

Profile bug fixes can accidentally weaken object authorization, reveal whether
a profile exists, or hide data-integrity problems that should remain visible to
operators.

## Required Checks

- Authorization remains server-side before profile data is read.
- Missing-profile responses do not reveal hidden user or tenant details.
- Broad error handling does not swallow unexpected repository or permission errors.

## Rejection Cases

Reject solutions that move authorization after profile formatting, expose
private profile existence in error text, or hide all profile failures as empty
display names.