# Starter Repo

## Stack

Python API service with feature flags, compatibility shims, generated client references, and deprecated endpoint routing.

## Initial State

The migration is complete, but the flag, fallback, compatibility branch, deprecated API, and docs references remain. There is no telemetry, caller search, owner, or rollback path.

## Files

- `profiles/flags.py`
- `profiles/service.py`
- `profiles/legacy_serializer.py`
- `profiles/routes.py`
- `sdk/generated/profile_client.py`
- `tests/test_profile_cleanup.py`

## Constraints

The starting point intentionally keeps stale compatibility paths. The benchmark expects deletion governance and evidence, not blind removal.
