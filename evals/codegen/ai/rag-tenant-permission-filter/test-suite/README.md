# Test Suite

## Required Checks

- Retrieval only returns chunks the actor can read at query time.
- Tenant and object filters are applied before prompt context assembly.
- Denied chunks are excluded from citations and model input.
- Tests prove cross tenant and revoked access snippets cannot leak.

## Fixtures

- Fixture data for rag permission filtering.
- Fixture data for tenant isolation.
- Fixture data for retrieval provenance.
- At least one denied or failure fixture that proves the implementation does not take a forbidden shortcut.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Reject shortcut: Filtering unauthorized chunks only after the LLM answer is generated.
- Reject shortcut: Relying on prompt instructions to hide restricted documents.
- Existing successful behavior remains available after the new guard or compatibility path is added.
