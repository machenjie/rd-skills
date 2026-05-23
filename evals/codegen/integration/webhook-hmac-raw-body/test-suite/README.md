# Test Suite

## Required Checks

- Valid signatures generated from raw bytes are accepted.
- Equivalent JSON with altered whitespace fails when the signature no longer matches raw bytes.
- Missing secrets or headers fail closed before business state changes.
- Rotation supports the active and previous secret without accepting unsigned events.

## Fixtures

- Fixture data for raw body signature verification.
- Fixture data for partner webhook contract.
- Fixture data for secret rotation.
- At least one denied or failure fixture that proves the implementation does not take a forbidden shortcut.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Reject shortcut: Verifying HMAC over JSON reserialization instead of raw body bytes.
- Reject shortcut: Accepting unsigned callbacks when configuration is missing.
- Existing successful behavior remains available after the new guard or compatibility path is added.
