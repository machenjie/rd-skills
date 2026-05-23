# Test Suite

## Required Checks

- Allowed HTTPS hosts can be fetched with bounded timeout and response size.
- Loopback, link local, private ranges, and metadata service addresses are rejected.
- Redirect chains are revalidated before any outbound request continues.
- Denied requests return client safe errors without leaking internal network details.

## Fixtures

- Fixture data for ssrf prevention.
- Fixture data for url canonicalization.
- Fixture data for network allowlist.
- At least one denied or failure fixture that proves the implementation does not take a forbidden shortcut.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Reject shortcut: String prefix allowlists that accept attacker controlled hostnames.
- Reject shortcut: Checking only the original URL before following redirects.
- Existing successful behavior remains available after the new guard or compatibility path is added.
