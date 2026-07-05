# Starter Repo

## Stack

Python notification service with email, SMS, push, tenant settings, environment variables, and feature flags.

## Initial State

The service reads raw env vars in business logic, branches on `mode` and `kind`, keeps stale flags, and lets a tenant flag skip a required consent check.

## Files

- `notifications/config.py`
- `notifications/service.py`
- `notifications/strategies.py`
- `tests/test_config_policy.py`

## Constraints

The starting point intentionally has stringly typed runtime policy and stale flags. The benchmark expects typed config, flag lifecycle, and invariant-preserving switches.
