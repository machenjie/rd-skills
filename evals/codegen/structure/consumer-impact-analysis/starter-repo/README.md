# Starter Repo

## Stack

Python API service with OpenAPI schema, generated TypeScript client, event payload schema, and public package exports.

## Initial State

The code directly renames `userName` to `displayName` across contracts and generated clients. Consumer list, telemetry, migration, deprecation, and rollback are missing.

## Files

- `openapi.yaml`
- `sdk/generated/user.ts`
- `users/api.py`
- `events/user_profile_v1.json`
- `tests/test_contract_compatibility.py`

## Constraints

The starting point intentionally performs a direct breaking rename. The benchmark expects consumer impact analysis and compatible rollout.
