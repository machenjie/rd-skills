# Security Checks

## Threat Surface

Test fixes can accidentally hardcode local credentials, leak database URLs, or
weaken the distinction between test and production configuration.

## Required Checks

- No secrets, personal paths, or machine-specific database URLs are committed.
- Test configuration cannot point at production by default.
- Error output included in evidence does not expose passwords or tokens.

## Rejection Cases

Reject solutions that hardcode credentials, print full secret-bearing URLs, or
use production configuration as a fallback for test failures.